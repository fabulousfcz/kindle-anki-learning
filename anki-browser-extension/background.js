// 生词一键进 Anki - 后台脚本（Service Worker）
// 通过 AnkiConnect 把选中单词添加到「英语词汇-词根词源」笔记类型

const ANKICONNECT_URL = "http://127.0.0.1:8765";

// 默认配置（可在 popup 里修改）
const DEFAULTS = {
  deckName: "英语生词本",
  modelName: "英语词汇-词根词源",
  wordField: "单词",
  allowDuplicate: false,
  duplicateScope: "notetype",
  tag: "浏览器",
};

// 读取配置
async function getConfig() {
  const saved = await chrome.storage.sync.get(DEFAULTS);
  return { ...DEFAULTS, ...saved };
}

// 调用 AnkiConnect
async function ankiconnect(action, params) {
  const body = JSON.stringify({ action, version: 6, params: params || {} });
  const resp = await fetch(ANKICONNECT_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
  const data = await resp.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return data.result;
}

// 添加单词到 Anki
async function addWord(word) {
  const cfg = await getConfig();
  // 构造字段对象：只有「单词」字段填词，其余留空（由监听器补全）
  const fields = { [cfg.wordField]: word };
  const note = {
    deckName: cfg.deckName,
    modelName: cfg.modelName,
    fields: fields,
    options: {
      allowDuplicate: cfg.allowDuplicate,
      duplicateScope: cfg.duplicateScope,
    },
    tags: [cfg.tag],
  };
  return ankiconnect("addNote", { note });
}

// 创建右键菜单
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "add-word-to-anki",
    title: "把这个词加进 Anki",
    contexts: ["selection"],
  });
});

// 处理右键菜单点击
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "add-word-to-anki") {
    const word = (info.selectionText || "").trim();
    if (!word) return;
    try {
      await addWord(word);
      notifySuccess(word);
    } catch (e) {
      notifyError(word, e);
    }
  }
});

// 处理来自 content script 的快捷键请求
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "ADD_WORD") {
    const word = (msg.word || "").trim();
    if (!word) {
      sendResponse({ ok: false, error: "empty" });
      return true;
    }
    addWord(word)
      .then((id) => {
        sendResponse({ ok: true, id, word });
      })
      .catch((e) => {
        sendResponse({ ok: false, error: String(e.message || e), word });
      });
    return true; // 异步响应
  }
});

// 成功提示（通过徽标 + 通知）
function notifySuccess(word) {
  chrome.action.setBadgeText({ text: "✓" });
  chrome.action.setBadgeBackgroundColor({ color: "#2e8b57" });
  setTimeout(() => chrome.action.setBadgeText({ text: "" }), 2000);
}

function notifyError(word, e) {
  const msg = String(e.message || e);
  // 重复提示用不同颜色
  const isDup = /duplicate/i.test(msg);
  chrome.action.setBadgeText({ text: isDup ? "重" : "!" });
  chrome.action.setBadgeBackgroundColor({
    color: isDup ? "#d2691e" : "#c0392b",
  });
  setTimeout(() => chrome.action.setBadgeText({ text: "" }), 3000);
}
