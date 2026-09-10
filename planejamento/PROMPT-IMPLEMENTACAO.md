# Prompt de Implementação — Analisador de Commits

Copie e cole este prompt no Claude Code (ou outro agente de código)
dentro deste diretório do projeto.

---

Você vai implementar um projeto Flask completo chamado **Analisador de
Commits**. Todo o planejamento já foi feito e está documentado nos
arquivos `planejamento/00-visao-geral.md` até
`planejamento/05-riscos-limites.md`, além das instruções operacionais
em `AGENTS.md`, na raiz deste diretório.

## Antes de escrever qualquer código

1. Leia **todos** os arquivos em `planejamento/`, na ordem numérica
   (00 a 05).
2. Leia `AGENTS.md` por completo — ele define convenções, ordem de
   implementação, definição de pronto por etapa, e regras de
   segurança não-negociáveis.
3. Depois de ler tudo, faça um resumo em texto (não em código) das
   decisões principais que você entendeu, e só prossiga para
   implementação após eu confirmar que o resumo está correto.

## O que construir

Uma aplicação Flask, sem banco de dados, que:

- Recebe a URL de um repositório público do GitHub via formulário web
- Clona o repositório (raso, temporário), extrai o histórico de
  commits, e parseia as mensagens no padrão Conventional Commits
- Gera um relatório visual completo (gráficos via Plotly.js) cobrindo:
  resumo executivo, participação por autor, classificação por tipo de
  commit, linha do tempo, padrão horário/semanal (heatmap), hotspots
  de arquivos, e pontos de atenção
- Descarta todo dado temporário ao final da requisição — nada é
  persistido
- É empacotável em Docker para deploy no Google Cloud Run

A especificação completa de cada métrica, estrutura de dados,
tratamento de erros e limites está nos documentos de planejamento —
não invente comportamento que não esteja lá sem antes perguntar.

## Ordem de implementação

Siga rigorosamente a ordem definida em
`planejamento/02-pipeline-dados.md`, seção "Ordem de implementação
recomendada":

1. `models/commit.py`
2. `services/conventional_commits.py` + testes
3. `services/validators.py` + testes
4. `services/cloner.py`
5. `services/extractor.py`
6. `services/analyzer.py` + testes
7. `services/cleanup.py`
8. Orquestração em `routes/analyzer.py`
9. Templates (`index.html`, `report.html`) e integração dos gráficos
   Plotly
10. `Dockerfile` e validação de build/execução local em container

Ao final de cada item, rode os testes relevantes e me mostre o
resultado antes de seguir para o próximo item. Não implemente vários
itens de uma vez sem checkpoint.

## Regras não-negociáveis (repetidas aqui por ênfase)

- Nunca usar `shell=True` em subprocess com dados vindos do usuário
- Nunca introduzir banco de dados, ORM, sistema de autenticação, ou
  qualquer persistência entre requisições
- Sempre limitar timeout de operações de rede/subprocess
- Sempre garantir limpeza de diretórios temporários, mesmo em caminhos
  de erro (`try/finally`)
- Toda mensagem visível ao usuário final em português do Brasil
- Nunca expor stacktrace ou detalhes internos de erro na interface

## Quando parar e perguntar

Se qualquer decisão de planejamento se mostrar impraticável durante a
implementação (por exemplo: `--filter=blob:none` não fornecer dados
suficientes para `--numstat`, ou algum limite de tempo/tamanho se
mostrar inadequado na prática), **pare e explique o problema antes de
mudar de abordagem**. Pequenos ajustes de valores numéricos podem vir
acompanhados apenas de uma nota explicativa; mudanças estruturais
exigem confirmação explícita minha antes de prosseguir.

## Entregável final esperado

- Código completo e funcional seguindo a estrutura de diretórios de
  `planejamento/01-arquitetura.md`
- Suíte de testes passando
- `Dockerfile` funcional, testado localmente (`docker build` +
  `docker run` servindo a aplicação corretamente, com `git` disponível
  no container)
- Um `README.md` explicando como rodar localmente (sem Docker, com
  `venv` + `pip install -r requirements.txt` + `flask run`) e como
  buildar/rodar via Docker
- Nenhum arquivo `.env` ou segredo commitado — usar `.env.example` se
  alguma variável de ambiente for necessária (não deveria ser, dado
  que não há banco de dados nem autenticação, mas documentar se
  surgir necessidade, ex.: token opcional da API do GitHub para
  aumentar rate limit)
