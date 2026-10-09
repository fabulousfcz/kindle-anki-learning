#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kindle 生词 → Anki 词根词源补全脚本
====================================
功能：从电脑端 Anki（经 AnkiConnect）读取「英语词汇-词根词源」笔记类型里
      尚未补全词根词源的生词，用 DeepSeek 批量生成：
        - 音标（英式）
        - 释义（简洁中文）
        - 例句（带中文翻译）
        - 词根词缀（拆分 + 含义）
        - 词源（简要）
      然后回写到 Anki 对应字段。

用法：
    python enrich_vocab.py [--limit N] [--dry-run]

依赖：仅 Python 标准库（urllib/json），无需 pip 安装任何包。
前提：电脑端 Anki 已启动，且 AnkiConnect 插件已加载（默认端口 8765）。
"""

import json
import os
import sys
import urllib.request
import urllib.error

# ============ 配置区（按需修改） ============
ANKICONNECT_URL = "http://127.0.0.1:8765"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

# DeepSeek API Key 从环境变量 DEEPSEEK_API_KEY 读取，
# 或从本目录下的 api_key.txt 文件读取（文件内容只放 key 本身）。
# 不要在这里直接写 key，避免泄露到公开仓库。
def _load_api_key():
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.txt")
    if os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            key = f.read().strip()
            if key:
                return key
    return None

DEEPSEEK_API_KEY = _load_api_key()
DEEPSEEK_MODEL = "deepseek-chat"

NOTE_TYPE = "英语词汇-词根词源"   # 笔记类型名（必须与 Anki 一致）
WORD_FIELD = "单词"              # 已由 KOReader 填好的字段
TARGET_FIELDS = ["音标", "释义", "例句", "词根词缀", "词源"]  # 需要补全的字段


def ankiconnect(action, **params):
    """调用 AnkiConnect 接口。"""
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(
        ANKICONNECT_URL, data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise SystemExit(f"无法连接 AnkiConnect：{e}\n请确认 Anki 已启动、AnkiConnect 已加载。")
    if data.get("error"):
        raise SystemExit(f"AnkiConnect 报错：{data['error']}")
    return data.get("result")


def deepseek_chat(messages):
    """调用 DeepSeek，返回回复文本。"""
    payload = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1200,
        "stream": False,
    })
    req = urllib.request.Request(
        DEEPSEEK_URL, data=payload.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"DeepSeek 请求失败 HTTP {e.code}：{body[:300]}")
    return data["choices"][0]["message"]["content"].strip()


def build_prompt(word):
    """构造给 DeepSeek 的提示词，要求输出严格 JSON。"""
    return (
        f'请为英语单词 "{word}" 生成学习卡片内容，严格输出 JSON（不要多余文字、不要代码块标记），'
        f'格式如下：\n'
        f'{{"音标":"英式音标 IPA","释义":"简洁中文释义","例句":"一句含该词的英文例句",'
        f'"例句翻译":"例句的中文翻译","词根词缀":"词根词缀拆分及含义说明","词源":"简要词源"}}\n'
        f'要求：释义准确简洁；例句自然地道；词根词缀尽量拆分到常见词根/前缀/后缀并说明含义；'
        f'词源用一两句话讲清来源。'
    )


def enrich_word(word):
    """为单个单词生成补全内容，返回字段字典。"""
    raw = deepseek_chat([
        {"role": "system", "content": "你是专业的英语词汇学助手，输出严格 JSON。"},
        {"role": "user", "content": build_prompt(word)},
    ])
    # 容错：去掉可能的 ```json ... ``` 包裹
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    data = json.loads(raw)
    # 合并例句 + 例句翻译到一个「例句」字段
    example = data.get("例句", "")
    trans = data.get("例句翻译", "")
    if trans:
        example = f"{example}\n{trans}"
    return {
        "音标": data.get("音标", ""),
        "释义": data.get("释义", ""),
        "例句": example,
        "词根词缀": data.get("词根词缀", ""),
        "词源": data.get("词源", ""),
    }


def main():
    if not DEEPSEEK_API_KEY:
        raise SystemExit(
            "未找到 DeepSeek API Key！\n"
            "请在本脚本同目录下新建 api_key.txt 文件，内容只写你的 DeepSeek Key；\n"
            "或设置环境变量 DEEPSEEK_API_KEY。\n"
            "（不要把 Key 直接写在代码里，避免泄露）"
        )
    limit = None
    dry_run = False
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        elif args[i] == "--dry-run":
            dry_run = True; i += 1
        else:
            i += 1

    # 1. 找到目标笔记类型下的所有笔记
    note_ids = ankiconnect("findNotes", query=f'"note:{NOTE_TYPE}"')
    if not note_ids:
        print(f"未找到笔记类型「{NOTE_TYPE}」下的笔记。")
        return
    print(f"共找到 {len(note_ids)} 条笔记。")

    # 2. 读取笔记，筛选出「单词」已填但词根词缀为空的
    infos = ankiconnect("notesInfo", notes=note_ids)
    to_enrich = []
    for info in infos:
        fields = info.get("fields", {})
        word = (fields.get(WORD_FIELD, {}).get("value", "") or "").strip()
        root = (fields.get("词根词缀", {}).get("value", "") or "").strip()
        if word and not root:  # 有单词、但词根词缀未补
            to_enrich.append((info["noteId"], word))
    print(f"需要补全的生词：{len(to_enrich)} 个。")
    if limit:
        to_enrich = to_enrich[:limit]
        print(f"本次仅处理前 {limit} 个。")

    if dry_run:
        print("\n[dry-run] 将要处理的单词：")
        for _, w in to_enrich:
            print("  -", w)
        return

    # 3. 逐个补全并回写
    ok, fail = 0, 0
    for idx, (note_id, word) in enumerate(to_enrich, 1):
        print(f"\n[{idx}/{len(to_enrich)}] 处理 {word} ...")
        try:
            fields = enrich_word(word)
            if dry_run:
                print("  ", json.dumps(fields, ensure_ascii=False))
            else:
                ankiconnect("updateNoteFields", note={
                    "id": note_id,
                    "fields": fields,
                })
            ok += 1
        except Exception as e:
            fail += 1
            print(f"  失败：{e}")

    print(f"\n完成：成功 {ok} 个，失败 {fail} 个。")


if __name__ == "__main__":
    main()
