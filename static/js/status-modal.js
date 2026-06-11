/**
 * Root-level status overlay — independent stacking context from the contact modal.
 */
(function () {
  const root = document.getElementById("status-modal");
  const backdrop = document.getElementById("status-modal-backdrop");
  const panel = document.getElementById("status-modal-panel");
  const titleNode = document.getElementById("status-modal-title");
  const headingNode = document.getElementById("status-modal-heading");
  const bodyNode = document.getElementById("status-modal-body");
  const okButton = document.getElementById("status-modal-ok");

  if (!root || !backdrop || !panel || !titleNode || !headingNode || !bodyNode || !okButton) {
    return;
  }

  const queue = [];
  /** @type {Array<(action: string) => void>} */
  const closeWaiters = [];
  /** @type {{ options: object, resolve: (action: string) => void } | null} */
  let activeItem = null;
  let cleanupListeners = null;
  let previousActiveElement = null;

  const buttonPalette = {
    primary: "app-btn app-btn-primary",
    success: "app-btn app-btn-primary",
    warning: "app-btn app-btn-secondary",
    danger: "app-btn app-btn-secondary",
    neutral: "app-btn app-btn-secondary",
  };

  const defaultOptions = {
    title: "",
    heading: "Notice",
    body: "",
    okText: "Close",
    okColor: "primary",
    closeOnEscape: true,
    closeOnBackdrop: true,
    panelClass: "app-modal-panel-confirm app-modal-size-sm",
    bodyClass: "app-modal-body-confirm whitespace-pre-line",
    headingClass: "app-modal-heading-confirm",
    onClose: null,
  };

  let panelCustomClasses = [];
  let bodyCustomClasses = [];
  let headingCustomClasses = [];

  function splitClasses(value) {
    if (!value) {
      return [];
    }
    return String(value).trim().split(/\s+/).filter(Boolean);
  }

  function applyCustomClasses(target, key, classString) {
    let previous = [];
    if (key === "panel") {
      previous = panelCustomClasses;
    } else if (key === "body") {
      previous = bodyCustomClasses;
    } else {
      previous = headingCustomClasses;
    }
    if (previous.length) {
      target.classList.remove(...previous);
    }
    const next = splitClasses(classString);
    if (next.length) {
      target.classList.add(...next);
    }
    if (key === "panel") {
      panelCustomClasses = next;
    } else if (key === "body") {
      bodyCustomClasses = next;
    } else {
      headingCustomClasses = next;
    }
  }

  function toSafeText(value) {
    if (value === null || value === undefined) {
      return "";
    }
    return String(value);
  }

  function normalizeOptions(options) {
    return { ...defaultOptions, ...(options || {}) };
  }

  function focusableElements() {
    return panel.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
  }

  function trapFocus(event) {
    if (event.key !== "Tab") {
      return;
    }
    const items = focusableElements();
    if (!items.length) {
      event.preventDefault();
      return;
    }
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
      return;
    }
    if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function notifyCloseWaiters(action) {
    const waiters = closeWaiters.splice(0, closeWaiters.length);
    waiters.forEach(function (resolve) {
      resolve(action);
    });
  }

  function close(action) {
    if (!activeItem) {
      return;
    }

    const item = activeItem;
    activeItem = null;

    root.classList.remove("is-open");
    root.setAttribute("aria-hidden", "true");
    document.body.classList.remove("status-modal-open");
    panel.removeAttribute("aria-busy");

    if (cleanupListeners) {
      cleanupListeners();
      cleanupListeners = null;
    }

    if (previousActiveElement && typeof previousActiveElement.focus === "function") {
      previousActiveElement.focus();
    }
    previousActiveElement = null;

    if (typeof item.options.onClose === "function") {
      try {
        item.options.onClose(action);
      } catch (error) {
        console.error("StatusModal onClose callback failed.");
      }
    }

    item.resolve(action);
    notifyCloseWaiters(action);
    window.setTimeout(processQueue, 0);
  }

  function bindListeners(options) {
    const onBackdrop = function () {
      if (options.closeOnBackdrop) {
        close("dismissed");
      }
    };
    const onOk = function () {
      close("ok");
    };
    const onKeyDown = function (event) {
      if (event.key === "Escape" && options.closeOnEscape) {
        event.preventDefault();
        close("dismissed");
        return;
      }
      trapFocus(event);
    };

    backdrop.addEventListener("click", onBackdrop);
    okButton.addEventListener("click", onOk);
    document.addEventListener("keydown", onKeyDown);

    return function () {
      backdrop.removeEventListener("click", onBackdrop);
      okButton.removeEventListener("click", onOk);
      document.removeEventListener("keydown", onKeyDown);
    };
  }

  function show(item) {
    const options = normalizeOptions(item.options);
    previousActiveElement = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    activeItem = { options: options, resolve: item.resolve };

    titleNode.textContent = toSafeText(options.title);
    headingNode.textContent = toSafeText(options.heading);
    bodyNode.textContent = toSafeText(options.body);

    titleNode.classList.toggle("hidden", !titleNode.textContent);
    headingNode.classList.toggle("hidden", !headingNode.textContent);
    bodyNode.classList.toggle("hidden", !bodyNode.textContent);

    okButton.textContent = toSafeText(options.okText);
    const palette = buttonPalette[options.okColor] || buttonPalette.primary;
    okButton.className = palette;

    applyCustomClasses(panel, "panel", options.panelClass);
    applyCustomClasses(bodyNode, "body", options.bodyClass);
    applyCustomClasses(headingNode, "heading", options.headingClass);

    cleanupListeners = bindListeners(options);

    root.classList.add("is-open");
    root.setAttribute("aria-hidden", "false");
    document.body.classList.add("status-modal-open");
    window.setTimeout(function () {
      okButton.focus();
    }, 50);
  }

  function processQueue() {
    if (activeItem || queue.length === 0) {
      return;
    }
    show(queue.shift());
  }

  /**
   * @param {object} [options]
   * @returns {Promise<string>}
   */
  function open(options) {
    return new Promise(function (resolve) {
      queue.push({ options: options || {}, resolve: resolve });
      processQueue();
    });
  }

  /**
   * @returns {Promise<string>}
   */
  function closeAsync() {
    return new Promise(function (resolve) {
      if (!activeItem) {
        resolve("closed");
        return;
      }
      closeWaiters.push(resolve);
      close("closed");
    });
  }

  window.StatusModal = {
    open: open,
    alert: open,
    close: closeAsync,
  };
})();
