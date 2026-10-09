#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动补全监听器（后台常驻）
============================
功能：后台盯着电脑端 Anki，一旦发现「英语词汇-词根词源」笔记类型里出现
      新的生词（单词已填、但词根词缀为空），就自动调用 DeepSeek 补全
      「音标/释义/例句/词根词缀/词源」并写回 Anki。

用法：
    python auto_enrich.py            # 前台运行，Ctrl+C 停止
    pythonw auto_enrich.py          # Windows 下无窗口后台运行

前提：
    - 电脑端 Anki 已启动，AnkiConnect 已加载（默认端口 8765）。
    - 能访问 DeepSeek API。

依赖：仅 Python 标准库，零第三方依赖。
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
import urllib.parse

# ============ 配置区 ============
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

# 有道词典免费 TTS（无需 key，音频为 mp3）
TTS_URL = "https://dict.youdao.com/dictvoice?audio={word}&type=2"

NOTE_TYPE = "英语词汇-词根词源"
WORD_FIELD = "单词"
TARGET_FIELDS = ["音标", "释义", "例句", "词根词缀", "词源"]

POLL_INTERVAL = 5          # 检查间隔（秒）
RECENT_WINDOW_DAYS = 7     # 只补最近 N 天内的新词，避免反复处理老笔记

ENABLE_TTS = True          # 是否自动生成发音音频


