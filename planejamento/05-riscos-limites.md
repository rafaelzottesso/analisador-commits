# 05 — Riscos e Limites

## Limites obrigatórios (proteção contra abuso e travamento)

| Limite | Valor sugerido | Ajustável via |
|---|---|---|
| Timeout do clone | 60 segundos | `config.py` |
| Timeout total do pipeline (clone + extração + análise) | 90 segundos | `config.py` |
| Tamanho máximo do repositório antes de clonar | Verificar via API pública do GitHub (`GET /repos/{owner}/{repo}`, campo `size`) antes de clonar; recusar acima de um limite (ex.: 200 MB) com mensagem clara | `config.py` |
| Número máximo de commits processados | Ex.: 5000 — acima disso, processar só os N mais recentes e avisar no relatório que a análise foi limitada | `config.py` |

A checagem de tamanho via API do GitHub **antes** do clone é
importante: evita clonar um repositório enorme só para descobrir
depois que é grande demais. Isso é uma chamada leve à API pública
(sem autenticação, mas sujeita a rate limit de ~60 req/hora por IP —
aceitável para o volume de uso esperado; se isso se tornar um
problema, considerar token de API do GitHub configurado como variável
de ambiente para aumentar o limite).

## Tratamento de erros — mapeamento completo

| Situação | Causa técnica | Mensagem ao usuário |
|---|---|---|
| URL não é do GitHub | Falha na regex de `validators.py` | "Por enquanto, só repositórios do GitHub são suportados." |
| URL malformada | Falha na regex | "URL inválida. Use o formato https://github.com/usuario/repositorio" |
| Repositório não existe ou é privado | Clone retorna erro de autenticação/404 | "Não foi possível acessar este repositório. Verifique se a URL está correta e se o repositório é público." |
| Repositório maior que o limite | Checagem via API antes do clone | "Este repositório é muito grande para ser analisado (limite atual: X MB)." |
| Timeout no clone | `subprocess.TimeoutExpired` | "O repositório demorou muito para ser clonado. Tente novamente ou use um repositório menor." |
| Repositório sem nenhum commit | Lista de commits vazia após extração | "Este repositório não possui histórico de commits para analisar." |
| Erro inesperado em qualquer etapa | Exceção não prevista | "Ocorreu um erro inesperado ao analisar o repositório. Tente novamente." (logar detalhes completos no servidor) |

## Concorrência e isolamento

- Cada requisição usa seu próprio diretório temporário com nome único
  (`uuid4()`), nunca reutilizar diretórios entre requisições
  simultâneas
- Se duas pessoas analisarem o mesmo repositório ao mesmo tempo, cada
  uma faz seu próprio clone independente — não há cache compartilhado
  na v1 (poderia ser uma otimização futura, mas adiciona
  complexidade de invalidação que não vale a pena agora)
- `cleanup.py` deve rodar em `finally`, garantindo que nenhum
  diretório temporário sobreviva à requisição, mesmo sob erro

## Segurança

- **Nunca** interpolar a URL fornecida pelo usuário diretamente em uma
  string de shell (`shell=True`) — sempre passar como lista de
  argumentos para `subprocess.run` (`subprocess.run(["git", "clone",
  ..., url, tmp_dir])`), evitando injeção de comando
- Validar que a URL, mesmo após passar na regex, resolve para o
  domínio `github.com` real antes de usar (evitar truques de URL que
  pareçam GitHub mas redirecionem para outro host)
- Limitar quem pode acessar o `/tmp` do container — natural no
  Cloud Run, que isola cada instância, mas não assumir isso sem
  confirmar nas configurações de deploy
- Não logar conteúdo completo de mensagens de commit em logs públicos
  se o Cloud Run Logging for compartilhado com outras pessoas —
  logar apenas metadados de erro, não dados do repositório analisado

## Escalabilidade e custo

- Cloud Run escalando a zero é o comportamento correto para o padrão
  de uso esperado (esporádico, não contínuo) — evita custo quando
  ninguém está usando
- Se o uso crescer (ex.: toda uma turma analisando ao mesmo tempo no
  fim do semestre), Cloud Run escala horizontalmente por padrão — cada
  instância processa uma requisição de cada vez, sem necessidade de
  configuração adicional para este cenário simples
- Monitorar tempo de resposta na prática após deploy; se timeouts
  forem frequentes, é o sinal de que vale migrar para processamento
  assíncrono (mencionado como não-escopo da v1, mas arquiteturalmente
  possível de adicionar depois sem reescrever o pipeline — só mudar a
  camada de orquestração)

## O que fica deliberadamente frágil na v1 (aceitar o risco)

- Sem cache entre análises do mesmo repositório
- Sem processamento assíncrono / fila
- Sem suporte a múltiplas branches (só a branch padrão)
- Sem suporte a repositórios privados
- Sem retry automático em caso de falha de rede no clone
