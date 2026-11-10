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
  separators: ",.",
  // Getters: cada `{ ...layoutBase }` recebe eixos novos. O Plotly grava o `type`
  // detectado no objeto de layout recebido; um eixo compartilhado vazaria entre gráficos.
  get xaxis() {
    return { separatethousands: true };
  },
  get yaxis() {
    return { separatethousands: true };
  },
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
    hovertemplate: "%{y} (F1): %{x:,} commits<extra></extra>",
  };

  const trace2 = {
    type: "bar",
    orientation: "h",
    name: "Fase 2",
    x: autores.map((a) => a.commits_p2),
    y: autores.map((a) => a.name),
    marker: { color: CORES.secundaria },
    hovertemplate: "%{y} (F2): %{x:,} commits<extra></extra>",
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
    hovertemplate: "%{x} (F1): %{y:,.1f}% (%{text} commits)<extra></extra>",
    text: tipos.map((t) => t.count_p1),
  };

  const trace2 = {
    type: "bar",
    name: "Fase 2 (%)",
    x: tipos.map((t) => t.commit_type),
    y: tipos.map((t) => t.pct_p2),
    marker: { color: CORES.secundaria },
    hovertemplate: "%{x} (F2): %{y:,.1f}% (%{text} commits)<extra></extra>",
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
      contador.textContent = visiveis.toLocaleString("pt-BR");
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

plotComparativoAutores();
plotComparativoTipos();
initBuscaAutoresComp();
initCopiarUrl();
