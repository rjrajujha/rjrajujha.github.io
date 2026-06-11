(function () {
  const root = document.getElementById("global-modal");
  if (!root) {
    return;
  }

  const backdrop = document.getElementById("global-modal-backdrop");
  const panel = document.getElementById("global-modal-panel");
  const titleNode = document.getElementById("global-modal-title");
  const headingNode = document.getElementById("global-modal-heading");
  const bodyNode = document.getElementById("global-modal-body");
  const cancelButton = document.getElementById("global-modal-cancel");
  const okButton = document.getElementById("global-modal-ok");
  const submitButton = document.getElementById("global-modal-submit");
  const closeButton = document.getElementById("global-modal-close");
  const actionButtons = [cancelButton, okButton, submitButton];

  if (
    !backdrop ||
    !panel ||
    !titleNode ||
    !headingNode ||
    !bodyNode ||
    !cancelButton ||
    !okButton ||
    !submitButton ||
    !closeButton
  ) {
    return;
  }

  const queue = [];
  /** @type {Array<(action: string) => void>} */
  const closeWaiters = [];
  let activeState = null;
  let cleanupListeners = null;
  let previousActiveElement = null;

  const sizeClassMap = {
    sm: "app-modal-size-sm",
    md: "app-modal-size-md",
    lg: "app-modal-size-lg",
    xl: "app-modal-size-xl",
    "2xl": "app-modal-size-2xl",
    full: "app-modal-size-full",
  };

  const textSizeMap = {
    xs: "text-xs",
    sm: "text-sm",
    base: "text-base",
    lg: "text-lg",
  };

  const fontMap = {
    body: "font-body",
    mono: "font-mono",
    heading: "font-heading",
  };

  const buttonPalette = {
    neutral: "app-btn app-btn-secondary",
    primary: "app-btn app-btn-primary",
    success: "app-btn app-btn-primary",
    warning: "app-btn app-btn-secondary",
    danger: "app-btn app-btn-secondary",
  };

  const defaultOptions = {
    title: "",
    heading: "Notice",
    body: "",
    size: "md",
    textSize: "sm",
    fontStyle: "body",
    showOk: true,
    showSubmit: false,
    showCancel: false,
    okText: "OK",
    submitText: "Submit",
    cancelText: "Cancel",
    okColor: "primary",
    submitColor: "success",
    cancelColor: "neutral",
    closeOnEscape: true,
    closeOnBackdrop: true,
    showCloseButton: false,
    contentNode: null,
    contentSelector: "",
    loading: false,
    disabled: false,
    onOk: null,
    onSubmit: null,
    onCancel: null,
    onClose: null,
    onConfirm: null,
    panelClass: "",
    bodyClass: "",
    headingClass: "",
    titleClass: "",
  };

  const customClassState = {
    panel: [],
    body: [],
    heading: [],
    title: [],
  };

  function splitClasses(value) {
    if (!value) {
      return [];
    }
    return String(value)
      .trim()
      .split(/\s+/)
      .filter(Boolean);
  }

  function applyCustomClass(target, key, classString) {
    const previous = customClassState[key];
    if (previous.length) {
      target.classList.remove(...previous);
    }
    const next = splitClasses(classString);
    if (next.length) {
      target.classList.add(...next);
    }
    customClassState[key] = next;
  }

  let contentRestoreState = null;

  function resolveContentNode(options) {
    if (options.contentNode instanceof HTMLElement) {
      return options.contentNode;
    }
    if (options.contentSelector) {
      return document.querySelector(options.contentSelector);
    }
    return null;
  }

  function restoreContentNode() {
    if (!contentRestoreState) {
      return;
    }

    const state = contentRestoreState;
    contentRestoreState = null;

    if (state.placeholder && state.placeholder.parentNode) {
      state.placeholder.replaceWith(state.node);
    } else if (state.parent) {
      if (state.nextSibling && state.nextSibling.parentNode === state.parent) {
        state.parent.insertBefore(state.node, state.nextSibling);
      } else {
        state.parent.appendChild(state.node);
      }
    }

    if (state.sourceContainer) {
      state.sourceContainer.setAttribute("aria-hidden", "true");
    }
  }

  function mountContentNode(node, options) {
    if (!node) {
      return;
    }

    restoreContentNode();

    const parent = node.parentNode;
    const nextSibling = node.nextSibling;
    const sourceContainer = parent && parent.id === "contact-modal-source" ? parent : null;
    const placeholder = document.createComment("global-modal-content-placeholder");

    if (parent) {
      parent.replaceChild(placeholder, node);
    }

    contentRestoreState = {
      node: node,
      parent: parent,
      nextSibling: nextSibling,
      placeholder: placeholder,
      sourceContainer: sourceContainer,
    };

    if (sourceContainer) {
      sourceContainer.removeAttribute("aria-hidden");
    }

    bodyNode.innerHTML = "";
    bodyNode.appendChild(node);
    bodyNode.classList.remove("hidden");
  }

  function focusInitialTarget(options) {
    const contentNode = resolveContentNode(options);
    if (contentNode) {
      const firstField = contentNode.querySelector(
        "input:not([type='hidden']):not([disabled]), textarea:not([disabled]), select:not([disabled])"
      );
      if (firstField && typeof firstField.focus === "function") {
        firstField.focus();
        return;
      }
    }
    panel.focus();
  }

  function toSafeText(value) {
    if (value === null || value === undefined) {
      return "";
    }
    return String(value);
  }

  function normalizeOptions(options) {
    return {
      ...defaultOptions,
      ...(options || {}),
    };
  }

  function setButtonStyle(button, paletteName, customClass, fallback) {
    const palette = buttonPalette[paletteName] || buttonPalette[fallback];
    const extra = splitClasses(customClass);
    button.className = extra.length ? palette + " " + extra.join(" ") : palette;
  }

  function setLoading(isLoading) {
    if (!activeState) {
      return;
    }
    activeState.loading = Boolean(isLoading);
    const disabled = Boolean(activeState.loading || activeState.options.disabled);
    actionButtons.forEach(function (button) {
      button.disabled = disabled;
    });
    panel.setAttribute("aria-busy", disabled ? "true" : "false");
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

  function closeModal(action) {
    if (!activeState) {
      return;
    }

    const state = activeState;
    activeState = null;

    root.classList.remove("is-open");
    root.setAttribute("aria-hidden", "true");
    document.body.classList.remove("overflow-hidden");
    panel.removeAttribute("aria-busy");

    if (cleanupListeners) {
      cleanupListeners();
      cleanupListeners = null;
    }

    restoreContentNode();

    if (previousActiveElement && typeof previousActiveElement.focus === "function") {
      previousActiveElement.focus();
    }
    previousActiveElement = null;

    if (typeof state.options.onClose === "function") {
      try {
        state.options.onClose(action);
      } catch (error) {
        console.error("GlobalModal onClose callback failed.");
      }
    }

    state.resolve(action);
    notifyCloseWaiters(action);
    window.setTimeout(processQueue, 0);
  }

  async function handleAction(action) {
    if (!activeState || activeState.loading) {
      return;
    }

    const options = activeState.options;
    let callback = null;
    if (action === "ok") {
      callback = options.onOk || options.onConfirm;
    } else if (action === "submit") {
      callback = options.onSubmit || options.onConfirm;
    } else if (action === "cancel") {
      callback = options.onCancel;
    }

    if (!callback) {
      closeModal(action);
      return;
    }

    try {
      const result = callback(action);
      if (result && typeof result.then === "function") {
        setLoading(true);
        const resolved = await result;
        setLoading(false);
        if (resolved === false) {
          return;
        }
      } else if (result === false) {
        return;
      }
      closeModal(action);
    } catch (error) {
      setLoading(false);
      console.error("GlobalModal callback failed.");
    }
  }

  function applyState(state) {
    const options = state.options;
    const contentNode = resolveContentNode(options);
    const usesCustomContent = Boolean(contentNode);

    titleNode.textContent = toSafeText(options.title);
    headingNode.textContent = toSafeText(options.heading || defaultOptions.heading);

    titleNode.classList.toggle("hidden", !titleNode.textContent);
    headingNode.classList.toggle("hidden", !headingNode.textContent);

    if (usesCustomContent) {
      bodyNode.textContent = "";
      mountContentNode(contentNode, options);
    } else {
      restoreContentNode();
      bodyNode.textContent = toSafeText(options.body);
      bodyNode.classList.toggle("hidden", !bodyNode.textContent);
    }

    cancelButton.textContent = toSafeText(options.cancelText || defaultOptions.cancelText);
    okButton.textContent = toSafeText(options.okText || defaultOptions.okText);
    submitButton.textContent = toSafeText(options.submitText || defaultOptions.submitText);

    setButtonStyle(cancelButton, options.cancelColor, options.cancelButtonClass, "neutral");
    setButtonStyle(okButton, options.okColor, options.okButtonClass, "primary");
    setButtonStyle(submitButton, options.submitColor, options.submitButtonClass, "success");

    cancelButton.classList.toggle("hidden", !options.showCancel || usesCustomContent);
    okButton.classList.toggle("hidden", !options.showOk || usesCustomContent);
    submitButton.classList.toggle("hidden", !options.showSubmit || usesCustomContent);
    closeButton.classList.toggle("hidden", !options.showCloseButton);

    document.getElementById("global-modal-actions").classList.toggle("hidden", usesCustomContent);

    panel.classList.remove(...Object.values(sizeClassMap));
    panel.classList.add(sizeClassMap[options.size] || sizeClassMap.md);

    bodyNode.classList.remove(...Object.values(textSizeMap), ...Object.values(fontMap));
    bodyNode.classList.add(
      textSizeMap[options.textSize] || textSizeMap.sm,
      fontMap[options.fontStyle] || fontMap.body
    );

    applyCustomClass(panel, "panel", options.panelClass);
    applyCustomClass(bodyNode, "body", options.bodyClass);
    applyCustomClass(headingNode, "heading", options.headingClass);
    applyCustomClass(titleNode, "title", options.titleClass);

    setLoading(Boolean(options.loading));
  }

  function bindListeners(options) {
    const onBackdrop = function () {
      if (options.closeOnBackdrop && !(activeState && activeState.loading)) {
        closeModal("dismissed");
      }
    };
    const onCancel = function () {
      handleAction("cancel");
    };
    const onOk = function () {
      handleAction("ok");
    };
    const onSubmit = function () {
      handleAction("submit");
    };
    const onCloseButton = function () {
      if (!(activeState && activeState.loading)) {
        closeModal("dismissed");
      }
    };
    const onKeyDown = function (event) {
      if (event.key === "Escape" && options.closeOnEscape && !(activeState && activeState.loading)) {
        event.preventDefault();
        closeModal("dismissed");
        return;
      }
      trapFocus(event);
    };

    backdrop.addEventListener("click", onBackdrop);
    cancelButton.addEventListener("click", onCancel);
    okButton.addEventListener("click", onOk);
    submitButton.addEventListener("click", onSubmit);
    closeButton.addEventListener("click", onCloseButton);
    document.addEventListener("keydown", onKeyDown);

    return function () {
      backdrop.removeEventListener("click", onBackdrop);
      cancelButton.removeEventListener("click", onCancel);
      okButton.removeEventListener("click", onOk);
      submitButton.removeEventListener("click", onSubmit);
      closeButton.removeEventListener("click", onCloseButton);
      document.removeEventListener("keydown", onKeyDown);
    };
  }

  function show(item) {
    previousActiveElement = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    activeState = {
      options: normalizeOptions(item.options),
      resolve: item.resolve,
      loading: false,
    };

    applyState(activeState);
    cleanupListeners = bindListeners(activeState.options);

    root.classList.add("is-open");
    root.setAttribute("aria-hidden", "false");
    document.body.classList.add("overflow-hidden");
    window.setTimeout(function () {
      focusInitialTarget(activeState.options);
    }, 50);
  }

  function processQueue() {
    if (activeState || queue.length === 0) {
      return;
    }
    show(queue.shift());
  }

  function open(options) {
    return new Promise(function (resolve) {
      queue.push({
        options: options || {},
        resolve: resolve,
      });
      processQueue();
    });
  }

  function alert(options) {
    if (window.StatusModal && typeof window.StatusModal.alert === "function") {
      return window.StatusModal.alert(options);
    }
    const opts = options || {};
    return open({
      ...opts,
      showOk: true,
      showCancel: false,
      showSubmit: false,
    });
  }

  function confirm(options) {
    const opts = options || {};
    return open({
      ...opts,
      showOk: false,
      showCancel: true,
      showSubmit: true,
      submitText: opts.submitText || "Confirm",
    });
  }

  /**
   * @returns {Promise<string>}
   */
  function close() {
    return new Promise(function (resolve) {
      if (!activeState) {
        resolve("closed");
        return;
      }
      closeWaiters.push(resolve);
      closeModal("closed");
    });
  }

  window.GlobalModal = {
    open: open,
    alert: alert,
    confirm: confirm,
    setLoading: setLoading,
    close: close,
  };

  function messageConfig(message) {
    const level = (message.level || "").toLowerCase();
    const tags = (message.tags || "").toLowerCase();
    const normalized = tags || level;

    if (normalized.includes("error")) {
      return { title: "Error", heading: "Action Required", okColor: "danger" };
    }
    if (normalized.includes("warning")) {
      return { title: "Warning", heading: "Check This", okColor: "warning" };
    }
    if (normalized.includes("success")) {
      return { title: "Success", heading: "Done", okColor: "success" };
    }
    return { title: "Info", heading: "Update", okColor: "primary" };
  }

  function showDjangoMessages() {
    const fallback = document.getElementById("flash-messages-fallback");
    if (!fallback) {
      return;
    }

    const messageNodes = fallback.querySelectorAll("[data-flash-message='true']");
    if (!messageNodes.length) {
      return;
    }
    fallback.classList.add("hidden");

    messageNodes.forEach(function (node) {
      const message = {
        level: node.getAttribute("data-level") || "",
        tags: node.getAttribute("data-tags") || "",
        text: node.textContent || "",
      };
      const config = messageConfig(message);
      if (window.StatusModal && typeof window.StatusModal.alert === "function") {
        window.StatusModal.alert({
          title: config.title,
          heading: config.heading,
          body: toSafeText(message && message.text),
          okText: "Close",
          okColor: config.okColor,
        });
      } else {
        alert({
          title: config.title,
          heading: config.heading,
          body: toSafeText(message && message.text),
          okText: "Close",
          okColor: config.okColor,
        });
      }
    });
  }

  showDjangoMessages();
})();
