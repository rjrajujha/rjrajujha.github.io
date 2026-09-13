(function () {
  const cards = Array.from(document.querySelectorAll(".portfolio-project-card"));
  if (!cards.length) {
    return;
  }

  let expandedCard = null;

  function getSectionId(card) {
    const section = card.closest("[data-section]");
    return section ? section.getAttribute("data-section") || section.id : "";
  }

  function getToggle(card) {
    return card.querySelector(".portfolio-project-toggle");
  }

  function getDetails(card) {
    return card.querySelector(".portfolio-project-details");
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

  function setExpanded(card, expand, options) {
    options = options || {};
    const toggle = getToggle(card);
    const details = getDetails(card);
    if (!toggle || !details) {
      return;
    }

    if (expand && expandedCard && expandedCard !== card) {
      setExpanded(expandedCard, false, { updateHash: false });
    }

    card.classList.toggle("is-expanded", expand);
    toggle.setAttribute("aria-expanded", expand ? "true" : "false");
    toggle.querySelector(".portfolio-project-toggle-label").textContent = expand ? "Show less" : "Read more";
    details.hidden = !expand;

    if (expand) {
      expandedCard = card;
      renderMermaidInCard(card);
      if (options.updateHash !== false) {
        updateProjectHash(card, options.replaceHash !== false);
      }
    } else if (expandedCard === card) {
      expandedCard = null;
    }
  }

  function collapseAll() {
    cards.forEach(function (card) {
      if (card.classList.contains("is-expanded")) {
        setExpanded(card, false, { updateHash: false });
      }
    });
    expandedCard = null;
  }

  function focusProject(card, options) {
    if (!card) {
      return;
    }
    options = options || {};
    setExpanded(card, true, {
      updateHash: options.updateHash !== false,
      replaceHash: true,
    });
    if (options.scroll !== false) {
      card.scrollIntoView({ behavior: "smooth", block: "nearest" });
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
      focusProject(card, { scroll: true, updateHash: false });
    }
  }

  cards.forEach(function (card) {
    const toggle = getToggle(card);
    if (!toggle) {
      return;
    }
    toggle.addEventListener("click", function () {
      const isExpanded = card.classList.contains("is-expanded");
      if (isExpanded) {
        setExpanded(card, false);
      } else {
        focusProject(card, { scroll: false });
      }
    });
  });

  window.addEventListener("hashchange", focusFromHash);
  focusFromHash();

  document.querySelectorAll("[data-copy-endpoint]").forEach(function (button) {
    button.addEventListener("click", function () {
      const value = button.getAttribute("data-copy-endpoint") || "";
      if (!value || !navigator.clipboard) {
        return;
      }
      navigator.clipboard.writeText(value).then(function () {
        const original = button.textContent;
        button.textContent = "Copied";
        button.classList.add("is-copied");
        window.setTimeout(function () {
          button.textContent = original;
          button.classList.remove("is-copied");
        }, 1400);
      }).catch(function () {
        return;
      });
    });
  });

  window.PortfolioProjects = {
    focusProject: focusProject,
    collapseAll: collapseAll,
  };
})();
