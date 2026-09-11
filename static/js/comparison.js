const fonte = document.getElementById("comparison-data");
if (!fonte) {
  throw new Error("JSON de comparação não encontrado");
}

const dados = JSON.parse(fonte.textContent);

const CORES = {
  primaria: "#6d5ef8",
  secundaria: "#0d9488",
  destaque: "#0d9488",
  aviso: "#f59e0b",
  alerta: "#dc3545",
  neutro: "#6b7280",
  paleta: ["#6d5ef8", "#0d9488", "#f59e0b", "#dc3545", "#0ea5e9", "#a99cfc", "#22c55e", "#ec4899"],
};

const layoutBase = {
  margin: { t: 16, r: 16, b: 48, l: 80 },
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { family: "Inter, system-ui, sans-serif", color: CORES.neutro },
  colorway: CORES.paleta,
  legend: { orientation: "h", y: -0.2 },
};

function plotComparativoAutores() {
  const container = document.getElementById("grafico-comparativo-autores");
  if (!container || !dados.authors || dados.authors.length === 0) {
    return;
  }

  const autores = [...dados.authors].reverse();

  const trace1 = {
    type: "bar",
    orientation: "h",
    name: "Fase 1",
    x: autores.map((a) => a.commits_p1),
    y: autores.map((a) => a.name),
    marker: { color: CORES.primaria },
    hovertemplate: "%{y} (F1): %{x} commits<extra></extra>",
  };

  const trace2 = {
    type: "bar",
    orientation: "h",
    name: "Fase 2",
    x: autores.map((a) => a.commits_p2),
    y: autores.map((a) => a.name),
    marker: { color: CORES.secundaria },
    hovertemplate: "%{y} (F2): %{x} commits<extra></extra>",
  };

  Plotly.newPlot(
    "grafico-comparativo-autores",
    [trace1, trace2],
    {
      ...layoutBase,
      barmode: "group",
    },
    { responsive: true, displayModeBar: false }
  );
}

function plotComparativoTipos() {
  const container = document.getElementById("grafico-comparativo-tipos");
  if (!container || !dados.types_comparison || dados.types_comparison.length === 0) {
    return;
  }

  const tipos = dados.types_comparison.slice(0, 6);

  const trace1 = {
    type: "bar",
    name: "Fase 1 (%)",
    x: tipos.map((t) => t.commit_type),
    y: tipos.map((t) => t.pct_p1),
    marker: { color: CORES.primaria },
    hovertemplate: "%{x} (F1): %{y}% (%{text} commits)<extra></extra>",
    text: tipos.map((t) => t.count_p1),
  };

  const trace2 = {
    type: "bar",
    name: "Fase 2 (%)",
    x: tipos.map((t) => t.commit_type),
    y: tipos.map((t) => t.pct_p2),
    marker: { color: CORES.secundaria },
    hovertemplate: "%{x} (F2): %{y}% (%{text} commits)<extra></extra>",
    text: tipos.map((t) => t.count_p2),
  };

  Plotly.newPlot(
    "grafico-comparativo-tipos",
    [trace1, trace2],
    {
      ...layoutBase,
      barmode: "group",
      margin: { t: 16, r: 16, b: 48, l: 40 },
    },
    { responsive: true, displayModeBar: false }
  );
}

function initBuscaAutoresComp() {
  const inputBusca = document.getElementById("busca-autor-comp");
  const tabela = document.getElementById("tabela-autores-comp-corpo");
  const contador = document.getElementById("contador-autores-comp-visiveis");
  if (!inputBusca || !tabela) return;

  inputBusca.addEventListener("input", () => {
    const termo = inputBusca.value.toLowerCase().trim();
    const linhas = tabela.querySelectorAll("tr");
    let visiveis = 0;

    linhas.forEach((linha) => {
      const texto = linha.textContent.toLowerCase();
      if (!termo || texto.includes(termo)) {
        linha.style.display = "";
        visiveis++;
      } else {
        linha.style.display = "none";
      }
    });

    if (contador) {
      contador.textContent = String(visiveis);
    }
  });
}

function initCopiarUrl() {
  const btnCopiar = document.getElementById("btn-copiar-url");
  if (!btnCopiar) return;

  btnCopiar.addEventListener("click", async () => {
    const url = btnCopiar.getAttribute("data-url");
    if (!url) return;

    try {
      await navigator.clipboard.writeText(url);
      const conteudoOriginal = btnCopiar.innerHTML;
      btnCopiar.innerHTML = `<i class="bi bi-check2 text-success"></i> Copiado!`;
      setTimeout(() => {
        btnCopiar.innerHTML = conteudoOriginal;
      }, 2000);
    } catch (err) {
      console.warn("Falha ao copiar URL:", err);
    }
  });
}