def ankiconnect(action, **params):
    """调用 AnkiConnect 接口。连接失败返回 None（而非抛错），便于轮询。"""
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(
        ANKICONNECT_URL, data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None  # Anki 未运行 / 未就绪
    if data.get("error"):
        return None
    return data.get("result")


def deepseek_chat(messages):
    """调用 DeepSeek，返回回复文本。失败抛异常。"""
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
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def build_prompt(word):
    return (
        f'请为英语单词 "{word}" 生成学习卡片内容，严格输出 JSON（不要多余文字、不要代码块标记），'
        f'格式如下：\n'
        f'{{"音标":"英式音标 IPA","释义":"简洁中文释义","例句":"一句含该词的英文例句",'
        f'"例句翻译":"例句的中文翻译","词根词缀":"词根词缀拆分及含义说明","词源":"简要词源"}}\n'
        f'要求：释义准确简洁；例句自然地道；词根词缀尽量拆分到常见词根/前缀/后缀并说明含义；'
        f'词源用一两句话讲清来源。'
    )


def enrich_word(word):
    raw = deepseek_chat([
        {"role": "system", "content": "你是专业的英语词汇学助手，输出严格 JSON。"},
        {"role": "user", "content": build_prompt(word)},
    ])
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    data = json.loads(raw)
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


def fetch_tts(word):
    """从有道词典下载单词发音，返回 mp3 字节。失败返回 None。"""
    url = TTS_URL.format(word=urllib.parse.quote(word))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            ct = resp.headers.get("Content-Type", "")
        if not data or "audio" not in ct:
            return None
        return data
    except Exception:
        return None


def add_audio_to_note(note_id, word):
    """下载发音、上传到 Anki 媒体库，并把 [sound:xxx.mp3] 拼进「音标」字段末尾。
    返回 True/False 表示是否成功。"""
    if not ENABLE_TTS:
        return False
    audio = fetch_tts(word)
    if not audio:
        return False

    # 安全文件名：只保留字母数字和连字符
    safe = re.sub(r"[^A-Za-z0-9\-]", "_", word)
    filename = f"youdao_{safe}.mp3"

    # 上传到 Anki 媒体库（storeMediaFile 自动去重）
    result = ankiconnect("storeMediaFile", filename=filename, data=_b64(audio))
    if result is None:
        return False

    # 读取当前音标字段值，追加 [sound:...]
    info = ankiconnect("notesInfo", notes=[note_id])
    if not info:
        return False
    phonetic = info[0]["fields"].get("音标", {}).get("value", "") or ""
    sound_tag = f"[sound:{filename}]"
    if sound_tag in phonetic:
        return True  # 已存在，跳过
    new_phonetic = (phonetic + "\n" + sound_tag).strip()
    ankiconnect("updateNoteFields", note={"id": note_id, "fields": {"音标": new_phonetic}})
    return True


def _b64(data):
    import base64
    return base64.b64encode(data).decode("ascii")


def find_pending():
    """找出「单词已填、词根词缀为空、最近添加」的笔记，返回 [(noteId, word), ...]"""
    note_ids = ankiconnect("findNotes", query=f'"note:{NOTE_TYPE}" added:{RECENT_WINDOW_DAYS}')
    if note_ids is None:
        return None  # Anki 不可用
    if not note_ids:
        return []
    infos = ankiconnect("notesInfo", notes=note_ids)
    if infos is None:
        return None
    pending = []
    for info in infos:
        fields = info.get("fields", {})
        word = (fields.get(WORD_FIELD, {}).get("value", "") or "").strip()
        root = (fields.get("词根词缀", {}).get("value", "") or "").strip()
        if word and not root:
            pending.append((info["noteId"], word))
    return pending


def _backfill_audio():
    """给「词根词缀已填、但音标字段还没有 [sound:]」的笔记补发音。"""
    note_ids = ankiconnect("findNotes", query=f'"note:{NOTE_TYPE}" added:{RECENT_WINDOW_DAYS}')
    if not note_ids:
        return
    infos = ankiconnect("notesInfo", notes=note_ids)
    if not infos:
        return
    for info in infos:
        word = (info["fields"].get(WORD_FIELD, {}).get("value", "") or "").strip()
        phonetic = (info["fields"].get("音标", {}).get("value", "") or "").strip()
        root = (info["fields"].get("词根词缀", {}).get("value", "") or "").strip()
        # 只补：词根已填（说明已完成 DeepSeek 补全）+ 有单词 + 音标里还没有发音
        if word and root and phonetic and "[sound:" not in phonetic:
            try:
                ok = add_audio_to_note(info["noteId"], word)
                if ok:
                    ts = time.strftime("%H:%M:%S")
                    print(f"[{ts}]   ♪ {word} 发音补全")
            except Exception:
                pass


def main():
    if not DEEPSEEK_API_KEY:
        print("未找到 DeepSeek API Key！")
        print("请在本脚本同目录下新建 api_key.txt 文件，内容只写你的 DeepSeek Key；")
        print("或设置环境变量 DEEPSEEK_API_KEY。（不要把 Key 直接写在代码里，避免泄露）")
        return
    print("=" * 50)
    print("自动补全监听器已启动")
    print(f"  笔记类型：{NOTE_TYPE}")
    print(f"  检查间隔：{POLL_INTERVAL} 秒")
    print(f"  监控范围：最近 {RECENT_WINDOW_DAYS} 天内新增")
    print("  按 Ctrl+C 停止")
    print("=" * 50)
    while True:
        try:
            pending = find_pending()
            if pending is None:
                # Anki 未运行或未就绪，静默等待
                time.sleep(POLL_INTERVAL)
                continue
            for note_id, word in pending:
                ts = time.strftime("%H:%M:%S")
                print(f"[{ts}] 发现新词：{word}，开始补全...")
                try:
                    fields = enrich_word(word)
                    ankiconnect("updateNoteFields", note={
                        "id": note_id,
                        "fields": fields,
                    })
                    print(f"[{ts}]   ✓ {word} 补全完成")
                except Exception as e:
                    print(f"[{ts}]   ✗ {word} 补全失败：{e}")

                # 补发音（词根词源补全之后顺带生成）
                if ENABLE_TTS:
                    try:
                        ok = add_audio_to_note(note_id, word)
                        if ok:
                            print(f"[{ts}]   ♪ {word} 发音已生成")
                        else:
                            print(f"[{ts}]   - {word} 发音生成失败（跳过）")
                    except Exception as e:
                        print(f"[{ts}]   - {word} 发音异常：{e}")

            # 补发音：处理「词根词源已补、但音标字段还没有 [sound:] 的」老词
            if ENABLE_TTS:
                _backfill_audio()
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("\n已停止。")
            break
        except Exception as e:
            print(f"意外错误：{e}，5 秒后重试")
            time.sleep(5)


if __name__ == "__main__":
    main()
