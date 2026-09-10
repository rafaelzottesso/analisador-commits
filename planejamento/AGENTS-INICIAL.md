# AGENTS.md — Instruções para Agentes de Código

Este arquivo orienta qualquer agente de IA (Claude Code, Copilot CLI,
etc.) trabalhando neste repositório. Leia também todos os documentos
em `planejamento/` antes de escrever qualquer código — eles contêm as
decisões de arquitetura e as definições de cada métrica que o código
deve implementar.

## Ordem de trabalho obrigatória

1. Leia `planejamento/00-visao-geral.md` até `planejamento/05-riscos-limites.md`
   nessa ordem, por completo, antes de escrever qualquer arquivo de
   código.
2. Implemente na ordem sugerida em `planejamento/02-pipeline-dados.md`,
   seção "Ordem de implementação recomendada".
3. Não pule direto para a interface (templates/rotas) antes dos
   services e models estarem prontos e testados.
4. Ao final de cada módulo implementado, rode os testes
   correspondentes antes de seguir para o próximo.

## Convenções de código

- Python 3.12+, seguir PEP 8
- Type hints em todas as funções públicas de `services/` e `models/`
- Dataclasses para estruturas de dados, nunca dicionários soltos como
  "modelo" de domínio (dicionários são aceitáveis só como formato de
  serialização final para JSON/template)
- Docstrings curtas em funções não-triviais explicando o "porquê", não
  o "o quê" (o código já diz o que faz)
- Nomes de variáveis e comentários em português, alinhado com o resto
  dos projetos do responsável — mas nomes de funções/classes/módulos
  em inglês (convenção Python padrão), como já é praticado nos outros
  projetos Django do responsável
- Nenhuma dependência de banco de dados, ORM, ou sistema de
  autenticação deve ser introduzida — se sentir necessidade de uma
  dessas coisas, pare e sinalize explicitamente em vez de adicionar
  silenciosamente

## Testes

- Cada `service` deve ter teste unitário correspondente em `tests/`
- `conventional_commits.py` e `analyzer.py` devem ter cobertura ampla
  de casos de borda (ver exemplos em `02-pipeline-dados.md` e
  `03-analises-metricas.md`)
- Para testar `cloner.py` e `extractor.py`, criar fixtures de
  repositórios Git locais reais dentro de `tests/fixtures/` (via
  `git init` programático em setup de teste, com commits sintéticos
  cobrindo: commits Conventional e não-Conventional, merge commits,
  múltiplos autores, arquivos de diferentes extensões) — não depender
  de repositórios remotos reais nos testes automatizados, para não
  tornar a suíte de testes dependente de rede
- Não é necessário 100% de cobertura, mas a lógica de parsing e
  agregação (o "coração" do sistema) deve estar bem coberta

## Definição de pronto (Definition of Done) por etapa

- **Models**: dataclasses criadas, com type hints completos, sem
  lógica de negócio dentro delas
- **Services individuais**: função implementada + testes unitários
  passando + tratamento explícito de erros esperados (não deixar
  exceções não tratadas vazarem para fora do service)
- **Pipeline completo**: rota `/analisar` orquestra todas as etapas,
  com `try/finally` garantindo cleanup, e todos os cenários de erro de
  `05-riscos-limites.md` mapeados para mensagens amigáveis
- **UI**: relatório renderiza todas as seções de
  `03-analises-metricas.md`, gráficos funcionam com dados reais de
  pelo menos 2 repositórios de teste diferentes (um pequeno, um médio)
- **Deploy**: Dockerfile builda localmente, container roda localmente
  servindo a aplicação corretamente, `git` disponível dentro do
  container

## O que fazer se uma decisão do planejamento parecer errada na prática

Os documentos em `planejamento/` refletem decisões tomadas com base em
raciocínio, não testadas ainda em código real. Se durante a
implementação algo se mostrar impraticável (ex.: `--filter=blob:none`
não fornece dados suficientes para numstat, ou algum limite de tempo
se mostra baixo demais), **não decida sozinho e siga em frente
silenciosamente** — pare, explique o problema encontrado e a alternativa
proposta, e só prossiga após confirmação. Pequenos ajustes de valores
(ex.: timeout de 60s para 45s) podem ser feitos com uma nota explicativa,
mas mudanças de abordagem (ex.: trocar biblioteca de gráficos, adicionar
banco de dados) exigem confirmação explícita antes de implementar.

## Segurança — não negociável

- Nunca usar `shell=True` em chamadas de subprocess com input do
  usuário
- Nunca interpolar strings de input do usuário diretamente em comandos
  shell
- Sempre validar a URL antes de qualquer clone
- Sempre limitar timeout de qualquer operação de rede/subprocess

## Idioma

Toda a interface do usuário (templates, mensagens de erro, labels de
gráficos) deve estar em português do Brasil. Código, nomes de
variáveis internas e comentários técnicos seguem a convenção descrita
acima.