function initTooltips() {
  if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
      new bootstrap.Tooltip(el);
    });
  }
}

function initStickyNav() {
  const navBar = document.getElementById("quick-nav-bar");
  if (!navBar) return;

  const links = Array.from(navBar.querySelectorAll(".quick-nav-link"));
  const secoes = links
    .map((link) => {
      const id = link.getAttribute("href")?.replace("#", "");
      return id ? document.getElementById(id) : null;
    })
    .filter(Boolean);

  let isClickScrolling = false;
  let clickTimeout = null;

  // 1. Rola suavemente a navbar interna para centralizar o link ativo (sem mover a janela principal)
  function centralizarLinkNaNavbar(linkAtivo) {
    if (!linkAtivo) return;
    const navScrollLeft = linkAtivo.offsetLeft - (navBar.offsetWidth / 2) + (linkAtivo.offsetWidth / 2);
    navBar.scrollTo({
      left: Math.max(0, navScrollLeft),
      behavior: "smooth",
    });
  }

  // 2. Navegar para a seção SOMENTE quando o usuário clica no item da navbar
  links.forEach((link) => {
    link.addEventListener("click", (e) => {
      const targetId = link.getAttribute("href")?.replace("#", "");
      const targetSection = document.getElementById(targetId);
      if (!targetSection) return;

      e.preventDefault();

      // Atualiza o estado ativo imediatamente
      links.forEach((l) => l.classList.remove("active"));
      link.classList.add("active");
      centralizarLinkNaNavbar(link);

      // Trava temporariamente a detecção de rolagem durante a animação do clique
      isClickScrolling = true;
      if (clickTimeout) clearTimeout(clickTimeout);

      const appHeader = document.querySelector(".app-header");
      const headerHeight = appHeader ? appHeader.offsetHeight : 60;
      const navHeight = navBar.offsetHeight || 44;
      const offsetTotal = headerHeight + navHeight + 16;

      const targetPosition = targetSection.getBoundingClientRect().top + window.scrollY - offsetTotal;

      window.scrollTo({
        top: Math.max(0, targetPosition),
        behavior: "smooth",
      });

      clickTimeout = setTimeout(() => {
        isClickScrolling = false;
      }, 750);
    });
  });

  // 3. Ao rolar a página manualmente, APENAS indica qual a seção atual (NUNCA move a página!)
  const updateActiveSectionOnScroll = () => {
    // Sombra sutil de elevação quando sai do topo
    if (window.scrollY > 80) {
      navBar.classList.add("is-stuck");
    } else {
      navBar.classList.remove("is-stuck");
    }

    // Se estiver em meio à transição de clique, ignora para evitar conflitos
    if (isClickScrolling) return;

    const appHeader = document.querySelector(".app-header");
    const headerHeight = appHeader ? appHeader.offsetHeight : 60;
    const navHeight = navBar.offsetHeight || 44;
    const offset = headerHeight + navHeight + 70;

    let secaoAtualId = null;

    // Encontra a seção ativa baseada na posição do topo da tela
    for (let i = secoes.length - 1; i >= 0; i--) {
      const secao = secoes[i];
      const rect = secao.getBoundingClientRect();
      if (rect.top <= offset) {
        secaoAtualId = secao.getAttribute("id");
        break;
      }
    }

    // Fallback: se estiver antes da primeira seção, marca a primeira
    if (!secaoAtualId && secoes.length > 0 && window.scrollY < 200) {
      secaoAtualId = secoes[0].getAttribute("id");
    }

    if (secaoAtualId) {
      links.forEach((link) => {
        if (link.getAttribute("href") === `#${secaoAtualId}`) {
          if (!link.classList.contains("active")) {
            link.classList.add("active");
            centralizarLinkNaNavbar(link);
          }
        } else {
          link.classList.remove("active");
        }
      });
    }
  };

  window.addEventListener("scroll", updateActiveSectionOnScroll, { passive: true });
  updateActiveSectionOnScroll();
}

plotComparativoAutores();
plotComparativoTipos();
initBuscaAutoresComp();
initCopiarUrl();
initTooltips();
initStickyNav();



