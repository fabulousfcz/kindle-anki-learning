# Kindle 生词学习系统（KOReader + Anki）

一个完整的 **Kindle 阅读 → 查词 → 自动生成 Anki 单词卡** 学习方案，卡片采用**墨墨背单词风格配色**。

在 Kindle 上阅读英文书时，遇到生词查词典后一键即可把「单词 / 音标 / 释义 / 例句 / 词根词缀 / 词源」写进 Anki，并自动用大模型补全例句、词根词缀和词源，最后以墨墨风格的卡片复习。

---

## 目录结构

```
.
├── anki.koplugin/           # KOReader 查词插件（含自动重试修复）
│   ├── ankiconnect.lua      # 连接 AnkiConnect 的核心逻辑（已加唤醒后自动重试）
│   ├── profiles/default.lua # 字段映射、牌组配置
│   └── ...
├── kindle-anki-delivery/    # 电脑端脚本（数据补全 + 初始化）
│   ├── setup_anki.py        # 创建 Anki 笔记类型（含墨墨配色模板）
│   ├── enrich_vocab.py      # 用 DeepSeek 补全例句/词根词缀/词源
│   ├── auto_enrich.py       # 自动补全（监听 Anki 新卡片）
│   ├── note_model.json      # 笔记类型定义 + 墨墨配色 CSS
│   ├── 墨墨风格卡片预览.html  # 卡片效果可视化预览
│   └── *.bat                # 一键启动脚本
└── anki-browser-extension/  # 浏览器扩展（辅助工具）
```

---

## 整体工作流

```
Kindle (KOReader)                电脑 (Anki + AnkiConnect)
   │  查词、点「添加到 Anki」           │
   │ ────── HTTP POST ────────────▶│  AnkiConnect 收到
   │                                │  → 写入 Anki（字段：单词/音标/释义/例句/词根词缀/词源）
   │                                │  → auto_enrich.py 监听新卡片
   │                                │     → DeepSeek 补全例句/词根/词源
   │                                │     → 更新回 Anki
   │  ◀─── 墨墨风格卡片复习（AnkiDroid）───│
```

---

## 快速开始

### 1. 电脑端

1. 安装 [Anki](https://apps.ankiweb.net/) 和 [AnkiConnect](https://ankiweb.net/shared/info/2055492159) 插件
2. 配置 AnkiConnect（`webBindAddress: "0.0.0.0"`，`webBindPort: 8765`，`webCorsOriginList: ["*"]`）
3. 运行 `setup_anki.py` 创建笔记类型（自动应用墨墨配色模板）
4. （可选）运行 `启动自动补全.bat`，开启大模型补全

### 2. Kindle 端

1. 将 `anki.koplugin/` 放到 Kindle 的 `koreader/plugins/` 目录
2. 在 KOReader 中：**搜索图标 → 设置 → Anki Settings**，填入电脑 IP 和端口（如 `http://192.168.61.44:8765`）
3. 阅读时查词典，点「添加到 Anki」即可

---

## 墨墨配色说明

卡片采用**墨墨背单词**的视觉风格：

| 元素 | 配色 |
|---|---|
| 顶部渐变 | `#79cfc6 → #4aab9f`（墨绿） |
| 单词 | `#1c3f54`（深蓝灰） |
| 音标标签 | `#43a498`（墨绿） |
| 助记标签 | `#54b8ad`（青绿） |
| 例句高亮 | `#e5514b`（墨墨红） |

实际卡片模板 CSS 定义在 `note_model.json`，可视化预览见 `墨墨风格卡片预览.html`。

---

## 已知问题与修复

### 问题：Kindle 休眠唤醒后连不上电脑（Host not reachable）

**根因**：Kindle 休眠后 WiFi 芯片深度省电，唤醒后需要一段时间才能恢复"主动发起连接"的能力。这不是电脑/防火墙/Clash 的问题，而是 Kindle 固件行为。

**修复**：`ankiconnect.lua` 已内置**自动重试**——唤醒后直接点「添加到 Anki」，若网络尚未恢复，笔记先本地保存，插件每 5 秒自动重试（最多 3 分钟），网络恢复后自动同步到 Anki。

详见 `anki.koplugin/自动重试修复说明.md`。

---

## 许可证

- `anki.koplugin/` 基于 [Ajatt-Tools/anki.koplugin](https://github.com/Ajatt-Tools/anki.koplugin)，遵循其 GPL 许可
- 其余脚本为本项目原创
