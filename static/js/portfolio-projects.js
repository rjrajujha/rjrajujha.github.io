(function () {
  const cards = Array.from(document.querySelectorAll(".portfolio-project-card"));
  if (!cards.length) {
    return;
  }

  let activeCard = null;
  let ticking = false;

  function getSectionId(card) {
    const section = card.closest("[data-section]");
    return section ? section.getAttribute("data-section") || section.id : "";
  }

  function renderMermaidInCard(card) {
    if (!card || !window.mermaid) {
      return;
    }
    const nodes = card.querySelectorAll("pre.mermaid:not([data-processed])");
    if (!nodes.length) {
      return;
    }
    const isDark = document.documentElement.classList.contains("dark");
    window.mermaid.initialize({
      startOnLoad: false,
      theme: isDark ? "dark" : "neutral",
      securityLevel: "strict",
      fontFamily: "Inter, system-ui, sans-serif",
    });
    window.mermaid.run({ nodes: nodes }).catch(function () {
      return;
    });
  }

  function updateProjectHash(card, replace) {
    const sectionId = getSectionId(card);
    const slug = card.getAttribute("data-project");
    if (!sectionId || !slug) {
      return;
    }
    const nextHash = "#" + sectionId + "#" + slug;
    if (window.location.hash === nextHash) {
      return;
    }
    const url = window.location.pathname + nextHash;
    const method = replace ? "replaceState" : "pushState";
    if (window.history && window.history[method]) {
      window.history[method](null, "", url);
    }
  }

  function setActiveCard(card, options) {
    options = options || {};
    if (!card) {
      return;
    }
    if (card === activeCard && !options.force) {
      return;
    }

    cards.forEach(function (item) {
      item.classList.toggle("is-active", item === card);
    });

    activeCard = card;
    renderMermaidInCard(card);

    if (options.updateHash !== false) {
      updateProjectHash(card, options.replaceHash !== false);
    }
  }

  function clearActiveCard() {
    cards.forEach(function (item) {
      item.classList.remove("is-active");
    });
    activeCard = null;
  }

  function findFocusedCard() {
    const viewportAnchor = window.innerHeight * 0.4;
    let focused = null;
    let closestDistance = Infinity;

    cards.forEach(function (card) {
      const rect = card.getBoundingClientRect();
      if (rect.bottom <= 0 || rect.top >= window.innerHeight) {
        return;
      }
      const anchor = rect.top + Math.min(rect.height * 0.2, 80);
      const distance = Math.abs(anchor - viewportAnchor);
      if (distance < closestDistance) {
        closestDistance = distance;
        focused = card;
      }
    });

    return focused;
  }

  function refreshFocus() {
    const focused = findFocusedCard();
    if (focused) {
      setActiveCard(focused, { replaceHash: true });
      return;
    }
    clearActiveCard();
  }

  function onScroll() {
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(function () {
        refreshFocus();
        ticking = false;
      });
    }
  }

  function focusProject(card, options) {
    if (!card) {
      return;
    }
    options = options || {};
    setActiveCard(card, { updateHash: options.updateHash !== false, replaceHash: true, force: true });
    if (options.scroll !== false) {
      card.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function focusFromHash() {
    const hash = window.location.hash.replace(/^#/, "");
    if (!hash) {
      return;
    }
    const parts = hash.split("#").filter(Boolean);
    if (parts.length < 2) {
      return;
    }
    const slug = parts[parts.length - 1];
    const card = document.getElementById(slug);
    if (card && card.classList.contains("portfolio-project-card")) {
      focusProject(card, { scroll: false, updateHash: false });
    }
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });
  window.addEventListener("hashchange", focusFromHash);

  refreshFocus();
  focusFromHash();

  window.PortfolioProjects = {
    focusProject: focusProject,
    refreshFocus: refreshFocus,
  };
})();
