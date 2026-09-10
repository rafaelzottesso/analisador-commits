# 02 — Pipeline de Dados

Este é o núcleo técnico do sistema. Cada etapa deve ser uma função ou
classe isolada e testável, sem efeitos colaterais escondidos.

## Etapa 1 — Validação da URL (`validators.py`)

Antes de qualquer clone:

- A URL deve corresponder ao padrão de um repositório GitHub:
  `https://github.com/<owner>/<repo>` (com ou sem `.git` no final, com
  ou sem barra final)
- Rejeitar URLs que não sejam `https://github.com/...` (não aceitar
  `git@github.com:...` na v1, para simplificar — é HTTPS público)
- Não fazer nenhuma chamada de rede nesta etapa — é validação de
  formato apenas (regex), rápida e sem custo

## Etapa 2 — Clone (`cloner.py`)

```
git clone --bare --filter=blob:none --single-branch <url> <tmp_dir>
```

Decisões:

- **`--bare`**: não precisamos do working tree, só do histórico —
  mais rápido e menor
- **`--filter=blob:none`** (partial clone): baixa apenas metadados de
  commit e árvores, não o conteúdo dos arquivos (blobs). Como a
  análise trabalha com `--numstat` (contagem de linhas), isso ainda
  funciona, porque numstat vem de diffs entre árvores, não do
  conteúdo integral do blob em todos os casos — **validar
  empiricamente na implementação**; se numstat exigir blobs em algum
  cenário, cair para clone normal sem o filter, mas manter `--bare`
  e considerar `--depth` como alternativa de redução de custo.
- **`--single-branch`**: só a branch padrão, não todas as branches —
  suficiente para o caso de uso (histórico principal do projeto)
- Diretório de destino: `tempfile.mkdtemp()` dentro de um diretório
  base configurável (ex.: `/tmp/commit_analyzer/`)
- **Timeout obrigatório** no subprocess do clone (ver
  05-riscos-limites.md para o valor) — usar `subprocess.run(..., timeout=N)`
  ou equivalente do GitPython, e tratar `TimeoutExpired` como erro de
  usuário ("repositório muito grande ou lento para clonar"), não como
  erro 500
- Verificar código de saída do clone; se falhar, mapear para mensagens
  claras: repo não existe / é privado / URL inválida / timeout

## Etapa 3 — Extração de commits (`extractor.py`)

Usar GitPython sobre o clone bare para iterar commits da branch padrão:

```python
import git
repo = git.Repo(tmp_dir)
for commit in repo.iter_commits():
    ...
```

Para cada commit, capturar:

- `hash` (sha completo e abreviado)
- `author_name`, `author_email`
- `committed_datetime` (**usar committed, não authored, como data
  primária de análise** — authored pode ser manipulada por rebase;
  documentar essa escolha no relatório se relevante)
- `message` (completa, primeira linha separada do corpo)
- `parents` (quantidade — para distinguir commit normal de merge
  commit)
- Estatísticas de arquivo: usar `commit.stats.files` do GitPython, que
  já retorna por arquivo: linhas inseridas, linhas removidas, e
  linhas totais alteradas

Montar uma lista de objetos `Commit` (dataclass definida em
`models/commit.py`, ver abaixo) — esta lista é a estrutura de dados
central que todas as etapas seguintes consomem.

### `models/commit.py` — estrutura de dados sugerida

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class FileChange:
    path: str
    insertions: int
    deletions: int

@dataclass
class Commit:
    sha: str
    sha_short: str
    author_name: str
    author_email: str
    committed_at: datetime
    message: str
    message_summary: str  # primeira linha
    is_merge: bool
    files_changed: list[FileChange] = field(default_factory=list)
    # preenchido na etapa de parsing de Conventional Commits:
    cc_type: str | None = None
    cc_scope: str | None = None
    cc_description: str | None = None
    is_conventional: bool = False
```

Manter isso como **dataclasses simples, não modelos de ORM** — reforça
a decisão de não ter banco de dados e mantém a estrutura serializável
para JSON sem fricção.

## Etapa 4 — Parsing de Conventional Commits (`conventional_commits.py`)

Regex de referência (ajustar conforme a especificação real usada pelos
alunos — o responsável mencionou que usam uma "skill" para padronizar,
então vale confirmar o formato exato antes de finalizar o regex):

```python
import re

CONVENTIONAL_COMMIT_RE = re.compile(
    r'^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)'
    r'(\((?P<scope>[\w\-\/]+)\))?'
    r'(?P<breaking>!)?'
    r':\s(?P<description>.+)$'
)

def parse_conventional_commit(message_summary: str) -> dict:
    match = CONVENTIONAL_COMMIT_RE.match(message_summary.strip())
    if not match:
        return {"is_conventional": False, "cc_type": None,
                "cc_scope": None, "cc_description": None}
    return {
        "is_conventional": True,
        "cc_type": match.group("type"),
        "cc_scope": match.group("scope"),
        "cc_description": match.group("description"),
    }
```

Esta função deve ser pura (sem I/O) e ter cobertura de testes unitários
extensa (ver `tests/test_conventional_commits.py`) cobrindo: casos
válidos de cada tipo, com e sem escopo, com breaking change (`!`),
mensagens que não seguem o padrão, mensagens vazias, mensagens com
`:` no meio da descrição (não deve confundir o parser).

## Etapa 5 — Agregação e análise (`analyzer.py`)

Recebe a lista de `Commit` já enriquecida com dados de Conventional
Commits e produz um objeto `ReportData` (ver `03-analises-metricas.md`
para a definição completa de cada métrica). Esta etapa usa pandas
internamente (converter a lista de dataclasses em DataFrame facilita
`groupby`, `resample`, etc.), mas a interface de saída deve ser uma
estrutura serializável (dict / dataclass), não um DataFrame exposto
para fora desta camada.

## Etapa 6 — Limpeza (`cleanup.py`)

```python
import shutil

def cleanup_repo(tmp_dir: str) -> None:
    shutil.rmtree(tmp_dir, ignore_errors=True)
```

Deve ser chamado em bloco `finally` na view que orquestra o pipeline,
garantindo remoção mesmo se qualquer etapa anterior lançar exceção.

## Ordem de implementação recomendada

1. `models/commit.py` (estruturas de dados, sem lógica)
2. `services/conventional_commits.py` + testes (é puro, fácil de testar
   isoladamente, sem precisar de repositório real)
3. `services/validators.py` + testes
4. `services/cloner.py` (testar contra um repositório pequeno público
   real ou um repositório git local criado nos testes)
5. `services/extractor.py` (depende de cloner funcionando)
6. `services/analyzer.py` + testes (usar fixtures de commits sintéticos,
   não depende de clone real para os testes de agregação)
7. `services/cleanup.py`
8. Orquestração na view (`routes/analyzer.py`)
9. Templates e gráficos
