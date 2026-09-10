# 00 — Visão Geral

## Problema

Professores de programação (contexto: disciplinas de Engenharia de Software,
Programação Orientada a Objetos, Programação Web) precisam avaliar o
trabalho de alunos em projetos versionados com Git, mas a análise manual de
histórico de commits é lenta, pouco sistemática e não escala para várias
equipes por turma.

## Objetivo

Construir uma ferramenta web pública, sem cadastro e sem persistência de
dados, que recebe a URL de um repositório público do GitHub e gera um
relatório visual (gráficos + tabelas) sobre o histórico de commits daquele
repositório: frequência, participação por autor, classificação por tipo de
commit (Conventional Commits), padrões temporais de trabalho e arquivos mais
alterados.

## Público-alvo

Professores avaliando projetos de alunos. Não é uma ferramenta de uso
corporativo/empresarial — não precisa lidar com múltiplos times, permissões,
ou repositórios privados.

## Escopo da v1

- Input: uma URL de repositório público do GitHub, via formulário web
- Processamento: clone raso, extração de commits, parsing de mensagens no
  padrão Conventional Commits, agregações estatísticas
- Output: página HTML única com relatório visual (gráficos interativos)
- Sem login, sem banco de dados, sem persistência entre requisições
- Processamento síncrono (usuário espera na mesma requisição) com timeout e
  limite de tamanho de repositório definidos explicitamente

## Fora de escopo da v1 (não implementar, mas não impedir arquiteturalmente)

- Repositórios privados / autenticação OAuth
- Múltiplos hosts de Git além do GitHub (GitLab, Bitbucket, self-hosted)
- Histórico de análises, contas de usuário, comparação entre turmas ao longo
  do tempo
- Exportação em PDF/CSV (pode vir depois, mas não é requisito agora)
- Processamento assíncrono com fila (Celery/RQ) — só considerar se o modelo
  síncrono se mostrar insuficiente na prática

## Por que sem banco de dados

Decisão deliberada do responsável pelo projeto: a ferramenta deve ser uma
"calculadora" de relatórios — recebe input, processa, exibe, descarta.
Isso simplifica deploy (sem Cloud SQL, sem migrations, sem gestão de
schema) e evita qualquer questão de retenção de dados de terceiros
(repositórios de alunos não devem ficar armazenados em lugar nenhum além do
disco temporário da própria requisição).

## Critério de sucesso da v1

Um professor consegue colar a URL de um repositório de um grupo de alunos
(tipicamente dezenas a poucas centenas de commits, poucos colaboradores) e
em até ~30 segundos ver um relatório completo, correto e visualmente claro,
sem precisar entender nada de Git internals para interpretar os dados.
