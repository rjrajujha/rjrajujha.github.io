(function () {
  const palette = document.getElementById("command-palette");
  const input = document.getElementById("command-palette-input");
  const resultsEl = document.getElementById("command-palette-results");
  const openTriggers = document.querySelectorAll("[data-command-palette-open]");

  if (!palette || !input || !resultsEl) {
    return;
  }

  const RESULT_LIMIT = 50;
  const DEFAULT_PROJECT_LIMIT = 6;
  const TYPE_ORDER = { section: 0, project: 1, heading: 2, action: 3, link: 4 };
  const TYPE_SCORE_BONUS = { section: 40, project: 30, heading: 20, action: 10, link: 5 };

  let index = [];
  try {
    const raw = document.getElementById("search-index-data");
    index = raw ? JSON.parse(raw.textContent || "[]") : [];
  } catch (error) {
    index = [];
  }

  const staticActions = [
    {
      type: "action",
      title: "Contact",
      subtitle: "Open contact form",
      url: "#open-contact",
      text: "contact email message reach",
    },
    {
      type: "action",
      title: "Toggle theme",
      subtitle: "Switch light / dark / system",
      url: "#toggle-theme",
      text: "theme dark light mode appearance",
    },
    {
      type: "action",
      title: "Open GitHub",
      subtitle: "github.com/rjrajujha",
      url: "https://github.com/rjrajujha",
      text: "github source code repository",
    },
    {
      type: "action",
      title: "Open LinkedIn",
      subtitle: "linkedin.com/in/rjrajujha",
      url: "https://linkedin.com/in/rjrajujha",
      text: "linkedin profile",
    },
  ];

  const fullIndex = index.concat(staticActions);
  let filtered = fullIndex.slice();
  let selectedIndex = 0;
  let isOpen = false;
  /** @type {HTMLElement | null} */
  let previousActiveElement = null;

  function normalize(text) {
    return (text || "").toLowerCase().trim();
  }

  function typeBonus(item) {
    return TYPE_SCORE_BONUS[item.type] || 0;
  }

  function compareDefaultItems(a, b) {
    const typeDelta = (TYPE_ORDER[a.type] ?? 9) - (TYPE_ORDER[b.type] ?? 9);
    if (typeDelta !== 0) {
      return typeDelta;
    }
    return a.title.localeCompare(b.title);
  }

  function destinationKey(url) {
    if (!url) {
      return "";
    }
    const normalized = String(url).trim().toLowerCase();
    if (normalized === "#open-contact") {
      return "#open-contact";
    }
    const match = normalized.match(/^\/#([^#?]+)(?:#([^?#]+))?/);
    if (match) {
      const section = match[1];
      const fragment = match[2];
      if (!fragment || fragment === section) {
        return "/#" + section;
      }
    }
    return normalized;
  }

  function dedupeResults(items) {
    const seen = new Map();
    const result = [];

    items.forEach(function (item) {
      const key = destinationKey(item.url);
      const existing = seen.get(key);
      if (!existing) {
        seen.set(key, item);
        result.push(item);
        return;
      }
      if ((TYPE_ORDER[item.type] ?? 9) < (TYPE_ORDER[existing.type] ?? 9)) {
        const index = result.indexOf(existing);
        if (index >= 0) {
          result[index] = item;
        }
        seen.set(key, item);
      }
    });

    return result;
  }

  function buildDefaultList() {
    const deduped = dedupeResults(fullIndex);
    const sections = deduped.filter(function (item) {
      return item.type === "section";
    });
    const projects = deduped
      .filter(function (item) {
        return item.type === "project";
      })
      .slice(0, DEFAULT_PROJECT_LIMIT);
    const actions = deduped.filter(function (item) {
      return item.type === "action";
    });
    return sections.concat(projects, actions);
  }

  function scoreItem(item, query) {
    if (!query) {
      return 1;
    }

    const q = normalize(query);
    const title = normalize(item.title);
    const subtitle = normalize(item.subtitle || "");
    const text = normalize(item.text || "");
    let score = 0;

    if (title === q) {
      score = 1000;
    } else if (title.startsWith(q)) {
      score = 800;
    } else if (title.includes(q)) {
      score = 600;
    } else if (subtitle.includes(q)) {
      score = 400;
    } else if (text.includes(q)) {
      score = 200;
    }

    const tokens = q.split(/\s+/).filter(Boolean);
    if (tokens.length > 1) {
      let tokenScore = 0;
      tokens.forEach(function (token) {
        if (title.includes(token)) {
          tokenScore += 80;
        } else if (subtitle.includes(token)) {
          tokenScore += 40;
        } else if (text.includes(token)) {
          tokenScore += 20;
        }
      });
      score = Math.max(score, tokenScore);
    }

    if (score > 0) {
      score += typeBonus(item);
    }

    return score;
  }

  function search(query) {
    const trimmed = (query || "").trim();
    if (!trimmed) {
      return buildDefaultList();
    }

    return dedupeResults(
      fullIndex
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
          return compareDefaultItems(a.item, b.item);
        })
        .slice(0, RESULT_LIMIT)
        .map(function (row) {
          return row.item;
        })
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

  function clampSelectedIndex() {
    if (!filtered.length) {
      selectedIndex = 0;
      return;
    }
    selectedIndex = Math.max(0, Math.min(selectedIndex, filtered.length - 1));
  }

  function scrollSelectedIntoView(behavior) {
    const selected = resultsEl.querySelector(".command-palette-item.is-selected");
    if (!selected) {
      return;
    }

    selected.scrollIntoView({
      block: "center",
      inline: "nearest",
      behavior: behavior || "auto",
    });
  }

  function setSelectedIndex(nextIndex, options) {
    const opts = options || {};
    if (!filtered.length) {
      selectedIndex = 0;
      syncActiveDescendant();
      return;
    }

    selectedIndex = Math.max(0, Math.min(nextIndex, filtered.length - 1));
    const items = resultsEl.querySelectorAll(".command-palette-item[data-index]");
    items.forEach(function (el) {
      const idx = Number(el.getAttribute("data-index"));
      const active = idx === selectedIndex;
      el.classList.toggle("is-selected", active);
      el.setAttribute("aria-selected", String(active));
    });
    syncActiveDescendant();

    if (opts.scroll) {
      window.requestAnimationFrame(function () {
        scrollSelectedIntoView("auto");
      });
    }
  }

  function selectItem(item) {
    if (!item) {
      return;
    }
    executeItem(item);
  }

  function renderResults() {
    clampSelectedIndex();
    resultsEl.innerHTML = "";

    if (!filtered.length) {
      const empty = document.createElement("li");
      empty.className = "command-palette-empty";
      empty.setAttribute("role", "presentation");
      empty.textContent = "No results found";
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

      const title = document.createElement("span");
      title.className = "command-palette-item-title";
      title.textContent = item.title;

      const subtitle = document.createElement("span");
      subtitle.className = "command-palette-item-subtitle";
      subtitle.textContent = item.subtitle || item.type;

      li.appendChild(title);
      li.appendChild(subtitle);

      li.addEventListener("mouseenter", function () {
        setSelectedIndex(idx, { scroll: false });
      });

      li.addEventListener("mousedown", function (event) {
        event.preventDefault();
      });

      li.addEventListener("click", function (event) {
        event.preventDefault();
        selectItem(item);
      });

      resultsEl.appendChild(li);
    });

    syncActiveDescendant();
  }

  function openPalette() {
    previousActiveElement = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    isOpen = true;
    palette.classList.remove("is-closed");
    palette.setAttribute("aria-hidden", "false");
    input.setAttribute("aria-expanded", "true");
    input.value = "";
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
    palette.setAttribute("aria-hidden", "true");
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    document.body.style.overflow = "";

    if (previousActiveElement && typeof previousActiveElement.focus === "function") {
      previousActiveElement.focus({ preventScroll: true });
    }
    previousActiveElement = null;
  }

  function toggleTheme() {
    const storageKey = "theme-preference";
    const order = ["dark", "light", "system"];
    const current = localStorage.getItem(storageKey) || "system";
    const next = order[(order.indexOf(current) + 1) % order.length];
    localStorage.setItem(storageKey, next);
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const useDark = next === "dark" || (next === "system" && mediaQuery.matches);
    document.documentElement.classList.toggle("dark", useDark);
    document.documentElement.setAttribute("data-theme", next);
    document.querySelectorAll("[data-theme-option]").forEach(function (option) {
      const active = option.getAttribute("data-theme-option") === next;
      option.classList.toggle("theme-option-active", active);
    });
  }

  function navigateToUrl(url) {
    if (!url) {
      return;
    }

    if (url === "#toggle-theme") {
      toggleTheme();
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

    let path = url;
    if (path.charAt(0) !== "/") {
      path = "/" + path.replace(/^\/?/, "");
    }

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

    if (!item || !item.url) {
      return;
    }

    navigateToUrl(item.url);
  }

  function onInput() {
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
    } else if (event.key === "Home") {
      event.preventDefault();
      setSelectedIndex(0, { scroll: true });
    } else if (event.key === "End") {
      event.preventDefault();
      setSelectedIndex(filtered.length - 1, { scroll: true });
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (filtered[selectedIndex]) {
        selectItem(filtered[selectedIndex]);
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      closePalette();
    }
  });

  document.addEventListener("keydown", function (event) {
    const isK = event.key === "k" || event.key === "K";
    const meta =
      event.metaKey ||
      event.ctrlKey ||
      (typeof event.getModifierState === "function" && event.getModifierState("Meta")) ||
      (typeof event.getModifierState === "function" && event.getModifierState("OS"));
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
