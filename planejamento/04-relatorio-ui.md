# 04 — Relatório e UI

## Página inicial (`index.html`)

- Formulário simples e único: campo de texto para URL do GitHub +
  botão "Analisar"
- Texto explicativo curto sobre o que a ferramenta faz e suas
  limitações (repositório deve ser público; repositórios muito
  grandes podem não ser suportados)
- Sem necessidade de design elaborado — funcional, limpo, claro
- Estado de carregamento: como o processamento é síncrono e pode levar
  segundos, mostrar um indicador de progresso/spinner após o submit
  (mesmo que seja só "Analisando repositório, isso pode levar até um
  minuto...")

## Página de relatório (`report.html`)

Estrutura em seções, na ordem definida em `03-analises-metricas.md`:

1. Cabeçalho: URL do repositório analisado, data/hora da análise,
   botão para analisar outro repositório
2. Resumo executivo (cards com números-chave, sem gráfico — só texto
   grande e legível)
3. Participação por autor (gráfico + tabela)
4. Classificação por tipo de commit (gráfico + tabela)
5. Linha do tempo (gráfico de série temporal)
6. Padrão horário/semanal (heatmap)
7. Arquivos e hotspots (gráfico + tabela)
8. Pontos de atenção (lista textual, estilo "alerta" visual mas neutro
   no tom)

## Biblioteca de gráficos

Usar **Plotly.js via CDN**. Justificativa: suporta heatmap nativamente
(necessário para a seção 5), gráficos interativos com hover
(importante para explorar dados por autor/tipo sem poluir a tela), e
não exige nenhuma geração de imagem no servidor (o Flask só serve
JSON, o JavaScript no browser desenha).

Alternativa aceitável: Chart.js, mas exigiria uma lib adicional
(chartjs-chart-matrix) para o heatmap — Plotly cobre tudo nativamente
com menos dependências, por isso é a escolha preferencial.

## Fluxo de renderização

O Flask, na rota `/analisar`, deve:

1. Rodar todo o pipeline (`02-pipeline-dados.md`)
2. Montar o objeto `ReportData`
3. Renderizar `report.html` passando `ReportData` serializado como
   JSON embutido no template (`{{ report_data | tojson }}` dentro de
   uma tag `<script>`), que o JavaScript da página lê para desenhar
   os gráficos Plotly

Não gerar os gráficos como imagens estáticas no servidor (evita
dependência de Kaleido/Orca e mantém a página leve e interativa).

## Tratamento de erros na UI

Qualquer falha no pipeline (URL inválida, repo não encontrado, repo
privado, timeout de clone, repo malformado) deve renderizar
`partials/error.html` com:

- Mensagem clara em português, sem jargão técnico nem stacktrace
- Sugestão de próxima ação quando aplicável (ex.: "verifique se o
  repositório é público")
- Link para tentar novamente

Nunca expor stacktrace do Python ou detalhes internos ao usuário final
— logar detalhes no servidor (stdout/stderr, capturado pelo Cloud Run
Logging), mostrar mensagem amigável na tela.

## Responsividade

A ferramenta deve funcionar em desktop (uso principal esperado: o
professor no computador), mas não precisa de otimização mobile
extensiva — usar um framework CSS leve (Bootstrap 5 via CDN, alinhado
com as convenções já usadas em outros projetos do responsável) para
responsividade básica sem esforço extra de design.
