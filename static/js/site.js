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

  function getContactForm() {
    return document.querySelector("#contact-modal-source [data-contact-form='true']");
  }

  /** @returns {Promise<void>} */
  async function closeContactModal() {
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
        document.body.classList.remove("contact-modal-open");
      },
    });
    document.body.classList.add("contact-modal-open");
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

  const contactQuery = new URLSearchParams(window.location.search).get("open");
  if (contactQuery === "contact") {
    openContactModal();
    if (window.history.replaceState) {
      const params = new URLSearchParams(window.location.search);
      params.delete("open");
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

  const submitButton = contactForm.querySelector("button[type='submit']");
  const cancelButton = contactForm.querySelector("[data-contact-cancel]");
  if (!submitButton) {
    return;
  }

  const defaultSubmitText = submitButton.textContent || "Send Message";

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
    subject: {
      input: contactForm.querySelector("#id_subject"),
      error: contactForm.querySelector("#contact-error-subject"),
      validate: function (value) {
        const trimmed = value.trim();
        if (!trimmed) {
          return "Please enter a subject.";
        }
        if (trimmed.length < 4) {
          return "Subject should be at least 4 characters.";
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
  }

  function showFieldError(fieldName, message) {
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

    if (firstInvalid) {
      firstInvalid.focus();
    }
    return valid;
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

  if (cancelButton) {
    cancelButton.addEventListener("click", function () {
      clearAllErrors();
      void closeContactModal();
    });
  }

  async function submitWithAjax() {
    const formData = new FormData(contactForm);
    const response = await fetch(contactForm.action, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      body: formData,
    });

    let data = {};
    try {
      data = await response.json();
    } catch (error) {
      data = {};
    }

    if (response.ok && data.success) {
      return { ok: true };
    }

    return {
      ok: false,
      message: data.message || "",
      errors: data.errors || {},
      status: response.status,
    };
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

    if (!validateContactForm()) {
      return;
    }

    submitButton.disabled = true;
    submitButton.textContent = "Sending...";

    try {
      const result = await submitWithAjax();

      if (result.ok) {
        contactForm.reset();
        clearAllErrors();
        await closeContactModal();
        showStatusModal(
          "Message Sent",
          "Thanks for reaching out.\n\nYour message has been successfully submitted and a confirmation email has been sent."
        );
        return;
      }

      if (result.status === 400 && result.errors && Object.keys(result.errors).length) {
        applyServerErrors(result.errors);
        return;
      }

      showStatusModal(
        "Unable to Send Message",
        "Something went wrong while sending your message.\n\nPlease try again in a few moments."
      );
    } catch (error) {
      showStatusModal(
        "Unable to Send Message",
        "Something went wrong while sending your message.\n\nPlease try again in a few moments."
      );
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = defaultSubmitText;
    }
  });
})();
