# 01 — Arquitetura

## Stack

- **Linguagem**: Python 3.12+
- **Framework web**: Flask (não Django — ver justificativa abaixo)
- **Servidor WSGI de produção**: Gunicorn
- **Deploy**: Google Cloud Run (container Docker)
- **Análise de dados**: pandas
- **Manipulação de Git**: GitPython (sobre subprocess de `git`, não
  reimplementar parsing de git log na mão)
- **Gráficos**: Plotly.js ou Chart.js via CDN, renderizado no template HTML
  (sem gerar imagens no servidor — o JS no browser desenha os gráficos a
  partir de JSON servido pelo Flask)
- **Templates**: Jinja2 (nativo do Flask)
- **Sem banco de dados relacional.** Sem ORM. Sem migrations.

## Por que Flask em vez de Django

Decisão tomada deliberadamente após comparação. Motivo central: a
aplicação é **stateless por design** (confirmado como requisito
permanente, não uma limitação temporária) — não há contas de usuário,
não há dados a persistir entre requisições, não há necessidade de
admin, auth, ORM ou migrations. Django assume essas peças por padrão e
exigiria desligá-las uma a uma (sessions em cache em vez de DB, remover
`django.contrib.admin`, remover `django.contrib.auth` se não usado,
configurar `DATABASES = {}`). Flask não carrega essa bagagem: a
estrutura do framework já corresponde ao formato real da aplicação
("recebe request → processa → renderiza → esquece"), com menos
configuração negativa.

Django seria a escolha certa se a ferramenta fosse crescer para ter
contas de professor, histórico de turmas ou comparações ao longo do
tempo — mas isso foi explicitamente descartado como direção futura.

## Por que não PHP

A hospedagem PHP existente do responsável é compartilhada e **não
permite `shell_exec`/`exec`**, o que inviabiliza rodar `git clone` ou
qualquer comando de git — que é o núcleo técnico desta ferramenta. Uma
alternativa via API REST do GitHub perderia acesso a dados de baixo
nível (`--numstat`, diffs por arquivo) e ficaria sujeita a rate limits
da API pública. PHP não é adequado para este problema específico.

## Estrutura de diretórios do projeto

```
commit_analyzer/
├── app.py                      # cria app Flask, registra blueprint(s)
├── config.py                   # limites, timeouts, configs de ambiente
├── routes/
│   ├── __init__.py
│   └── analyzer.py             # GET / (form) ; POST /analisar (pipeline)
├── services/
│   ├── __init__.py
│   ├── cloner.py                # clone raso em diretório temporário
│   ├── extractor.py             # git log → lista de Commit (dataclass)
│   ├── conventional_commits.py  # parser de mensagens (regex)
│   ├── analyzer.py              # agregações pandas → estrutura de relatório
│   ├── validators.py            # valida URL do GitHub, tamanho do repo
│   └── cleanup.py               # remoção garantida do clone temporário
├── models/
│   ├── __init__.py
│   └── commit.py                 # dataclasses: Commit, FileChange, ReportData
├── templates/
│   ├── base.html
│   ├── index.html                # formulário
│   ├── report.html                # relatório completo
│   └── partials/
│       └── error.html
├── static/
│   ├── css/
│   └── js/
├── tests/
│   ├── test_cloner.py
│   ├── test_extractor.py
│   ├── test_conventional_commits.py
│   ├── test_analyzer.py
│   └── fixtures/                  # repositórios de teste pequenos, gerados
│                                    # localmente com git init + commits
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
└── README.md
```

## Fluxo de dados (alto nível)

```
Usuário cola URL no form (GET /)
        ↓ POST /analisar
validators.py → valida formato da URL, se é GitHub, se responde
        ↓
cloner.py → git clone --bare --filter=blob:none --depth <N ou completo>
            para /tmp/<uuid>/, com timeout
        ↓
extractor.py → percorre o clone com GitPython, monta lista de
               objetos Commit (dataclass) com metadados + numstat
        ↓
conventional_commits.py → para cada Commit, parseia commit.message
                            em (type, scope, description, is_conventional)
        ↓
analyzer.py → recebe lista de Commit já enriquecida, usa pandas para
              gerar todas as agregações definidas em 03-analises-metricas.md
              → retorna um único objeto/dict ReportData serializável
        ↓
cleanup.py → remove /tmp/<uuid>/ (try/finally, executa mesmo se algo
             falhar no meio do caminho)
        ↓
routes/analyzer.py → renderiza report.html passando ReportData
                      (convertido para JSON onde os gráficos precisam)
```

Importante: **cleanup.py deve rodar sempre**, inclusive em caminhos de
erro (repo não existe, timeout, repo malformado). Nunca deixar
diretórios temporários órfãos em `/tmp`.

## Deploy no Cloud Run

- Aplicação empacotada em container Docker (ver Dockerfile no repo)
- Cloud Run escala a zero quando ocioso — adequado para uso esporádico
- **Atenção ao timeout de requisição do Cloud Run**: o timeout máximo
  configurável deve ser ajustado (Cloud Run permite até 60 min, mas o
  padrão é 5 min) para acomodar clones de repositórios maiores. Mesmo
  assim, a aplicação deve ter seu próprio timeout interno mais curto
  (ver 05-riscos-limites.md) para nunca depender do limite da
  plataforma como única proteção.
- `git` precisa estar instalado na imagem base do container (usar uma
  imagem base Python que permita `apt-get install git`, ou uma imagem
  que já inclua git)
- Sem necessidade de Cloud SQL, sem necessidade de volumes persistentes
  — `/tmp` do próprio container é suficiente e é automaticamente limpo
  entre instâncias

## O que este documento não decide (decisão do responsável, não do agente)

- Domínio/subdomínio final onde a ferramenta será publicada
- Se haverá alguma proteção de acesso (ex.: senha simples) para evitar
  uso por estranhos — a v1 assume acesso público sem restrição, mas
  isso é uma decisão de produto que pode mudar
