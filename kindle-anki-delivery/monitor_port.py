#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控 8765 端口的入站连接来源。
作用：判断 Kindle 的请求到底有没有到达电脑，以及来源 IP 是谁。
纯标准库，零依赖。
"""
import subprocess
import time
import re

PORT = "8765"

def snapshot():
    """抓取当前 8765 端口的连接快照，返回 [(本地地址, 远程地址, 状态), ...]"""
    out = subprocess.run(
        ["netstat", "-ano", "-p", "TCP"],
        capture_output=True, text=True, errors="ignore"
    ).stdout
    lines = out.splitlines()
    result = []
    for line in lines:
        if PORT in line:
            # 过滤掉纯监听行和本机回环
            if "LISTENING" in line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                local = parts[1]
                remote = parts[2]
                state = parts[3] if len(parts) > 3 else ""
                result.append((local, remote, state))
    return result

def main():
    print(f"开始监控 {PORT} 端口的入站连接（每 1 秒刷新）...")
    print("在 Kindle 上点 Add to Anki 或 Test，看下面是否出现来自 192.168.61.225 的连接。")
    print("=" * 60)
    seen = set()
    try:
        while True:
            conns = snapshot()
            for c in conns:
                key = (c[0], c[1])
                # 只显示非本机回环的新连接（重点看是否来自 Kindle）
                remote = c[1]
                # 排除本机 127.0.0.1 和电脑自己 192.168.61.44
                if "127.0.0.1" in remote or "192.168.61.44" in remote:
                    continue
                if key not in seen:
                    seen.add(key)
                    ts = time.strftime("%H:%M:%S")
                    print(f"[{ts}] 新连接: 本地={c[0]}  <-  远程={c[1]}  状态={c[2]}")
                    # 特别提示 Kindle
                    if "192.168.61.225" in remote:
                        print(f"          ^^^ 这是 Kindle 的连接！请求已到达电脑 ✓")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n监控结束。")

if __name__ == "__main__":
    main()
