// popup 脚本：加载/保存配置，测试连接
const DEFAULTS = {
  deckName: "英语生词本",
  modelName: "英语词汇-词根词源",
  wordField: "单词",
};

async function load() {
  const cfg = await chrome.storage.sync.get(DEFAULTS);
  document.getElementById("deckName").value = cfg.deckName;
  document.getElementById("modelName").value = cfg.modelName;
  document.getElementById("wordField").value = cfg.wordField;
}

async function save() {
  const cfg = {
    deckName: document.getElementById("deckName").value.trim() || DEFAULTS.deckName,
    modelName: document.getElementById("modelName").value.trim() || DEFAULTS.modelName,
    wordField: document.getElementById("wordField").value.trim() || DEFAULTS.wordField,
  };
  await chrome.storage.sync.set(cfg);
  const status = document.getElementById("status");
  status.textContent = "✓ 已保存";
  status.className = "ok";
}

async function testConnection() {
  const status = document.getElementById("status");
  try {
    const resp = await fetch("http://127.0.0.1:8765", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "version", version: 6 }),
    });
    const data = await resp.json();
    if (data.error) throw new Error(data.error);
    status.textContent = `✓ AnkiConnect 在线（v${data.result}）`;
    status.className = "ok";
  } catch (e) {
    status.textContent = "✗ 无法连接 Anki，请确认 Anki 已启动";
    status.className = "err";
  }
}

document.getElementById("save").addEventListener("click", save);
document.getElementById("save").addEventListener("dblclick", testConnection);

load();
testConnection();
