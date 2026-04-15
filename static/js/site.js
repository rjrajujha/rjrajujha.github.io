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
  if (!revealItems.length) {
    return;
  }

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

  revealItems.forEach(function (item) {
    observer.observe(item);
  });
})();
