# AGENTS.md — Diretrizes para Agentes de Código

Este repositório é mantido e desenvolvido com o auxílio de múltiplos agentes de IA e IDEs (**Cursor, Claude Code, Google Antigravity, VS Code / Copilot e Serena**).

Este documento é a **fonte única de verdade** sobre padrões de projeto, convenções arquiteturais, segurança e localização das *skills* e regras de cada ferramenta. Qualquer agente atuando no repositório deve respeitar estas orientações.

---

## 1. Índice de Ferramentas, Skills e Configurações

Cada ferramenta armazena suas habilidades e instruções em diretórios específicos. Embora cada IDE utilize seu próprio padrão de pasta, **as regras e skills aqui listadas são de observância obrigatória para todos os agentes**:

| Ferramenta | Local de Configuração / Skills | Propósito no Repositório |
| :--- | :--- | :--- |
| **Cursor** | `.cursor/skills/` | Skills sob demanda para o Cursor AI |
| **Claude Code** | `.claude/` e `CLAUDE.md` | Configurações de execução e contexto para o Claude CLI |
| **Antigravity** | `.agents/skills/` e `AGENTS.md` | Customizações locais do Google Antigravity (lê `AGENTS.md` nativamente) |
| **VS Code / Copilot** | `.vscode/` e `.github/` | Configurações de workspace e instruções para GitHub Copilot |
| **Serena** | `.serena/` | Configuração semântica do projeto (`project.yml`) e memórias persistidas |

### 🎯 Skills Disponíveis no Projeto

1. **`commit-padrao`**
   - **Localização:** `.cursor/skills/commit-padrao/SKILL.md`
   - **Quem deve seguir:** **TODOS OS AGENTES** (Cursor, Claude, Antigravity, Copilot).
   - **Regra:** Todas as mensagens de commit devem seguir o padrão Conventional Commits com:
     - **Título:** `tipo(escopo): resumo no imperativo` (máx. 72 chars, sem ponto final).
     - **Linha em branco**.
     - **Corpo obrigatório (2 a 5 linhas ou bullets):** Descrever concretamente o que mudou no código (nomeando funções, modelos, rotas e arquivos alterados). Proibido usar apenas mensagens vagas como "ajustes diversos" ou parafrasear o título.

---

## 2. Visão Geral da Arquitetura

O **Analisador de Commits** é uma ferramenta web para professores avaliarem o histórico de commits de repositórios públicos do GitHub.

- **Linguagem & Framework:** Python 3.12+ e Flask (sem Django, sem ORM, sem migrations).
- **Processamento de Dados:** pandas para agregações estatísticas de commits e autores.
- **Git:** Extração direta via `git log --numstat` em clones bare temporários.
- **Visualização:** Plotly.js / CSS customizado renderizado no browser a partir de JSON servido pelo Flask.
- **Infraestrutura:** Google Cloud Run (container Docker com `git` instalado, escala a zero).
- **Documentação histórica:** Os documentos originais de concepção e o prompt inicial estão arquivados em `planejamento/`.

### Princípio Fundamental: Stateless por Design
A aplicação **não tem banco de dados, nem sistema de autenticação, nem sessões persistidas em disco**. Cada requisição é independente:
1. Recebe a URL via formulário web (`POST /analisar`).
2. Valida a URL e checa o tamanho na API do GitHub (`services/validators.py`).
3. Clona o repositório em diretório temporário (`services/cloner.py`).
4. Extrai o histórico e métricas (`services/extractor.py` e `services/conventional_commits.py`).
5. Agrega os dados com pandas (`services/analyzer.py`).
6. **Remove os arquivos clonados obrigatoriamente** no `finally` (`services/cleanup.py`).
7. Renderiza o relatório HTML (`templates/report.html`).

---

## 3. Regras de Segurança Não-Negociáveis

1. **Nunca usar `shell=True`** em chamadas de subprocess com input do usuário.
2. **Nunca concatenar strings de input do usuário** diretamente em comandos de shell — use listas de argumentos (`subprocess.run(["git", "clone", ...])`).
3. **Limpeza garantida de temporários:** Sempre executar o cleanup de repositórios temporários dentro de blocos `try ... finally`, inclusive em casos de erro ou timeout.
4. **Timeouts estritos:** Nenhuma chamada externa (Git clone, requisição HTTP) pode rodar indefinidamente. Respeitar os limites definidos em `config.py`.
5. **Privacidade e logs:** Não logar dados sensíveis nem mensagens completas de commits nos servidores. Nunca commitar arquivos `.env`.

---

## 4. Convenções de Código

- **Estilo:** PEP 8 com tipagem estática (Type hints) em todas as funções públicas de `services/` e `models/`.
- **Modelos:** Usar `@dataclass` para estruturas de dados de domínio (`models/commit.py`). Nunca utilizar dicionários soltos como entidades internas de negócio.
- **Idiomas:**
  - **Código:** Nomes de classes, métodos, funções, arquivos e módulos em **inglês**.
  - **Documentação e Variáveis:** Comentários, docstrings e variáveis internas em **português** (alinhado aos padrões do projeto).
  - **Interface do Usuário (UI):** 100% em **português do Brasil (pt-BR)**.
- **Tratamento de Exceções:** Tratar exceções conhecidas nos serviços gerando erros amigáveis mapeados (`services/errors.py`). Nunca expor *stack traces* na interface web.

---

## 5. Comandos e Procedimentos Úteis

### Ambiente Virtual e Dependências
```powershell
# Ativação no Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Execução Local
```bash
# Execução padrão (porta 5000)
flask --app app run

# Execução em porta específica (ex.: 8080)
flask --app app run --port 8080
```

### Execução dos Testes
```bash
pytest
```
*Nota: Os testes usam fixtures locais sintéticas criadas com `git init` e não dependem de conexão de rede.*

### Deploy no Google Cloud Run
O repositório já está preparado para deploy no Cloud Run com `.gcloudignore`, `.dockerignore` e Dockerfile otimizado:
```powershell
# Via script auxiliar no Windows:
.\deploy.ps1 -ProjectId "seu-id-do-gcp"

# Ou comando direto via gcloud:
gcloud run deploy analisador-commits \
  --source . \
  --region southamerica-east1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --concurrency 30 \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 120s
```
