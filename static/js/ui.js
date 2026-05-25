(function () {
  const sidebar = document.querySelector(".js-sidebar");
  const backdrop = document.querySelector(".js-sidebar-backdrop");

  function openSidebar() {
    sidebar?.classList.add("is-open");
    backdrop?.classList.add("is-visible");
  }

  function closeSidebar() {
    sidebar?.classList.remove("is-open");
    backdrop?.classList.remove("is-visible");
  }

  document.querySelectorAll(".js-sidebar-open").forEach((button) => {
    button.addEventListener("click", openSidebar);
  });

  document.querySelectorAll(".js-sidebar-close").forEach((button) => {
    button.addEventListener("click", closeSidebar);
  });

  backdrop?.addEventListener("click", closeSidebar);
})();
