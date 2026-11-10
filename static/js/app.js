(function () {
  "use strict";

  // Carregado com defer depois do bundle do Bootstrap: `bootstrap` já existe aqui,
  // ao contrário dos scripts de página, que rodam antes dos scripts deferidos.

  function initBotaoTopo() {
    const btnTopo = document.getElementById("btn-voltar-topo");
    if (!btnTopo) return;

    const alternarVisibilidade = () => {
      btnTopo.classList.toggle("visivel", window.scrollY > 300);
    };
    window.addEventListener("scroll", alternarVisibilidade, { passive: true });
    alternarVisibilidade();

    btnTopo.addEventListener("click", () => {
      const prefereReducao = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.scrollTo({ top: 0, behavior: prefereReducao ? "auto" : "smooth" });
    });
  }

  function initTooltips() {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
      bootstrap.Tooltip.getOrCreateInstance(el);
    });
  }

  // Expõe a altura real do header (muda com quebra de linha/zoom) para o
  // scroll-margin-top das seções, assim âncoras não caem embaixo da barra fixa.
  function initAlturaHeader() {
    const header = document.querySelector(".app-header");
    if (!header) return 0;
    const atualizar = () => {
      document.documentElement.style.setProperty("--altura-header", `${header.offsetHeight}px`);
    };
    atualizar();
    new ResizeObserver(atualizar).observe(header);
    return header.offsetHeight;
  }

  function initNavSecoes(alturaHeader) {
    const nav = document.getElementById("nav-secoes");
    if (!nav) return;

    bootstrap.ScrollSpy.getOrCreateInstance(document.body, {
      target: "#nav-secoes",
      rootMargin: `-${alturaHeader + 8}px 0px -55% 0px`,
    });

    document.body.addEventListener("activate.bs.scrollspy", (evento) => {
      const ativo = evento.relatedTarget;
      nav.querySelectorAll(".nav-link").forEach((link) => {
        if (link === ativo) {
          link.setAttribute("aria-current", "location");
        } else {
          link.removeAttribute("aria-current");
        }
      });
      // Em telas estreitas a lista rola na horizontal: mantém o item ativo à vista.
      // Sem "smooth": no Chromium, um scroll suave aqui cancela o scroll suave
      // da página disparado pelo clique na âncora, e ela para antes da seção.
      const esquerda = ativo.offsetLeft - nav.clientWidth / 2 + ativo.offsetWidth / 2;
      nav.scrollLeft = Math.max(0, esquerda);
    });
  }

  window.addEventListener("DOMContentLoaded", () => {
    initBotaoTopo();
    initTooltips();
    initNavSecoes(initAlturaHeader());
  });
})();
