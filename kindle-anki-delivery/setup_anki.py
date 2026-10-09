#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键在 Anki 中创建「英语词汇-词根词源」笔记类型 + 牌组
=========================================================
用法：
    python setup_anki.py

依赖：仅标准库。
前提：Anki 已启动、AnkiConnect 已加载（默认端口 8765）。
"""

import json
import urllib.request
import urllib.error

ANKICONNECT_URL = "http://127.0.0.1:8765"
MODEL_NAME = "英语词汇-词根词源"
DECK_NAME = "英语生词本"


def ankiconnect(action, **params):
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


def main():
    # 1. 建牌组
    ankiconnect("createDeck", deck=DECK_NAME)
    print(f"✅ 牌组已就绪：{DECK_NAME}")

    # 2. 建笔记类型
    model = {
        "modelName": MODEL_NAME,
        "inOrderFields": ["单词", "音标", "释义", "例句", "词根词缀", "词源"],
        "css": (
            ".card { font-family: 'Noto Sans CJK SC', 'Microsoft YaHei', sans-serif; "
            "font-size: 20px; text-align: center; color: #222; background-color: #fafafa; }\n"
            ".word { font-size: 40px; font-weight: bold; margin: 20px 0 4px; }\n"
            ".phonetic { font-size: 20px; color: #888; margin-bottom: 16px; }\n"
            ".hr { border-top: 1px solid #ddd; margin: 16px 0; }\n"
            ".sec { text-align: left; margin: 12px 0; line-height: 1.7; }\n"
            ".sec .label { font-weight: bold; color: #0a6b5c; margin-right: 6px; }\n"
            ".def { font-size: 22px; text-align: left; line-height: 1.6; margin: 8px 0; }\n"
            ".example { color: #444; font-style: italic; }"
        ),
        "isCloze": False,
        "cardTemplates": [
            {
                "Name": "单词卡",
                "Front": '<div class="word">{{单词}}</div>\n'
                         '{{#音标}}<div class="phonetic">{{音标}}</div>{{/音标}}',
                "Back": "{{FrontSide}}\n<hr id=answer>\n"
                        '<div class="def">{{释义}}</div>\n'
                        '{{#词根词缀}}<div class="sec"><span class="label">词根词缀</span>'
                        "{{词根词缀}}</div>{{/词根词缀}}\n"
                        '{{#例句}}<div class="sec example">{{例句}}</div>{{/例句}}\n'
                        '{{#词源}}<div class="sec"><span class="label">词源</span>'
                        "{{词源}}</div>{{/词源}}",
            }
        ],
    }
    existing = ankiconnect("modelNames")
    if MODEL_NAME in existing:
        # 已存在则覆盖更新（保留已有笔记）
        ankiconnect("updateModelTemplates", model={
            "name": MODEL_NAME,
            "templates": model["cardTemplates"],
        })
        ankiconnect("updateModelStyling", model={
            "name": MODEL_NAME,
            "css": model["css"],
        })
        print(f"ℹ️ 笔记类型「{MODEL_NAME}」已存在，已更新模板和样式。")
    else:
        ankiconnect("createModel", **model)
        print(f"✅ 笔记类型已创建：{MODEL_NAME}")

    print("\n全部完成。现在可以在 KOReader 里查词 → Add to Anki 了。")


if __name__ == "__main__":
    main()
