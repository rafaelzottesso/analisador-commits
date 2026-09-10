const fonte = document.getElementById("report-data");
if (!fonte) {
  throw new Error("JSON do relatório não encontrado");
}

const dados = JSON.parse(fonte.textContent);

const CORES = {
  primaria: "#6d5ef8",
  primariaClara: "#a99cfc",
  destaque: "#0d9488",
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
};

function plotAutores() {
  const autores = [...dados.authors].reverse();
  Plotly.newPlot(
    "grafico-autores",
    [
      {
        type: "bar",
        orientation: "h",
        x: autores.map((a) => a.commit_count),
        y: autores.map((a) => a.name),
        marker: { color: CORES.primaria },
        hovertemplate: "%{y}: %{x} commits<extra></extra>",
      },
    ],
    { ...layoutBase },
    { responsive: true, displayModeBar: false }
  );
}

function plotTipos() {
  Plotly.newPlot(
    "grafico-tipos",
    [
      {
        type: "pie",
        labels: dados.commit_types.types.map((t) => t.commit_type),
        values: dados.commit_types.types.map((t) => t.count),
        hole: 0.45,
        marker: { colors: CORES.paleta },
        hovertemplate: "%{label}: %{value} (%{percent})<extra></extra>",
      },
    ],
    { ...layoutBase, margin: { t: 8, r: 8, b: 8, l: 8 } },
    { responsive: true, displayModeBar: false }
  );
}

function plotTiposPorAutor() {
  const autores = [...new Set(dados.commit_types.by_author.map((item) => item.author_name))];
  const tipos = [...new Set(dados.commit_types.by_author.map((item) => item.commit_type))];
  const traces = tipos.map((tipo) => ({
    type: "bar",
    name: tipo,
    x: autores,
    y: autores.map((nome) => {
      const item = dados.commit_types.by_author.find(
        (linha) => linha.author_name === nome && linha.commit_type === tipo
      );
      return item ? item.count : 0;
    }),
  }));
  Plotly.newPlot(
    "grafico-tipos-autor",
    traces,
    { ...layoutBase, barmode: "stack", margin: { t: 8, r: 16, b: 64, l: 48 } },
    { responsive: true, displayModeBar: false }
  );
}

function plotTimeline() {
  const pontos = dados.timeline.points;
  Plotly.newPlot(
    "grafico-timeline",
    [
      {
        type: "scatter",
        mode: "lines+markers",
        x: pontos.map((p) => p.date),
        y: pontos.map((p) => p.count),
        line: { color: CORES.primaria },
        marker: {
          size: pontos.map((p) => (p.is_outlier ? 10 : 6)),
          color: pontos.map((p) => (p.is_outlier ? CORES.alerta : CORES.primaria)),
        },
        hovertemplate: "%{x}: %{y} commits<extra></extra>",
      },
    ],
    { ...layoutBase, margin: { t: 8, r: 16, b: 48, l: 48 } },
    { responsive: true, displayModeBar: false }
  );
}

function plotHeatmap() {
  const horas = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, "0") + "h");
  Plotly.newPlot(
    "grafico-heatmap",
    [
      {
        type: "heatmap",
        z: dados.time_heatmap.matrix,
        x: horas,
        y: dados.time_heatmap.weekday_labels,
        colorscale: [
          [0, "rgba(109, 94, 248, 0.08)"],
          [1, CORES.primaria],
        ],
        hovertemplate: "%{y} %{x}: %{z} commits<extra></extra>",
      },
    ],
    { ...layoutBase, margin: { t: 8, r: 16, b: 48, l: 80 } },
    { responsive: true, displayModeBar: false }
  );
}

function plotArquivos() {
  const arquivos = [...dados.file_hotspots.top_by_commits].slice(0, 12).reverse();
  Plotly.newPlot(
    "grafico-arquivos",
    [
      {
        type: "bar",
        orientation: "h",
        x: arquivos.map((a) => a.commit_count),
        y: arquivos.map((a) => a.path),
        marker: { color: CORES.destaque },
        hovertemplate: "%{y}: %{x} commits<extra></extra>",
      },
    ],
    { ...layoutBase },
    { responsive: true, displayModeBar: false }
  );
}

function plotExtensoes() {
  Plotly.newPlot(
    "grafico-extensoes",
    [
      {
        type: "pie",
        labels: dados.file_hotspots.by_extension.map((e) => e.extension),
        values: dados.file_hotspots.by_extension.map((e) => e.total_changed),
        marker: { colors: CORES.paleta },
        hovertemplate: "%{label}: %{value} linhas<extra></extra>",
      },
    ],
    { ...layoutBase, margin: { t: 8, r: 8, b: 8, l: 8 } },
    { responsive: true, displayModeBar: false }
  );
}

plotAutores();
plotTipos();
plotTiposPorAutor();
plotTimeline();
plotHeatmap();
plotArquivos();
plotExtensoes();
