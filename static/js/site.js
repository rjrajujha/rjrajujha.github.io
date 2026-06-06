(function () {
  const menuToggle = document.getElementById("mobile-menu-toggle");
  const mobileNavPanel = document.getElementById("mobile-nav-panel");

  if (menuToggle && mobileNavPanel) {
    menuToggle.addEventListener("click", function () {
      const isOpen = !mobileNavPanel.classList.contains("hidden");
      mobileNavPanel.classList.toggle("hidden", isOpen);
      mobileNavPanel.classList.toggle("flex", !isOpen);
      menuToggle.setAttribute("aria-expanded", String(!isOpen));
    });

    mobileNavPanel.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        mobileNavPanel.classList.add("hidden");
        mobileNavPanel.classList.remove("flex");
        menuToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  const revealItems = document.querySelectorAll(".reveal");
  if (revealItems.length) {
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.15,
      }
    );

    revealItems.forEach(function (item, index) {
      if (!prefersReducedMotion) {
        item.style.setProperty("--reveal-delay", Math.min(index, 3) * 35 + "ms");
      }
      observer.observe(item);
    });
  }

  function closeMobileNav() {
    if (!mobileNavPanel || !menuToggle) {
      return;
    }
    mobileNavPanel.classList.add("hidden");
    mobileNavPanel.classList.remove("flex");
    menuToggle.setAttribute("aria-expanded", "false");
  }

  if (mobileNavPanel) {
    mobileNavPanel.querySelectorAll("[data-open-contact-modal]").forEach(function (trigger) {
      trigger.addEventListener("click", closeMobileNav);
    });
  }

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

  function openContactModal() {
    const form = document.querySelector("#contact-modal-source [data-contact-form='true']");
    if (!form || !window.GlobalModal || typeof window.GlobalModal.open !== "function") {
      return;
    }

    window.GlobalModal.open({
      title: "",
      heading: "Start a conversation",
      body: "",
      contentNode: form,
      showOk: false,
      showCancel: false,
      showSubmit: false,
      showCloseButton: true,
      size: "md",
      closeOnBackdrop: true,
      closeOnEscape: true,
      headingClass: "pr-8",
      panelClass: "max-h-[min(90dvh,40rem)] overflow-y-auto",
      bodyClass: "mt-4",
    });
  }

  document.querySelectorAll("[data-open-contact-modal]").forEach(function (trigger) {
    trigger.addEventListener("click", function (event) {
      event.preventDefault();
      openContactModal();
    });
  });

  const contactQuery = new URLSearchParams(window.location.search).get("open");
  if (contactQuery === "contact") {
    openContactModal();
    if (window.history.replaceState) {
      const params = new URLSearchParams(window.location.search);
      params.delete("open");
      const query = params.toString();
      window.history.replaceState({}, "", window.location.pathname + (query ? "?" + query : "") + window.location.hash);
    }
  }

  const contactForm = document.querySelector("[data-contact-form='true']");
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
  if (!submitButton) {
    return;
  }

  const defaultSubmitText = submitButton.textContent || "Send Message";

  function composeValidationMessage(errors) {
    if (!errors || typeof errors !== "object") {
      return "";
    }

    const lines = [];
    Object.keys(errors).forEach(function (field) {
      const fieldErrors = Array.isArray(errors[field]) ? errors[field] : [];
      if (!fieldErrors.length) {
        return;
      }
      const label = field === "__all__" ? "Form" : field.charAt(0).toUpperCase() + field.slice(1);
      lines.push(label + ": " + fieldErrors.join(", "));
    });
    return lines.join("\n");
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
      contactForm.reset();
      return {
        ok: true,
        message: data.message || "Your message was sent successfully.",
      };
    }

    return {
      ok: false,
      message: data.message || "We could not send your message. Please try again.",
      errors: data.errors || {},
    };
  }

  contactForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const formInContactModal = Boolean(document.getElementById("global-modal-body")?.contains(contactForm));

    submitButton.disabled = true;
    submitButton.textContent = "Sending...";

    if (!formInContactModal) {
      window.GlobalModal.open({
        title: "Contact",
        heading: "Sending message...",
        body: "Please wait while your message is being submitted.",
        showOk: false,
        showCancel: false,
        showSubmit: false,
        closeOnBackdrop: false,
        closeOnEscape: false,
      });
    }

    try {
      const result = await submitWithAjax();
      if (!formInContactModal) {
        window.GlobalModal.close();
      }

      if (result.ok) {
        contactForm.reset();
        if (formInContactModal) {
          window.GlobalModal.close();
        }
        window.GlobalModal.alert({
          title: "Contact",
          heading: "Message sent",
          body: result.message,
          okColor: "success",
          okText: "Close",
        });
        return;
      }

      const validationMessage = composeValidationMessage(result.errors);
      const fullMessage = validationMessage ? result.message + "\n\n" + validationMessage : result.message;
      window.GlobalModal.alert({
        title: "Contact",
        heading: "Could not send message",
        body: fullMessage,
        bodyClass: "whitespace-pre-line",
        okColor: "warning",
        okText: "Review",
      });
    } catch (error) {
      if (!formInContactModal) {
        window.GlobalModal.close();
      }
      window.GlobalModal.alert({
        title: "Contact",
        heading: "Temporary issue",
        body: "We could not submit your message right now. Please try again in a moment.",
        okColor: "warning",
        okText: "Close",
      });
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = defaultSubmitText;
    }
  });
})();
