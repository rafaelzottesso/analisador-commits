const fonte = document.getElementById("report-data");
if (!fonte) {
  throw new Error("JSON do relatório não encontrado");
}

const dados = JSON.parse(fonte.textContent);
const layoutBase = {
  margin: { t: 32, r: 16, b: 48, l: 80 },
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { family: "system-ui, sans-serif" },
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
        marker: { color: "#0d6efd" },
        hovertemplate: "%{y}: %{x} commits<extra></extra>",
      },
    ],
    { ...layoutBase, title: "Commits por autor" },
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
        hole: 0.35,
        hovertemplate: "%{label}: %{value} (%{percent})<extra></extra>",
      },
    ],
    { ...layoutBase, margin: { t: 32, r: 16, b: 16, l: 16 }, title: "Tipos de commit" },
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
    { ...layoutBase, barmode: "stack", title: "Tipo por autor", margin: { t: 32, r: 16, b: 64, l: 48 } },
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
        line: { color: "#0d6efd" },
        marker: {
          size: pontos.map((p) => (p.is_outlier ? 10 : 6)),
          color: pontos.map((p) => (p.is_outlier ? "#dc3545" : "#0d6efd")),
        },
        hovertemplate: "%{x}: %{y} commits<extra></extra>",
      },
    ],
    { ...layoutBase, title: "Commits por dia", margin: { t: 32, r: 16, b: 48, l: 48 } },
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
        colorscale: "Blues",
        hovertemplate: "%{y} %{x}: %{z} commits<extra></extra>",
      },
    ],
    { ...layoutBase, title: "Heatmap dia × hora", margin: { t: 32, r: 16, b: 48, l: 80 } },
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
        marker: { color: "#198754" },
        hovertemplate: "%{y}: %{x} commits<extra></extra>",
      },
    ],
    { ...layoutBase, title: "Arquivos mais tocados" },
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
        hovertemplate: "%{label}: %{value} linhas<extra></extra>",
      },
    ],
    { ...layoutBase, margin: { t: 32, r: 16, b: 16, l: 16 }, title: "Esforço por extensão" },
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
