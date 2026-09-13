(function () {
  function canRegisterServiceWorker() {
    if (!("serviceWorker" in navigator)) {
      return false;
    }
    const hostname = window.location.hostname;
    const isLocalHost = hostname === "localhost" || hostname === "127.0.0.1";
    return window.location.protocol === "https:" && !isLocalHost;
  }

  function clearLocalServiceWorkers() {
    const hostname = window.location.hostname;
    const isLocalHost = hostname === "localhost" || hostname === "127.0.0.1";
    if (!isLocalHost || !("serviceWorker" in navigator)) {
      return;
    }

    navigator.serviceWorker.getRegistrations().then(function (registrations) {
      registrations.forEach(function (registration) {
        registration.unregister();
      });
    });

    if ("caches" in window) {
      caches.keys().then(function (keys) {
        keys
          .filter(function (key) {
            return key.indexOf("rj-portfolio-shell-") === 0;
          })
          .forEach(function (key) {
            caches.delete(key);
          });
      });
    }
  }

  function registerServiceWorker() {
    clearLocalServiceWorkers();
    if (!canRegisterServiceWorker()) {
      return;
    }
    window.addEventListener("load", function () {
      navigator.serviceWorker
        .register("/service-worker.js", { scope: "/", updateViaCache: "none" })
        .then(function (registration) {
          registration.update();
        })
        .catch(function () {
          return;
        });
    });
  }

  registerServiceWorker();

  function isMobileViewport() {
    return window.matchMedia("(max-width: 1023px)").matches;
  }

  function isCompactViewport() {
    return window.matchMedia("(max-width: 375px)").matches;
  }

  function getContactForm() {
    return (
      document.querySelector("#global-modal-body [data-contact-form='true']") ||
      document.querySelector("#contact-modal-source [data-contact-form='true']") ||
      document.querySelector("[data-contact-form='true']")
    );
  }

  function getCsrfToken(form) {
    const input = form.querySelector("input[name='csrfmiddlewaretoken']");
    if (input && input.value) {
      return input.value;
    }
    const meta = document.querySelector("meta[name='csrf-token']");
    return meta ? meta.getAttribute("content") || "" : "";
  }

  let turnstileWidgetId = null;

  function setTurnstileToken(token) {
    const form = getContactForm();
    if (!form) {
      return;
    }
    const tokenInput = form.querySelector("#id_cf_turnstile_response");
    if (tokenInput) {
      tokenInput.value = token || "";
    }
    const error = form.querySelector("#contact-error-turnstile");
    if (error && token) {
      error.hidden = true;
      error.textContent = "";
    }
  }

  function readTurnstileToken(form) {
    if (!form) {
      return "";
    }
    const ours = form.querySelector("#id_cf_turnstile_response");
    if (ours && ours.value.trim()) {
      return ours.value.trim();
    }
    const injected = form.querySelector("[name='cf-turnstile-response']");
    if (injected && injected.value.trim()) {
      if (ours) {
        ours.value = injected.value.trim();
      }
      return injected.value.trim();
    }
    if (window.turnstile && turnstileWidgetId !== null) {
      try {
        const response = window.turnstile.getResponse(turnstileWidgetId);
        if (response) {
          if (ours) {
            ours.value = response;
          }
          return response;
        }
      } catch (error) {
        return "";
      }
    }
    return "";
  }

  function withTurnstileApi(callback) {
    if (window.turnstile && typeof window.turnstile.render === "function") {
      callback(window.turnstile);
      return;
    }
    let attempts = 0;
    const timer = window.setInterval(function () {
      attempts += 1;
      if (window.turnstile && typeof window.turnstile.render === "function") {
        window.clearInterval(timer);
        callback(window.turnstile);
      } else if (attempts >= 60) {
        window.clearInterval(timer);
      }
    }, 100);
  }

  function destroyTurnstileWidget() {
    if (window.turnstile && turnstileWidgetId !== null) {
      try {
        window.turnstile.remove(turnstileWidgetId);
      } catch (error) {
        /* widget already gone */
      }
    }
    turnstileWidgetId = null;
    const form = getContactForm();
    if (form) {
      const container = form.querySelector("[data-turnstile-widget]");
      if (container) {
        container.innerHTML = "";
      }
      const tokenInput = form.querySelector("#id_cf_turnstile_response");
      if (tokenInput) {
        tokenInput.value = "";
      }
    }
  }

  function renderTurnstileWidget(form) {
    if (!form || form.getAttribute("data-turnstile-enabled") !== "true") {
      return;
    }
    const sitekey = (form.getAttribute("data-turnstile-sitekey") || "").trim();
    const container = form.querySelector("[data-turnstile-widget]");
    if (!sitekey || !container) {
      return;
    }

    withTurnstileApi(function (api) {
      destroyTurnstileWidget();
      const theme = document.documentElement.classList.contains("dark") ? "dark" : "light";
      turnstileWidgetId = api.render(container, {
        sitekey: sitekey,
        theme: theme,
        size: isCompactViewport() ? "compact" : "normal",
        callback: function (token) {
          setTurnstileToken(token);
        },
        "expired-callback": function () {
          setTurnstileToken("");
        },
        "error-callback": function () {
          setTurnstileToken("");
        },
      });
    });
  }

  /** @returns {Promise<void>} */
  async function closeContactModal() {
    destroyTurnstileWidget();
    if (window.GlobalModal && typeof window.GlobalModal.close === "function") {
      await window.GlobalModal.close();
    }
    document.body.classList.remove("contact-modal-open");
  }

  function openContactModal() {
    const form = getContactForm();
    if (!form || !window.GlobalModal || typeof window.GlobalModal.open !== "function") {
      return;
    }

    const mobile = isMobileViewport();
    window.GlobalModal.open({
      title: "",
      heading: "Contact",
      body: "",
      contentNode: form,
      showOk: false,
      showCancel: false,
      showSubmit: false,
      showCloseButton: true,
      size: mobile ? "full" : "lg",
      closeOnBackdrop: true,
      closeOnEscape: true,
      panelClass: mobile ? "app-modal-panel-sheet" : "app-modal-panel-contact",
      headingClass: "app-modal-heading-contact",
      bodyClass: "app-modal-body-contact",
      onClose: function () {
        destroyTurnstileWidget();
        document.body.classList.remove("contact-modal-open");
      },
    });
    document.body.classList.add("contact-modal-open");
    window.setTimeout(function () {
      renderTurnstileWidget(getContactForm());
    }, 0);
  }

  function showStatusModal(heading, body) {
    window.GlobalModal.alert({
      title: "",
      heading: heading,
      body: body,
      bodyClass: "app-modal-body-confirm whitespace-pre-line",
      panelClass: "app-modal-panel-confirm app-modal-size-md",
      headingClass: "app-modal-heading-confirm",
      okText: "Close",
    });
  }

  window.ContactModal = { open: openContactModal, close: closeContactModal };

  window.onContactTurnstileSuccess = function (token) {
    setTurnstileToken(token);
  };

  window.onContactTurnstileExpired = function () {
    setTurnstileToken("");
  };

  document.querySelectorAll("[data-contact-nav], [data-open-contact-modal]").forEach(function (trigger) {
    trigger.addEventListener("click", function (event) {
      event.preventDefault();
      openContactModal();
      const sidebar = document.getElementById("docs-sidebar");
      const mobileToggle = document.getElementById("mobile-sidebar-toggle");
      if (sidebar) {
        sidebar.classList.remove("is-open");
      }
      if (mobileToggle) {
        mobileToggle.setAttribute("aria-expanded", "false");
      }
    });
  });

  const params = new URLSearchParams(window.location.search);
  const contactQuery = params.get("open");
  const pendingVerifyChallenge = params.get("verify") || "";
  if (contactQuery === "contact") {
    openContactModal();
    if (window.history.replaceState) {
      params.delete("open");
      params.delete("verify");
      const query = params.toString();
      window.history.replaceState({}, "", window.location.pathname + (query ? "?" + query : ""));
    }
  }

  const contactForm = getContactForm();
  if (!contactForm || !window.fetch || !window.FormData) {
    return;
  }

  const hasModalApi =
    window.GlobalModal &&
    typeof window.GlobalModal.open === "function" &&
    typeof window.GlobalModal.alert === "function" &&
    typeof window.GlobalModal.close === "function";
  if (!hasModalApi) {
    return;
  }

  const submitButton = contactForm.querySelector("#contact-submit-button");
  const verifyButton = contactForm.querySelector("#contact-verify-button");
  const cancelButton = contactForm.querySelector("[data-contact-cancel]");
  const backButton = contactForm.querySelector("[data-contact-back]");
  const detailsStep = contactForm.querySelector('[data-contact-step="details"]');
  const otpStep = contactForm.querySelector('[data-contact-step="otp"]');
  const challengeInput = contactForm.querySelector("#id_challenge_id");
  const otpInput = contactForm.querySelector("#id_otp");
  const otpLead = contactForm.querySelector("[data-contact-otp-lead]");
  const otpCountdown = contactForm.querySelector("[data-contact-otp-countdown]");
  const messageInput = contactForm.querySelector("#id_message");
  const defaultOtpTtlSeconds = parseInt(contactForm.getAttribute("data-otp-ttl-seconds") || "600", 10);
  let otpCountdownTimer = null;
  let activeChallengeId = "";
  const turnstileEnabled = contactForm.getAttribute("data-turnstile-enabled") === "true";
  const verifyUrl = contactForm.getAttribute("data-verify-url") || "/contact/verify-otp/";
  if (!submitButton) {
    return;
  }

  const defaultSubmitText = submitButton.textContent || "Continue";
  const defaultVerifyText = verifyButton ? verifyButton.textContent || "Verify & Send" : "Verify & Send";

  const fieldConfig = {
    name: {
      input: contactForm.querySelector("#id_name"),
      error: contactForm.querySelector("#contact-error-name"),
      validate: function (value) {
        const trimmed = value.trim();
        if (!trimmed) {
          return "Please enter your name.";
        }
        if (trimmed.length < 2) {
          return "Please enter your full name.";
        }
        return "";
      },
    },
    email: {
      input: contactForm.querySelector("#id_email"),
      error: contactForm.querySelector("#contact-error-email"),
      validate: function (value) {
        const trimmed = value.trim();
        if (!trimmed) {
          return "Please enter your email address.";
        }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
          return "Please enter a valid email address.";
        }
        return "";
      },
    },
    message: {
      input: contactForm.querySelector("#id_message"),
      error: contactForm.querySelector("#contact-error-message"),
      validate: function (value) {
        const trimmed = value.trim();
        if (!trimmed) {
          return "Please enter a message.";
        }
        if (trimmed.split(/\s+/).filter(Boolean).length < 5) {
          return "Please include at least 5 words in your message.";
        }
        return "";
      },
    },
  };

  function clearFieldError(fieldName) {
    if (fieldName === "cf_turnstile_response") {
      const error = contactForm.querySelector("#contact-error-turnstile");
      if (error) {
        error.hidden = true;
        error.textContent = "";
      }
      return;
    }
    if (fieldName === "otp") {
      const error = contactForm.querySelector("#contact-error-otp");
      if (error) {
        error.hidden = true;
        error.textContent = "";
      }
      if (otpInput) {
        otpInput.removeAttribute("aria-invalid");
      }
      return;
    }
    const field = fieldConfig[fieldName];
    if (!field || !field.input || !field.error) {
      return;
    }
    field.error.textContent = "";
    field.error.hidden = true;
    field.input.removeAttribute("aria-invalid");
    field.input.removeAttribute("aria-describedby");
    const wrapper = field.input.closest("[data-contact-field]");
    if (wrapper) {
      wrapper.classList.remove("has-error");
    }
  }

  function clearAllErrors() {
    Object.keys(fieldConfig).forEach(clearFieldError);
    clearFieldError("otp");
    clearFieldError("cf_turnstile_response");
  }

  function showFieldError(fieldName, message) {
    if (fieldName === "cf_turnstile_response") {
      const error = contactForm.querySelector("#contact-error-turnstile");
      if (error) {
        error.textContent = message;
        error.hidden = false;
      }
      return;
    }
    if (fieldName === "otp") {
      const error = contactForm.querySelector("#contact-error-otp");
      if (error) {
        error.textContent = message;
        error.hidden = false;
      }
      if (otpInput) {
        otpInput.setAttribute("aria-invalid", "true");
        otpInput.focus();
      }
      return;
    }
    const field = fieldConfig[fieldName];
    if (!field || !field.input || !field.error) {
      return;
    }
    field.error.textContent = message;
    field.error.hidden = false;
    field.input.setAttribute("aria-invalid", "true");
    field.input.setAttribute("aria-describedby", field.error.id);
    const wrapper = field.input.closest("[data-contact-field]");
    if (wrapper) {
      wrapper.classList.add("has-error");
    }
  }

  function validateContactForm() {
    clearAllErrors();
    let firstInvalid = null;
    let valid = true;

    Object.keys(fieldConfig).forEach(function (fieldName) {
      const field = fieldConfig[fieldName];
      if (!field.input) {
        return;
      }
      const message = field.validate(field.input.value || "");
      if (message) {
        showFieldError(fieldName, message);
        valid = false;
        if (!firstInvalid) {
          firstInvalid = field.input;
        }
      }
    });

    if (turnstileEnabled) {
      const token = readTurnstileToken(contactForm);
      if (!token) {
        showFieldError("cf_turnstile_response", "Please complete the security check.");
        valid = false;
      }
    }

    if (firstInvalid) {
      firstInvalid.focus();
    }
    return valid;
  }

  function stopOtpCountdown() {
    if (otpCountdownTimer) {
      window.clearInterval(otpCountdownTimer);
      otpCountdownTimer = null;
    }
    if (otpCountdown) {
      otpCountdown.hidden = true;
      otpCountdown.textContent = "";
    }
  }

  function formatCountdown(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins <= 0) {
      return secs + " second" + (secs === 1 ? "" : "s");
    }
    if (secs === 0) {
      return mins + " minute" + (mins === 1 ? "" : "s");
    }
    return mins + " min " + secs + " sec";
  }

  function startOtpCountdown(secondsRemaining) {
    stopOtpCountdown();
    if (!otpCountdown || !secondsRemaining || secondsRemaining <= 0) {
      return;
    }
    let remaining = secondsRemaining;
    function tick() {
      if (remaining <= 0) {
        if (otpCountdownTimer) {
          window.clearInterval(otpCountdownTimer);
          otpCountdownTimer = null;
        }
        otpCountdown.textContent = "This code has expired. Go back and request a new one.";
        otpCountdown.hidden = false;
        return;
      }
      otpCountdown.textContent = "Code expires in " + formatCountdown(remaining) + ".";
      otpCountdown.hidden = false;
      remaining -= 1;
    }
    tick();
    otpCountdownTimer = window.setInterval(tick, 1000);
  }

  function autosizeMessage() {
    if (!messageInput) {
      return;
    }
    // Fixed floor height — never use height:"auto" (causes focus/click jump).
    const minHeight = 104;
    const maxHeight = Math.min(window.innerHeight * 0.32, 240);
    messageInput.style.height = minHeight + "px";
    const needed = messageInput.scrollHeight;
    if (needed > minHeight + 1) {
      messageInput.style.height = Math.min(needed, maxHeight) + "px";
    }
  }

  function showDetailsStep() {
    stopOtpCountdown();
    activeChallengeId = "";
    if (detailsStep) {
      detailsStep.hidden = false;
    }
    if (otpStep) {
      otpStep.hidden = true;
    }
    if (challengeInput) {
      challengeInput.value = "";
    }
    if (otpInput) {
      otpInput.value = "";
    }
    autosizeMessage();
  }

  function showOtpStep(form, challengeId, message, expiresInSeconds) {
    if (detailsStep) {
      detailsStep.hidden = true;
    }
    if (otpStep) {
      otpStep.hidden = false;
    }
    activeChallengeId = (challengeId || "").trim();
    if (challengeInput) {
      challengeInput.value = activeChallengeId;
    }
    if (otpLead && message) {
      otpLead.textContent = message;
    }
    clearFieldError("otp");
    const ttl =
      typeof expiresInSeconds === "number" && expiresInSeconds > 0
        ? expiresInSeconds
        : defaultOtpTtlSeconds;
    startOtpCountdown(ttl);
    if (otpInput) {
      otpInput.value = "";
      otpInput.focus();
    }
  }

  function resetTurnstile() {
    const form = getContactForm() || contactForm;
    const tokenInput = form.querySelector("#id_cf_turnstile_response");
    if (tokenInput) {
      tokenInput.value = "";
    }
    if (form.getAttribute("data-turnstile-enabled") === "true") {
      renderTurnstileWidget(form);
    }
  }

  Object.keys(fieldConfig).forEach(function (fieldName) {
    const field = fieldConfig[fieldName];
    if (!field.input) {
      return;
    }
    field.input.addEventListener("input", function () {
      clearFieldError(fieldName);
    });
  });

  if (otpInput) {
    otpInput.addEventListener("input", function () {
      clearFieldError("otp");
    });
  }

  if (messageInput) {
    messageInput.addEventListener("input", autosizeMessage);
    autosizeMessage();
  }

  if (cancelButton) {
    cancelButton.addEventListener("click", function () {
      clearAllErrors();
      showDetailsStep();
      void closeContactModal();
    });
  }

  if (backButton) {
    backButton.addEventListener("click", function () {
      clearAllErrors();
      showDetailsStep();
      resetTurnstile();
    });
  }

  async function postForm(url, formData) {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCsrfToken(contactForm),
      },
      body: formData,
    });

    let data = {};
    try {
      data = await response.json();
    } catch (error) {
      data = {};
    }

    return { response: response, data: data };
  }

  function applyServerErrors(errors) {
    clearAllErrors();
    let firstInvalid = null;

    Object.keys(errors).forEach(function (fieldName) {
      if (fieldName === "__all__") {
        return;
      }
      const messages = errors[fieldName];
      const message = Array.isArray(messages) ? messages[0] : String(messages || "");
      if (!message) {
        return;
      }
      showFieldError(fieldName, message);
      const field = fieldConfig[fieldName];
      if (field && field.input && !firstInvalid) {
        firstInvalid = field.input;
      }
    });

    if (firstInvalid) {
      firstInvalid.focus();
    }
  }

  contactForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    // On the OTP step, Enter should verify — never re-hit the submit cooldown.
    if (otpStep && !otpStep.hidden) {
      if (verifyButton && !verifyButton.disabled) {
        verifyButton.click();
      }
      return;
    }

    if (!validateContactForm()) {
      return;
    }

    if (submitButton.getAttribute("aria-busy") === "true") {
      return;
    }

    submitButton.disabled = true;
    submitButton.setAttribute("aria-busy", "true");
    submitButton.textContent = "Sending code…";

    try {
      const formData = new FormData(contactForm);
      const token = readTurnstileToken(contactForm);
      if (token) {
        formData.set("cf_turnstile_response", token);
        formData.set("cf-turnstile-response", token);
      }

      const result = await postForm(contactForm.action, formData);
      const data = result.data;
      const response = result.response;

      if (response.ok && data.success && data.requires_otp && data.challenge_id) {
        showOtpStep(
          contactForm,
          data.challenge_id,
          data.message || "",
          data.otp_expires_in_seconds
        );
        return;
      }

      if (response.status === 400 && data.errors && Object.keys(data.errors).length) {
        applyServerErrors(data.errors);
        resetTurnstile();
        return;
      }

      showStatusModal(
        "Unable to Continue",
        data.message || "Something went wrong while starting verification.\n\nPlease try again."
      );
      resetTurnstile();
    } catch (error) {
      showStatusModal(
        "Unable to Continue",
        "Something went wrong while starting verification.\n\nPlease try again."
      );
      resetTurnstile();
    } finally {
      submitButton.disabled = false;
      submitButton.removeAttribute("aria-busy");
      submitButton.textContent = defaultSubmitText;
    }
  });

  if (pendingVerifyChallenge) {
    showOtpStep(
      contactForm,
      pendingVerifyChallenge,
      "Enter the verification code sent to your email."
    );
  }

  if (verifyButton) {
    let verifyInFlight = false;
    verifyButton.addEventListener("click", async function () {
      clearFieldError("otp");
      const otpValue = otpInput ? otpInput.value.trim() : "";
      const challengeId = (activeChallengeId || (challengeInput ? challengeInput.value : "")).trim();
      if (!otpValue) {
        showFieldError("otp", "Enter the verification code from your email.");
        return;
      }
      if (!challengeId) {
        showFieldError("otp", "Verification session expired. Please start again.");
        showDetailsStep();
        return;
      }
      if (verifyInFlight) {
        return;
      }

      verifyInFlight = true;
      verifyButton.disabled = true;
      verifyButton.setAttribute("aria-busy", "true");
      verifyButton.textContent = "Verifying…";

      try {
        if (challengeInput) {
          challengeInput.value = challengeId;
        }
        const formData = new FormData();
        formData.append("challenge_id", challengeId);
        formData.append("otp", otpValue);
        formData.append("csrfmiddlewaretoken", getCsrfToken(contactForm));

        const result = await postForm(verifyUrl, formData);
        const data = result.data;
        const response = result.response;

        if (response.ok && data.success) {
          contactForm.reset();
          clearAllErrors();
          showDetailsStep();
          destroyTurnstileWidget();
          await closeContactModal();
          showStatusModal(
            "Message Sent",
            data.message ||
              "Thanks for reaching out.\n\nYour message has been verified and delivered."
          );
          return;
        }

        const message = data.message || "Verification failed. Please try again.";
        if (/expired|start again/i.test(message)) {
          stopOtpCountdown();
          activeChallengeId = "";
          if (otpCountdown) {
            otpCountdown.textContent = "This code has expired. Go back and request a new one.";
            otpCountdown.hidden = false;
          }
        }

        if (data.errors && data.errors.otp) {
          showFieldError("otp", Array.isArray(data.errors.otp) ? data.errors.otp[0] : data.errors.otp);
          return;
        }

        showFieldError("otp", message);
      } catch (error) {
        showFieldError("otp", "Verification failed. Please try again.");
      } finally {
        verifyInFlight = false;
        verifyButton.disabled = false;
        verifyButton.removeAttribute("aria-busy");
        verifyButton.textContent = defaultVerifyText;
      }
    });
  }
})();
