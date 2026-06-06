(function () {
  try {
    const storageKey = "theme-preference";
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const root = document.documentElement;

    function currentPreference() {
      const saved = localStorage.getItem(storageKey);
      if (saved === "light" || saved === "dark" || saved === "system") {
        return saved;
      }
      return "system";
    }

    function resolvedDark(theme) {
      return theme === "dark" || (theme === "system" && mediaQuery.matches);
    }

    function updateControls(theme) {
      const options = document.querySelectorAll("[data-theme-option]");
      options.forEach(function (option) {
        const isActive = option.getAttribute("data-theme-option") === theme;
        option.classList.toggle("theme-option-active", isActive);
        option.setAttribute("aria-pressed", String(isActive));
      });
    }

    function applyTheme(theme) {
      root.classList.toggle("dark", resolvedDark(theme));
      root.setAttribute("data-theme", theme);
      updateControls(theme);
    }

    function setTheme(theme) {
      localStorage.setItem(storageKey, theme);
      applyTheme(theme);
    }

    applyTheme(currentPreference());

    document.querySelectorAll("[data-theme-option]").forEach(function (option) {
      option.addEventListener("click", function () {
        setTheme(option.getAttribute("data-theme-option"));
      });
    });

    mediaQuery.addEventListener("change", function () {
      if (currentPreference() === "system") {
        applyTheme("system");
      }
    });
  } catch (error) {
    document.documentElement.classList.remove("dark");
    document.documentElement.setAttribute("data-theme", "system");
  }
})();
