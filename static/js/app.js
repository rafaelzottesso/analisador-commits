(function () {
  "use strict";

  window.addEventListener("DOMContentLoaded", () => {
    const btnTopo = document.getElementById("btn-voltar-topo");
    if (!btnTopo) {
      return;
    }

    const alternarVisibilidade = () => {
      if (window.scrollY > 300) {
        btnTopo.classList.add("visivel");
      } else {
        btnTopo.classList.remove("visivel");
      }
    };

    window.addEventListener("scroll", alternarVisibilidade, { passive: true });
    alternarVisibilidade();

    btnTopo.addEventListener("click", () => {
      const prefereReducao = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.scrollTo({
        top: 0,
        behavior: prefereReducao ? "auto" : "smooth",
      });
    });
  });
})();
