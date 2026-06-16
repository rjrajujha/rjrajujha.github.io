(function () {
  const sections = Array.from(document.querySelectorAll("[data-section]"));
  const navLinks = Array.from(document.querySelectorAll("[data-section-nav]"));
  const contactNavLinks = Array.from(document.querySelectorAll("[data-contact-nav]"));
  const mobileToggle = document.getElementById("mobile-sidebar-toggle");
  const mobileClose = document.getElementById("mobile-sidebar-close");
  const sidebar = document.getElementById("docs-sidebar");
  const backdrop = document.getElementById("docs-sidebar-backdrop");

  let scrollLock = false;
  let scrollLockTimer = null;

  function normalizeSectionId(sectionId) {
    if (sectionId === "about") {
      return "intro";
    }
    return sectionId;
  }

  function openProjectDetails(target) {
    if (!target) {
      return;
    }
    const card = target.closest(".portfolio-project-card");
    if (!card) {
      return;
    }
    if (window.PortfolioProjects) {
      window.PortfolioProjects.focusProject(card, { scroll: false, updateHash: true });
    }
  }

  function setSidebarOpen(open) {
    if (!sidebar) {
      return;
    }
    sidebar.classList.toggle("is-open", open);
    if (backdrop) {
      backdrop.classList.toggle("is-open", open);
      backdrop.setAttribute("aria-hidden", String(!open));
    }
    if (mobileToggle) {
      mobileToggle.setAttribute("aria-expanded", String(open));
    }
    document.body.classList.toggle("sidebar-open", open);
  }

  function closeSidebar() {
    setSidebarOpen(false);
  }

  function setActiveSection(sectionId) {
    const normalized = normalizeSectionId(sectionId);
    navLinks.forEach(function (link) {
      const isActive = link.getAttribute("data-section-nav") === normalized;
      link.classList.toggle("is-active", isActive);
      if (isActive) {
        link.setAttribute("aria-current", "location");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  function updateHash(sectionId, replace) {
    const normalized = normalizeSectionId(sectionId);
    if (normalized === "intro") {
      return;
    }
    const nextHash = "#" + normalized;
    if (window.location.hash === nextHash) {
      return;
    }
    const method = replace ? "replaceState" : "pushState";
    if (window.history[method]) {
      window.history[method](null, "", nextHash);
    } else {
      window.location.hash = nextHash;
    }
  }

  function lockScrollSync() {
    scrollLock = true;
    clearTimeout(scrollLockTimer);
    scrollLockTimer = setTimeout(function () {
      scrollLock = false;
    }, 800);
  }

  function scrollToSection(sectionId) {
    const normalized = normalizeSectionId(sectionId);

    if (normalized === "contact") {
      if (window.ContactModal && typeof window.ContactModal.open === "function") {
        window.ContactModal.open();
      }
      return;
    }

    const target = document.getElementById(normalized);
    if (!target) {
      window.location.assign("/#" + normalized);
      return;
    }
    lockScrollSync();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
    if (normalized !== "intro") {
      setActiveSection(normalized);
      updateHash(normalized, false);
    }
  }

  function scrollToAnchor(hash) {
    if (!hash || hash === "#") {
      return;
    }

    const normalized = hash.replace(/^#/, "");
    if (normalized === "contact" || normalized === "open-contact") {
      if (window.ContactModal && typeof window.ContactModal.open === "function") {
        window.ContactModal.open();
      }
      return;
    }

    const parts = normalized.split("#").filter(Boolean);
    if (!parts.length) {
      return;
    }

    if (parts[0] === "contact" || parts[0] === "open-contact") {
      if (window.ContactModal && typeof window.ContactModal.open === "function") {
        window.ContactModal.open();
      }
      return;
    }

    lockScrollSync();
    const sectionId = normalizeSectionId(parts[0]);
    let target = document.getElementById(sectionId);

    if (parts.length > 1) {
      const inner = document.getElementById(parts[parts.length - 1]);
      if (inner) {
        target = inner;
      }
    }

    if (target) {
      openProjectDetails(target);
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      if (sectionId !== "intro") {
        setActiveSection(sectionId);
        const hashParts = [sectionId];
        if (parts.length > 1 && parts[parts.length - 1] !== sectionId) {
          hashParts.push(parts[parts.length - 1]);
        }
        const nextHash = "#" + hashParts.join("#");
        if (window.history && window.history.replaceState) {
          window.history.replaceState(null, "", window.location.pathname + nextHash);
        }
      }
      return;
    }

    window.location.assign("/#" + parts.join("#"));
  }

  if (navLinks.length && sections.length) {
    const observer = new IntersectionObserver(
      function (entries) {
        if (scrollLock || document.body.classList.contains("sidebar-open")) {
          return;
        }
        const visible = entries
          .filter(function (entry) {
            return entry.isIntersecting;
          })
          .sort(function (a, b) {
            return b.intersectionRatio - a.intersectionRatio;
          });

        if (!visible.length) {
          return;
        }

        const sectionId = visible[0].target.getAttribute("data-section");
        if (sectionId && sectionId !== "intro") {
          setActiveSection(sectionId);
          updateHash(sectionId, true);
        }
      },
      {
        root: null,
        rootMargin: "-20% 0px -60% 0px",
        threshold: [0, 0.1, 0.25, 0.5],
      }
    );

    sections.forEach(function (section) {
      observer.observe(section);
    });
  }

  navLinks.forEach(function (link) {
    link.addEventListener("click", function (event) {
      const sectionId = link.getAttribute("data-section-nav");
      if (!sectionId) {
        return;
      }
      event.preventDefault();
      scrollToSection(sectionId);
      closeSidebar();
    });
  });

  contactNavLinks.forEach(function (link) {
    link.addEventListener("click", function () {
      closeSidebar();
    });
  });

  window.addEventListener("hashchange", function () {
    scrollToAnchor(window.location.hash);
  });

  if (window.location.hash) {
    const hash = window.location.hash.replace(/^#/, "");
    if (hash === "contact" || hash === "open-contact") {
      if (window.ContactModal && typeof window.ContactModal.open === "function") {
        window.ContactModal.open();
      }
    } else {
      requestAnimationFrame(function () {
        scrollToAnchor(window.location.hash);
      });
    }
  } else if (sections.length) {
    const firstSection = sections.find(function (section) {
      return section.getAttribute("data-section") !== "intro";
    });
    if (firstSection) {
      setActiveSection(firstSection.getAttribute("data-section"));
    }
  }

  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener("click", function () {
      const willOpen = !sidebar.classList.contains("is-open");
      setSidebarOpen(willOpen);
    });
  }

  if (mobileClose) {
    mobileClose.addEventListener("click", closeSidebar);
  }

  if (backdrop) {
    backdrop.addEventListener("click", closeSidebar);
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && sidebar && sidebar.classList.contains("is-open")) {
      closeSidebar();
    }
  });

  window.DocsNav = {
    scrollToSection: scrollToSection,
    scrollToAnchor: scrollToAnchor,
    closeSidebar: closeSidebar,
  };
})();
