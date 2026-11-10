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
    if (!header) return;
    const atualizar = () => {
      document.documentElement.style.setProperty("--altura-header", `${header.offsetHeight}px`);
    };
    atualizar();
    new ResizeObserver(atualizar).observe(header);
  }

  function initNavSecoes() {
    const nav = document.getElementById("nav-secoes");
    if (!nav) return;

    const links = Array.from(nav.querySelectorAll(".nav-link"));
    const secoes = links.map((link) => document.querySelector(link.getAttribute("href")));
    const header = document.querySelector(".app-header");
    let ativoAtual = null;

    const marcarAtivo = (ativo) => {
      if (ativo === ativoAtual) return;
      ativoAtual = ativo;
      links.forEach((link) => {
        link.classList.toggle("active", link === ativo);
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
    };

    // Ativa a última seção cujo topo já passou logo abaixo do header. No fim da
    // página vale a última seção, que é curta e nunca chega ao topo da tela.
    const atualizar = () => {
      const noFim =
        window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2;
      if (noFim) {
        marcarAtivo(links[links.length - 1]);
        return;
      }
      const linhaDeCorte = header.offsetHeight + 24;
      let indice = 0;
      secoes.forEach((secao, i) => {
        if (secao && secao.getBoundingClientRect().top <= linhaDeCorte) indice = i;
      });
      marcarAtivo(links[indice]);
    };

    let agendado = false;
    window.addEventListener(
      "scroll",
      () => {
        if (agendado) return;
        agendado = true;
        requestAnimationFrame(() => {
          agendado = false;
          atualizar();
        });
      },
      { passive: true }
    );
    atualizar();
  }

  window.addEventListener("DOMContentLoaded", () => {
    initBotaoTopo();
    initTooltips();
    initAlturaHeader();
    initNavSecoes();
  });
})();
