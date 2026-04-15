(function () {
  const root = document.getElementById("chatbot-root");
  if (!root) {
    return;
  }

  const toggleBtn = document.getElementById("chatbot-toggle");
  const closeBtn = document.getElementById("chatbot-close");
  const panel = document.getElementById("chatbot-panel");
  const messagesBox = document.getElementById("chatbot-messages");
  const form = document.getElementById("chatbot-form");
  const input = document.getElementById("chatbot-input");

  function appendMessage(sender, text) {
    const row = document.createElement("div");
    row.className = sender === "user" ? "chat-row-user" : "chat-row-assistant";

    const bubble = document.createElement("div");
    bubble.className = sender === "user" ? "chat-bubble-user" : "chat-bubble-assistant";
    bubble.textContent = text;

    row.appendChild(bubble);
    messagesBox.appendChild(row);
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }

  function setPanel(open) {
    panel.classList.toggle("hidden", !open);
    if (open) {
      input.focus();
    }
  }

  function getCookie(name) {
    const cookieValue = document.cookie
      .split(";")
      .map((cookie) => cookie.trim())
      .find((cookie) => cookie.startsWith(name + "="));
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

  toggleBtn.addEventListener("click", function () {
    const isHidden = panel.classList.contains("hidden");
    setPanel(isHidden);

    if (isHidden && messagesBox.children.length === 0) {
      appendMessage("assistant", "Hi, I am Raju's portfolio assistant. Ask me about projects, skills, or experience.");
    }
  });

  closeBtn.addEventListener("click", function () {
    setPanel(false);
  });

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const message = input.value.trim();
    if (!message) {
      return;
    }

    appendMessage("user", message);
    input.value = "";
    input.disabled = true;

    try {
      const response = await fetch("/chatbot/api/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify({ message: message }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "The assistant could not process the request.");
      }

      appendMessage("assistant", data.reply);
    } catch (err) {
      appendMessage("assistant", "I could not reach the AI service right now. Please try again in a moment.");
    } finally {
      input.disabled = false;
      input.focus();
    }
  });
})();
