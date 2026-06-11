(function () {
  const root = document.getElementById("chatbot-root");
  if (!root) {
    return;
  }

  const toggleBtn = document.getElementById("chatbot-toggle");
  const closeBtn = document.getElementById("chatbot-close");
  const clearBtn = document.getElementById("chatbot-clear");
  const panel = document.getElementById("chatbot-panel");
  const messagesScroller = document.getElementById("chatbot-messages");
  const messagesInner = document.getElementById("chatbot-messages-inner");
  const emptyState = document.getElementById("chatbot-empty-state");
  const form = document.getElementById("chatbot-form");
  const input = document.getElementById("chatbot-input");
  const sendButton = document.getElementById("chatbot-send");

  if (
    !toggleBtn ||
    !closeBtn ||
    !panel ||
    !messagesScroller ||
    !messagesInner ||
    !form ||
    !input ||
    !sendButton ||
    !emptyState
  ) {
    return;
  }

  function resizeInput() {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
  }

  input.addEventListener("input", resizeInput);
  resizeInput();

  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendButton.click();
    }
  });

  const storageKey = "ask-raju-chat-history";
  const urlPattern = /(https?:\/\/[^\s<]+)/g;
  let typingNode = null;
  let stickToBottom = true;

  function isOffline() {
    return typeof navigator !== "undefined" && navigator.onLine === false;
  }

  function naturalTypingDelay(inputText) {
    const baseDelay = 380;
    const lengthFactor = Math.min(String(inputText || "").length * 7, 480);
    return baseDelay + lengthFactor;
  }

  function isNearBottom() {
    const threshold = 72;
    return messagesScroller.scrollHeight - messagesScroller.scrollTop - messagesScroller.clientHeight <= threshold;
  }

  function setSuggestionsVisibility() {
    const hasMessages = messagesInner.querySelectorAll(".chat-row-user, .chat-row-assistant").length > 0;
    emptyState.classList.toggle("is-hidden", hasMessages);
    messagesInner.classList.toggle("is-idle", !hasMessages);
  }

  messagesInner.querySelectorAll("[data-chat-suggestion]").forEach(function (button) {
    button.addEventListener("click", function () {
      const prompt = button.getAttribute("data-chat-suggestion") || "";
      if (!prompt) {
        return;
      }
      input.value = prompt;
      resizeInput();
      sendButton.click();
    });
  });

  function scrollToBottom(force) {
    if (!force && !stickToBottom) {
      return;
    }
    window.requestAnimationFrame(function () {
      messagesScroller.scrollTop = messagesScroller.scrollHeight;
    });
  }

  messagesScroller.addEventListener(
    "scroll",
    function () {
      stickToBottom = isNearBottom();
    },
    { passive: true }
  );

  const markdownLinkPattern = /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g;

  function createChatLink(href, label) {
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
    anchor.className = "chat-link";
    anchor.textContent = label;
    return anchor;
  }

  function appendPlainUrls(target, text) {
    const parts = String(text || "").split(urlPattern);
    parts.forEach(function (part) {
      if (!part) {
        return;
      }
      if (/^https?:\/\//.test(part)) {
        let cleanUrl = part;
        let trailing = "";
        while (/[),.;!?]$/.test(cleanUrl)) {
          trailing = cleanUrl.slice(-1) + trailing;
          cleanUrl = cleanUrl.slice(0, -1);
        }

        target.appendChild(createChatLink(cleanUrl, cleanUrl));
        if (trailing) {
          target.appendChild(document.createTextNode(trailing));
        }
        return;
      }
      target.appendChild(document.createTextNode(part));
    });
  }

  function appendInlineMarkdown(target, text) {
    const raw = String(text || "");
    let lastIndex = 0;
    let match;

    markdownLinkPattern.lastIndex = 0;
    while ((match = markdownLinkPattern.exec(raw)) !== null) {
      if (match.index > lastIndex) {
        appendPlainUrls(target, raw.slice(lastIndex, match.index));
      }
      target.appendChild(createChatLink(match[2], match[1]));
      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < raw.length) {
      appendPlainUrls(target, raw.slice(lastIndex));
    }
  }

  function appendTextWithLinks(target, text) {
    const lines = String(text || "").split("\n");

    lines.forEach(function (line, index) {
      appendInlineMarkdown(target, line);
      if (index < lines.length - 1) {
        target.appendChild(document.createElement("br"));
      }
    });
  }

  function appendMessage(sender, text) {
    const row = document.createElement("div");
    row.className = sender === "user" ? "chat-row-user" : "chat-row-assistant";

    const bubble = document.createElement("div");
    bubble.className = sender === "user" ? "chat-bubble-user" : "chat-bubble-assistant";
    appendTextWithLinks(bubble, text);
    row.appendChild(bubble);

    messagesInner.appendChild(row);
    setSuggestionsVisibility();
    scrollToBottom(true);
  }

  function isMobileChat() {
    return window.matchMedia("(max-width: 1023px)").matches;
  }

  function syncKeyboardInset() {
    if (panel.classList.contains("is-closed") || !isMobileChat()) {
      panel.style.removeProperty("--keyboard-inset");
      return;
    }

    const viewport = window.visualViewport;
    if (!viewport) {
      panel.style.removeProperty("--keyboard-inset");
      return;
    }

    const inset = Math.max(0, window.innerHeight - viewport.height - viewport.offsetTop);
    if (inset > 0) {
      panel.style.setProperty("--keyboard-inset", inset + "px");
    } else {
      panel.style.removeProperty("--keyboard-inset");
    }
    scrollToBottom(false);
  }

  function setPanel(open) {
    panel.classList.toggle("is-closed", !open);
    panel.setAttribute("aria-hidden", String(!open));
    toggleBtn.classList.toggle("is-hidden", open);
    toggleBtn.setAttribute("aria-expanded", String(open));
    document.body.classList.toggle("chat-panel-open", open);

    if (open) {
      syncKeyboardInset();
      window.setTimeout(function () {
        input.focus({ preventScroll: true });
        scrollToBottom(true);
      }, 50);
    } else {
      panel.style.removeProperty("--keyboard-inset");
      input.blur();
    }
  }

  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", syncKeyboardInset);
  }

  input.addEventListener("focus", syncKeyboardInset);
  input.addEventListener("blur", function () {
    window.setTimeout(syncKeyboardInset, 100);
  });

  function setLoading(loading) {
    sendButton.disabled = loading;
    sendButton.setAttribute("aria-busy", String(loading));
    input.setAttribute("aria-busy", String(loading));
  }

  function keepInputFocused() {
    window.requestAnimationFrame(function () {
      if (panel.classList.contains("is-closed")) {
        return;
      }
      input.focus({ preventScroll: true });
      syncKeyboardInset();
    });
  }

  function showTypingIndicator() {
    if (typingNode) {
      return;
    }

    const row = document.createElement("div");
    row.className = "chat-row-assistant";
    row.setAttribute("data-chat-typing", "true");

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble-assistant chat-bubble-typing inline-flex items-center gap-2";

    const dotWrap = document.createElement("span");
    dotWrap.className = "chat-typing-dots";
    dotWrap.setAttribute("aria-hidden", "true");
    dotWrap.innerHTML = "<span></span><span></span><span></span>";
    bubble.appendChild(dotWrap);

    row.appendChild(bubble);
    messagesInner.appendChild(row);
    typingNode = row;
    setSuggestionsVisibility();
    scrollToBottom(true);
  }

  function hideTypingIndicator() {
    if (!typingNode) {
      return;
    }
    typingNode.remove();
    typingNode = null;
    setSuggestionsVisibility();
  }

  function getCookie(name) {
    const cookieValue = document.cookie
      .split(";")
      .map(function (cookie) {
        return cookie.trim();
      })
      .find(function (cookie) {
        return cookie.startsWith(name + "=");
      });
    return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
  }

  function csrfToken() {
    const tokenFromCookie = getCookie("csrftoken");
    if (tokenFromCookie) {
      return tokenFromCookie;
    }
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") || "" : "";
  }

  function safeParse(raw) {
    try {
      return JSON.parse(raw);
    } catch (error) {
      return [];
    }
  }

  function collectHistory() {
    const entries = [];
    messagesInner.querySelectorAll(".chat-row-user, .chat-row-assistant").forEach(function (row) {
      if (row.hasAttribute("data-chat-typing")) {
        return;
      }
      const bubble = row.querySelector(".chat-bubble-user, .chat-bubble-assistant");
      if (!bubble) {
        return;
      }
      entries.push({
        role: row.classList.contains("chat-row-user") ? "user" : "assistant",
        content: bubble.textContent || "",
      });
    });
    return entries;
  }

  function saveHistory() {
    try {
      localStorage.setItem(storageKey, JSON.stringify(collectHistory().slice(-20)));
    } catch (error) {
      return;
    }
  }

  function loadHistory() {
    let entries = [];
    try {
      entries = safeParse(localStorage.getItem(storageKey) || "[]");
    } catch (error) {
      entries = [];
    }
    if (!Array.isArray(entries) || !entries.length) {
      return false;
    }

    entries.forEach(function (entry) {
      if (!entry || !entry.role || !(entry.content || entry.text)) {
        return;
      }
      appendMessage(entry.role === "user" ? "user" : "assistant", entry.text || entry.content);
    });
    return true;
  }

  function clearConversation() {
    hideTypingIndicator();
    messagesInner.querySelectorAll(".chat-row-user, .chat-row-assistant").forEach(function (row) {
      row.remove();
    });
    try {
      localStorage.removeItem(storageKey);
    } catch (error) {
      return;
    }
    stickToBottom = true;
    setSuggestionsVisibility();
    input.focus({ preventScroll: true });
    scrollToBottom(true);
  }

  async function confirmClearConversation() {
    if (window.GlobalModal && typeof window.GlobalModal.confirm === "function") {
      const action = await window.GlobalModal.confirm({
        title: "",
        heading: "Clear conversation?",
        body: "This will permanently remove the current conversation history from this device.",
        cancelText: "Cancel",
        submitText: "Clear Conversation",
        panelClass: "app-modal-panel-confirm",
        headingClass: "app-modal-heading-confirm",
        bodyClass: "app-modal-body-confirm",
      });
      return action === "submit";
    }
    return window.confirm("Clear this conversation?");
  }

  function syncChatbotVisibility() {
    const offline = isOffline();
    root.hidden = offline;
    if (offline) {
      setPanel(false);
    }
  }

  window.addEventListener("online", syncChatbotVisibility);
  window.addEventListener("offline", syncChatbotVisibility);
  syncChatbotVisibility();

  toggleBtn.addEventListener("click", function () {
    const isHidden = panel.classList.contains("is-closed");
    setPanel(isHidden);

    if (isHidden && messagesInner.querySelectorAll(".chat-row-user, .chat-row-assistant").length === 0) {
      loadHistory();
      setSuggestionsVisibility();
    }
  });

  closeBtn.addEventListener("click", function () {
    setPanel(false);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !panel.classList.contains("is-closed")) {
      setPanel(false);
    }
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", async function () {
      const confirmed = await confirmClearConversation();
      if (confirmed) {
        clearConversation();
      }
    });
  }

  sendButton.addEventListener("pointerdown", function (event) {
    event.preventDefault();
  });

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const message = input.value.trim();
    if (!message) {
      return;
    }

    const historyForRequest = collectHistory()
      .slice(-8)
      .map(function (entry) {
        return { role: entry.role, content: entry.content };
      });

    stickToBottom = true;
    appendMessage("user", message);
    input.value = "";
    resizeInput();
    keepInputFocused();
    setLoading(true);
    showTypingIndicator();
    keepInputFocused();

    try {
      const typingDelay = naturalTypingDelay(message);
      const responsePromise = fetch("/chatbot/api/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify({ message: message, history: historyForRequest }),
      });
      await new Promise(function (resolve) {
        window.setTimeout(resolve, typingDelay);
      });

      const response = await responsePromise;

      let data = {};
      try {
        data = await response.json();
      } catch (error) {
        data = {};
      }
      hideTypingIndicator();
      if (!response.ok) {
        throw new Error(data.error || "The assistant could not process the request.");
      }

      appendMessage("assistant", data.reply || "I could not generate a useful reply right now.");
      saveHistory();
    } catch (error) {
      hideTypingIndicator();
      appendMessage("assistant", "I could not complete that request right now. Please try again in a moment.");
    } finally {
      setLoading(false);
      keepInputFocused();
      scrollToBottom(true);
    }
  });

  setSuggestionsVisibility();
})();
