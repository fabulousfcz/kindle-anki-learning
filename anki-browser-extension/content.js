// 生词一键进 Anki - 页面脚本
// 选中英文单词后，在附近浮出一个「+Anki」小按钮，点击即加词

(function () {
  let btn = null;

  function createButton() {
    if (btn) return btn;
    btn = document.createElement("div");
    btn.textContent = "+Anki";
    btn.style.cssText = [
      "position: fixed",
      "z-index: 2147483647",
      "background: #0a6b5c",
      "color: #fff",
      "font: 600 13px/1 'Segoe UI', 'Microsoft YaHei', sans-serif",
      "padding: 6px 10px",
      "border-radius: 6px",
      "cursor: pointer",
      "box-shadow: 0 2px 8px rgba(0,0,0,0.25)",
      "user-select: none",
      "transition: background 0.15s",
      "display: none",
    ].join(";");
    btn.addEventListener("mouseenter", () => {
      btn.style.background = "#085b4e";
    });
    btn.addEventListener("mouseleave", () => {
      btn.style.background = "#0a6b5c";
    });
    btn.addEventListener("mousedown", (e) => {
      e.preventDefault();
      e.stopPropagation();
    });
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const sel = window.getSelection();
      const word = (sel ? sel.toString() : "").trim();
      if (!word) return;
      sendWord(word);
      hideButton();
      // 清除选区
      if (sel) sel.removeAllRanges();
    });
    document.body.appendChild(btn);
    return btn;
  }

  function showButton(x, y) {
    const b = createButton();
    b.style.left = x + "px";
    b.style.top = y + "px";
    b.style.display = "block";
  }

  function hideButton() {
    if (btn) btn.style.display = "none";
  }

  function sendWord(word) {
    chrome.runtime.sendMessage({ type: "ADD_WORD", word }, (resp) => {
      if (chrome.runtime.lastError) return;
      showToast(resp);
    });
  }

  function showToast(resp) {
    const t = document.createElement("div");
    let text, color;
    if (resp && resp.ok) {
      text = `✓ "${resp.word}" 已加入 Anki`;
      color = "#2e8b57";
    } else if (resp && /duplicate/i.test(resp.error || "")) {
      text = `⚠ "${resp.word}" 已在 Anki 里`;
      color = "#d2691e";
    } else {
      const err = resp && resp.error ? resp.error : "未知错误";
      text = `✗ 添加失败：${err}`;
      color = "#c0392b";
    }
    t.textContent = text;
    t.style.cssText = [
      "position: fixed",
      "z-index: 2147483647",
      "left: 50%",
      "top: 20px",
      "transform: translateX(-50%)",
      "background: #fff",
      "color: " + color,
      "font: 600 14px/1.5 'Segoe UI', 'Microsoft YaHei', sans-serif",
      "padding: 10px 16px",
      "border-radius: 8px",
      "box-shadow: 0 4px 16px rgba(0,0,0,0.2)",
      "border: 1px solid #eee",
      "transition: opacity 0.4s",
    ].join(";");
    document.body.appendChild(t);
    setTimeout(() => {
      t.style.opacity = "0";
      setTimeout(() => t.remove(), 400);
    }, 1800);
  }

  // 监听鼠标松开（选中文字后）
  document.addEventListener("mouseup", (e) => {
    setTimeout(() => {
      const sel = window.getSelection();
      const text = sel ? sel.toString().trim() : "";
      // 只处理「单个英文单词」的选中（避免整段选中也弹按钮）
      if (text && /^[A-Za-z][A-Za-z'’-]*$/.test(text) && text.length <= 40) {
        // 按钮出现在选区右下角附近
        const rect = sel.getRangeAt(0).getBoundingClientRect();
        const x = Math.min(rect.right + 8, window.innerWidth - 90);
        const y = Math.min(rect.bottom + 8, window.innerHeight - 40);
        showButton(x, y);
      } else {
        hideButton();
      }
    }, 10);
  });

  // 点击空白处隐藏按钮
  document.addEventListener("mousedown", (e) => {
    if (btn && e.target !== btn) hideButton();
  });
})();
