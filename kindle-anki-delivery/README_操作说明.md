# Kindle 生词 → Anki 词根词源卡片 · 完整方案

> 目标：在 KOReader 里选中生词 → 一键进 Anki 电脑版 → 自动补全「音标 + 释义 + 例句 + 词根词缀 + 词源」。

---

## 一、你的环境现状（已确认）

| 组件 | 状态 |
|---|---|
| Kindle Scribe 2024 | 已越狱 + 已装 KOReader |
| 电脑端 Anki | 已安装，已登录 AnkiWeb |
| AnkiConnect 插件 | 已装，`webBindAddress=0.0.0.0`、端口 8765 已配好 |
| DeepSeek API key | 已提供 |
| Python | 3.13.14 |

**只差最后一步：把 `anki.koplugin` 插件装到 Kindle。**

---

## 二、第一步：装插件到 Kindle（手动拖拽）

1. 在资源管理器打开 Kindle 设备（Scribe 是 MTP 便携设备，不是盘符）。
2. 进入 `koreader` → `plugins` 文件夹。
3. 把电脑上这个文件夹整个拖进去：
   ```
   C:\Users\Cysteine\WorkBuddy\2026-10-08-05-36-38\anki.koplugin\
   ```
   目标位置变成：`Kindle\koreader\plugins\anki.koplugin\`
4. 把配置文件也放进去（覆盖默认的 default.lua）：
   ```
   把 kindle-anki-delivery\default.lua 复制到
   Kindle\koreader\plugins\anki.koplugin\profiles\default.lua
   ```
5. 安全弹出 Kindle，拔线。
6. 在 Kindle 上**完全退出 KOReader 再重新打开**。

---

## 三、第二步：在电脑 Anki 里建笔记类型和牌组（跑脚本）

先确认电脑端 **Anki 已启动**，然后双击运行（或在终端执行）：

```
python C:\Users\Cysteine\WorkBuddy\2026-10-08-05-36-38\kindle-anki-delivery\setup_anki.py
```

> 用系统 Python：`py -3 setup_anki.py`
> 这会自动创建牌组「英语生词本」和笔记类型「英语词汇-词根词源」。

---

## 四、第三步：KOReader 里查词建卡

1. 让 **Kindle 和电脑连同一个 Wi-Fi**。
2. 在 KOReader 里读书，长按选中不认识的单词 → 弹出词典。
3. 词典弹窗里会出现一个 **「Add to Anki」** 按钮（插件加的）。
4. 点一下，单词 + 词典释义 + 原句就会通过 AnkiConnect 传到电脑 Anki。

> 如果按钮没出现：确认插件目录层级是 `koreader/plugins/anki.koplugin/`（不是多套一层）。

---

## 五、第四步：补全词根词缀 + 例句 + 词源（跑脚本）

在电脑上执行：

```
python C:\Users\Cysteine\WorkBuddy\2026-10-08-05-36-38\kindle-anki-delivery\enrich_vocab.py
```

脚本会自动：
1. 从 Anki 读取所有「英语词汇-词根词源」类型、但**词根词缀还没填**的生词；
2. 逐个调用 DeepSeek，生成音标、释义、例句（含翻译）、词根词缀、词源；
3. 回写到 Anki 对应字段。

常用参数：
```
--limit 20     只处理前 20 个
--dry-run      只列出要处理的词，不真正调用 API
```

---

## 六、完成后的卡片效果

- **正面**：单词 + 音标
- **背面**：释义 + 词根词缀 + 例句（含翻译）+ 词源

---

## 常见问题

- **Kindle 上看不到「Add to Anki」按钮**：插件没加载，完全退出 KOReader 重开；或检查目录层级。
- **点了按钮没反应 / 报连不上**：确认 Kindle 和电脑同一 Wi-Fi；确认 Anki 已开；AnkiConnect 端口 8765 未变。
- **enrich_vocab.py 报「连不上 AnkiConnect」**：Anki 没启动。
- **词根词缀是空的**：说明该词还没跑 enrich_vocab.py，跑一遍即可。
