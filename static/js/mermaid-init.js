(function () {
  function initMermaid() {
    if (!window.mermaid) {
      return;
    }

    const isDark = document.documentElement.classList.contains("dark");
    window.mermaid.initialize({
      startOnLoad: false,
      theme: isDark ? "dark" : "neutral",
      securityLevel: "strict",
      fontFamily: "Inter, system-ui, sans-serif",
    });

    const nodes = document.querySelectorAll("pre.mermaid");
    if (!nodes.length) {
      return;
    }

    window.mermaid.run({ nodes: nodes }).catch(function () {
      return;
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initMermaid);
  } else {
    initMermaid();
  }
})();
