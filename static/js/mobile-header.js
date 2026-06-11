/**
 * Mobile header compact animation driven by scroll position.
 * @param {number} scrollY
 * @returns {number} progress 0–1
 */
function mobileHeaderProgress(scrollY) {
  return Math.min(1, Math.max(0, (scrollY - 20) / 80));
}

(function () {
  const header = document.querySelector(".docs-mobile-header");
  if (!header) {
    return;
  }

  const mq = window.matchMedia("(max-width: 1023px)");
  let ticking = false;

  function applyProgress(progress) {
    header.style.setProperty("--header-compact", String(progress));
    const compact = progress > 0.85;
    header.classList.toggle("is-compact", compact);
    header.querySelectorAll(".docs-mobile-label-short").forEach(function (node) {
      node.setAttribute("aria-hidden", compact ? "false" : "true");
    });
    header.querySelectorAll(".docs-mobile-label-full").forEach(function (node) {
      node.setAttribute("aria-hidden", compact ? "true" : "false");
    });
  }

  function update() {
    if (!mq.matches) {
      applyProgress(0);
      return;
    }
    applyProgress(mobileHeaderProgress(window.scrollY || document.documentElement.scrollTop || 0));
  }

  function onScroll() {
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(function () {
        update();
        ticking = false;
      });
    }
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  mq.addEventListener("change", update);
  update();
})();
