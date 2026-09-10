# 03 — Análises e Métricas

Cada seção abaixo corresponde a um bloco do relatório final e a uma
função de agregação em `analyzer.py`. Todas operam sobre a lista de
`Commit` já enriquecida (pós Conventional Commits).

## 1. Resumo executivo

- Total de commits
- Total de autores distintos (por email, não por nome — nomes podem
  variar entre commits do mesmo autor; email é chave mais estável,
  mas documentar que autores podem ter múltiplos emails também)
- Período coberto (data do primeiro ao último commit)
- Total de linhas inseridas / removidas no período
- Taxa de aderência ao Conventional Commits (% de commits que
  casaram com o regex)
- Total de merge commits vs. commits diretos

## 2. Participação por autor

Por autor (agrupado por email, exibindo o nome mais frequente
associado a esse email):

- Número de commits
- % do total de commits
- Linhas inseridas / removidas / total modificado
- Primeiro e último commit (para ver janela de atividade de cada um)
- Tipos de commit mais usados por esse autor (para detectar
  especialização: alguém que só faz `docs`, por exemplo)

Gráfico sugerido: barras horizontais (commits por autor), ordenado
decrescente.

**Sinal de atenção a destacar no relatório**: se um autor tem menos de
X% dos commits totais (limiar configurável, ex.: 10% dividido
igualmente entre o número de autores como referência), sinalizar
visualmente como possível desequilíbrio de participação — sem
julgamento automático, só destaque visual para o professor investigar.

## 3. Classificação por tipo de commit (Conventional Commits)

- Contagem e % por tipo (`feat`, `fix`, `docs`, `refactor`, `test`,
  `chore`, `style`, `perf`, `build`, `ci`, `revert`)
- Commits não-conventional agrupados como categoria própria
  ("não padronizado")
- Distribuição de tipos por autor (tabela cruzada autor × tipo, ou
  gráfico de barras empilhadas)
- Uso de escopo (`feat(escopo): ...`) — quantos commits especificam
  escopo, quais escopos mais aparecem

Gráfico sugerido: pizza ou barras para distribuição geral de tipos;
barras empilhadas para tipo por autor.

## 4. Linha do tempo de commits

- Commits por dia (série temporal completa do período)
- Destaque visual para dias com concentração muito acima da média
  (possível sinal de "correria de última hora" antes de prazo) — usar
  um limiar estatístico simples (ex.: dias acima de 2 desvios-padrão
  da média diária), não um número mágico fixo
- Linha por autor sobreposta (opcional, para ver se a concentração é
  de todo o grupo ou de uma pessoa só)

Gráfico sugerido: linha temporal (eixo X = data, eixo Y = nº de
commits), com opção de segmentar por autor.

## 5. Padrão horário e semanal (heatmap)

- Matriz dia da semana (7) × hora do dia (24), contando commits em
  cada célula
- Revela hábitos de trabalho: tudo concentrado à noite, fim de semana,
  horário comercial, etc.
- **Cuidado com timezone**: `committed_datetime` do GitPython já vem
  com timezone do commit; decidir explicitamente se a exibição será
  no horário local do commit (como registrado) ou convertida para um
  fuso fixo (ex.: America/Sao_Paulo) — documentar a escolha no
  relatório para não gerar interpretação errada. Recomendação: manter
  o horário local do commit tal como registrado (é o que reflete o
  hábito real de quem commitou), com uma nota explicativa no relatório.

Gráfico sugerido: heatmap (Plotly tem suporte nativo).

## 6. Arquivos e hotspots

- Top N arquivos mais alterados (por número de commits que os tocam,
  não só por linhas — um arquivo tocado em muitos commits pequenos é
  diferente de um arquivo reescrito uma vez)
- Top N arquivos por linhas totais modificadas
- Distribuição por extensão/linguagem (agrupar por extensão de
  arquivo — `.py`, `.html`, `.js`, etc. — como proxy de "onde o
  esforço foi investido")
- Cruzamento arquivo × autor: quem mexeu em quê (útil para ver se há
  divisão de responsabilidade clara ou se todos mexem em tudo)

Gráfico sugerido: barras horizontais para top arquivos; pizza ou
barras para distribuição por extensão.

## 7. Sinais de qualidade indiretos (seção "Pontos de atenção")

Esta seção existe para dar ao professor pistas, não vereditos. Cada
item deve ser apresentado como observação neutra, não como acusação.

- Commits com mensagem vazia ou muito curta (< N caracteres, ex.: 10)
- Commits enormes (muitas linhas alteradas de uma vez só) — possível
  sinal de trabalho não commitado incrementalmente e depois
  "jogado" de uma vez
- Mensagens genéricas repetidas (ex.: várias mensagens idênticas tipo
  "ajustes", "fix", "wip") — comparar mensagens normalizadas
  (lowercase, sem pontuação) e contar repetições
- Concentração temporal extrema (todos os commits de um autor no
  mesmo dia, especialmente perto do prazo)
- Reverts (`cc_type == "revert"` ou merge de reversão)

## Estrutura de saída (`ReportData`)

Sugestão de shape do objeto final passado ao template (pode ser um
dataclass aninhado ou um dict — decisão do agente na implementação,
mas deve ser claramente tipado e documentado):

```python
@dataclass
class ReportData:
    summary: SummaryStats
    authors: list[AuthorStats]
    commit_types: CommitTypeStats
    timeline: TimelineData
    time_heatmap: HeatmapData
    file_hotspots: FileHotspotStats
    attention_flags: list[AttentionFlag]
    repo_url: str
    generated_at: datetime
```

Cada sub-estrutura deve conter os dados já prontos para serialização
em JSON (para alimentar os gráficos no template via
`{{ dados | tojson }}` do Jinja2), evitando lógica de formatação
dentro do template.
