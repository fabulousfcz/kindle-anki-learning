#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
固化 AnkiConnect 配置：确保 webBindAddress 始终为 0.0.0.0，防止被重置回 127.0.0.1。

用途：每次启动 Anki 前运行一次（或配合启动器），自动把配置写回正确值。
纯标准库，零依赖。
"""
import json
import os
import sys

# AnkiConnect 插件的 config.json 路径（按需修改）
ADDON_DIR = os.path.expandvars(
    r"%APPDATA%\Anki2\addons21\2055492159"
)
CONFIG_PATH = os.path.join(ADDON_DIR, "config.json")

# 期望的配置值
EXPECTED = {
    "apiKey": None,
    "apiLogPath": None,
    "webBindAddress": "0.0.0.0",
    "webBindPort": 8765,
    "webCorsOriginList": ["*"],
    "ignoreOriginList": [],
}

def main():
    if not os.path.exists(CONFIG_PATH):
        print(f"[错误] 找不到 AnkiConnect 配置：{CONFIG_PATH}")
        print("       请确认 AnkiConnect 插件（ID 2055492159）已安装。")
        sys.exit(1)

    # 读取当前配置
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    changed = False
    for key, val in EXPECTED.items():
        if config.get(key) != val:
            print(f"[修复] {key}: {config.get(key)!r} -> {val!r}")
            config[key] = val
            changed = True

    if not changed:
        print("[正常] 配置已是正确状态：webBindAddress = 0.0.0.0")
    else:
        # 写入
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"[完成] 配置已固化，请重启 Anki 使其生效。")

    # 打印最终状态
    print(f"\n当前 webBindAddress = {config.get('webBindAddress')!r}")
    print(f"当前 webBindPort    = {config.get('webBindPort')!r}")

if __name__ == "__main__":
    main()
