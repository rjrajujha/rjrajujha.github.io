(function () {
  const palette = document.getElementById("command-palette");
  const input = document.getElementById("command-palette-input");
  const resultsEl = document.getElementById("command-palette-results");
  const openTriggers = document.querySelectorAll("[data-command-palette-open]");

  if (!palette || !input || !resultsEl) {
    return;
  }

  const RESULT_LIMIT = 24;
  const TYPE_ORDER = { project: 0, section: 1 };

  let index = [];
  try {
    const raw = document.getElementById("search-index-data");
    index = raw ? JSON.parse(raw.textContent || "[]") : [];
  } catch (error) {
    index = [];
  }

  let filtered = index.slice();
  let selectedIndex = 0;
  let isOpen = false;
  let activeQuery = "";
  /** @type {HTMLElement | null} */
  let previousActiveElement = null;

  const ICONS = {
    folder:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"></path></svg>',
    rocket:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M14 3c3 2 5 5 5 9 0 4-2 7-5 9M9 21H5v-4M14 3L9 8"></path></svg>',
    mail:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"></rect><path stroke-linecap="round" d="M3 7l9 6 9-6"></path></svg>',
  };

  function normalize(text) {
    return (text || "").toLowerCase().trim();
  }

  function iconForItem(item) {
    if (item.type === "project") {
      return ICONS.rocket;
    }
    if (item.url === "#open-contact") {
      return ICONS.mail;
    }
    return ICONS.folder;
  }

  function typeLabel(item) {
    if (item.url === "#open-contact") {
      return "Contact";
    }
    return item.type === "project" ? "Project" : "Section";
  }

  function compareItems(a, b) {
    const typeDelta = (TYPE_ORDER[a.type] ?? 9) - (TYPE_ORDER[b.type] ?? 9);
    if (typeDelta !== 0) {
      return typeDelta;
    }
    return a.title.localeCompare(b.title);
  }

  function scoreItem(item, query) {
    if (!query) {
      return TYPE_ORDER[item.type] ?? 9;
    }

    const q = normalize(query);
    const title = normalize(item.title);
    const subtitle = normalize(item.subtitle || "");
    let score = 0;

    if (item.type === "project") {
      if (title === q) {
        score = 1000;
      } else if (title.startsWith(q)) {
        score = 850;
      } else if (title.includes(q)) {
        score = 700;
      } else if (subtitle.includes(q)) {
        score = 400;
      }
    } else if (title === q) {
      score = 600;
    } else if (title.startsWith(q)) {
      score = 500;
    } else if (title.includes(q)) {
      score = 350;
    }

    return score;
  }

  function search(query) {
    const trimmed = (query || "").trim();
    if (!trimmed) {
      return index.slice().sort(compareItems);
    }

    return index
      .map(function (item) {
        return { item: item, score: scoreItem(item, trimmed) };
      })
      .filter(function (row) {
        return row.score > 0;
      })
      .sort(function (a, b) {
        if (b.score !== a.score) {
          return b.score - a.score;
        }
        return compareItems(a.item, b.item);
      })
      .slice(0, RESULT_LIMIT)
      .map(function (row) {
        return row.item;
      });
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function highlightMatch(text, query) {
    const source = text || "";
    const q = normalize(query);
    if (!q) {
      return escapeHtml(source);
    }
    const lower = source.toLowerCase();
    const matchIndex = lower.indexOf(q);
    if (matchIndex === -1) {
      return escapeHtml(source);
    }
    const before = source.slice(0, matchIndex);
    const match = source.slice(matchIndex, matchIndex + q.length);
    const after = source.slice(matchIndex + q.length);
    return (
      escapeHtml(before) +
      '<mark class="command-palette-mark">' +
      escapeHtml(match) +
      "</mark>" +
      escapeHtml(after)
    );
  }

  function optionId(idx) {
    return "command-palette-option-" + idx;
  }

  function syncActiveDescendant() {
    if (!filtered.length) {
      input.removeAttribute("aria-activedescendant");
      return;
    }
    input.setAttribute("aria-activedescendant", optionId(selectedIndex));
  }

  function setSelectedIndex(nextIndex, options) {
    const opts = options || {};
    if (!filtered.length) {
      selectedIndex = 0;
      syncActiveDescendant();
      return;
    }

    selectedIndex = Math.max(0, Math.min(nextIndex, filtered.length - 1));
    resultsEl.querySelectorAll(".command-palette-item[data-index]").forEach(function (el) {
      const idx = Number(el.getAttribute("data-index"));
      const active = idx === selectedIndex;
      el.classList.toggle("is-selected", active);
      el.setAttribute("aria-selected", String(active));
    });
    syncActiveDescendant();

    if (opts.scroll) {
      window.requestAnimationFrame(function () {
        const selected = resultsEl.querySelector(".command-palette-item.is-selected");
        if (selected) {
          selected.scrollIntoView({ block: "nearest", inline: "nearest" });
        }
      });
    }
  }

  function renderResults() {
    resultsEl.innerHTML = "";

    if (!filtered.length) {
      const empty = document.createElement("li");
      empty.className = "command-palette-empty";
      empty.setAttribute("role", "presentation");
      empty.innerHTML =
        '<p class="command-palette-empty-title">No results found</p>' +
        '<p class="command-palette-empty-hint">Try searching for a project or section.</p>';
      resultsEl.appendChild(empty);
      syncActiveDescendant();
      return;
    }

    filtered.forEach(function (item, idx) {
      const li = document.createElement("li");
      li.id = optionId(idx);
      li.className = "command-palette-item" + (idx === selectedIndex ? " is-selected" : "");
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", String(idx === selectedIndex));
      li.setAttribute("data-index", String(idx));

      const icon = document.createElement("span");
      icon.className = "command-palette-item-icon";
      icon.innerHTML = iconForItem(item);

      const body = document.createElement("span");
      body.className = "command-palette-item-body";

      const title = document.createElement("span");
      title.className = "command-palette-item-title";
      title.innerHTML = highlightMatch(item.title, activeQuery);

      const subtitle = document.createElement("span");
      subtitle.className = "command-palette-item-subtitle";
      subtitle.textContent = item.subtitle || typeLabel(item);

      body.appendChild(title);
      body.appendChild(subtitle);
      li.appendChild(icon);
      li.appendChild(body);

      li.addEventListener("mouseenter", function () {
        setSelectedIndex(idx, { scroll: false });
      });
      li.addEventListener("mousedown", function (event) {
        event.preventDefault();
      });
      li.addEventListener("click", function (event) {
        event.preventDefault();
        executeItem(item);
      });

      resultsEl.appendChild(li);
    });

    syncActiveDescendant();
  }

  function openPalette() {
    previousActiveElement = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    isOpen = true;
    palette.classList.remove("is-closed");
    palette.classList.add("is-open");
    palette.setAttribute("aria-hidden", "false");
    input.setAttribute("aria-expanded", "true");
    input.value = "";
    activeQuery = "";
    filtered = search("");
    selectedIndex = 0;
    resultsEl.scrollTop = 0;
    renderResults();
    window.requestAnimationFrame(function () {
      input.focus({ preventScroll: true });
    });
    document.body.style.overflow = "hidden";
  }

  function closePalette() {
    isOpen = false;
    palette.classList.add("is-closed");
    palette.classList.remove("is-open");
    palette.setAttribute("aria-hidden", "true");
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    document.body.style.overflow = "";

    if (previousActiveElement && typeof previousActiveElement.focus === "function") {
      previousActiveElement.focus({ preventScroll: true });
    }
    previousActiveElement = null;
  }

  function navigateToUrl(url) {
    if (!url) {
      return;
    }

    if (url === "#open-contact") {
      if (window.ContactModal && typeof window.ContactModal.open === "function") {
        window.ContactModal.open();
      }
      return;
    }

    if (url.indexOf("http") === 0) {
      window.open(url, "_blank", "noopener,noreferrer");
      return;
    }

    let path = url.charAt(0) === "/" ? url : "/" + url.replace(/^\/?/, "");
    const hashIndex = path.indexOf("#");
    if (hashIndex !== -1) {
      const pathname = path.slice(0, hashIndex) || "/";
      const hash = path.slice(hashIndex);
      const primarySection = hash.replace(/^#/, "").split("#")[0];
      const onHome = window.location.pathname === "/";
      const sectionExists = Boolean(primarySection && document.getElementById(primarySection));

      if (pathname === "/" && (!onHome || !sectionExists)) {
        window.location.assign("/" + hash);
        return;
      }

      if (window.history && window.history.pushState) {
        window.history.pushState(null, "", pathname + hash);
      } else {
        window.location.hash = hash;
      }
      if (window.DocsNav && typeof window.DocsNav.scrollToAnchor === "function") {
        window.requestAnimationFrame(function () {
          window.DocsNav.scrollToAnchor(hash);
        });
      }
      return;
    }

    window.location.href = path;
  }

  function executeItem(item) {
    closePalette();
    if (item && item.url) {
      navigateToUrl(item.url);
    }
  }

  function onInput() {
    activeQuery = input.value.trim();
    filtered = search(input.value);
    selectedIndex = 0;
    resultsEl.scrollTop = 0;
    renderResults();
  }

  openTriggers.forEach(function (trigger) {
    trigger.addEventListener("click", openPalette);
  });

  palette.querySelectorAll("[data-command-palette-close]").forEach(function (el) {
    el.addEventListener("click", closePalette);
  });

  input.addEventListener("input", onInput);

  input.addEventListener("keydown", function (event) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setSelectedIndex(selectedIndex + 1, { scroll: true });
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setSelectedIndex(selectedIndex - 1, { scroll: true });
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (filtered[selectedIndex]) {
        executeItem(filtered[selectedIndex]);
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      closePalette();
    }
  });

  document.addEventListener("keydown", function (event) {
    const isK = event.key === "k" || event.key === "K";
    const meta = event.metaKey || event.ctrlKey;
    if (isK && meta) {
      event.preventDefault();
      if (isOpen) {
        closePalette();
      } else {
        openPalette();
      }
    }
  });

  window.CommandPalette = { open: openPalette, close: closePalette, navigateToUrl: navigateToUrl };
})();
