# Analisador de Commits

Ferramenta web para professores avaliarem o histórico de commits de
repositórios **públicos** do GitHub. Recebe uma URL, gera um relatório
visual e descarta os dados temporários — sem cadastro e sem banco de
dados.

## Requisitos

- Python 3.12+
- Git disponível no PATH

## Executar localmente

```bash
python -m venv .venv
```

No Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app run
```

No Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run
```

Abra http://127.0.0.1:5000 e cole a URL de um repositório público.

### Rodar em porta específica (ex.: 8080)

Para definir uma porta diferente da padrão (5000), utilize a flag `--port`:

```bash
flask --app app run --port 8080
```

E acesse em http://127.0.0.1:8080.

Variável opcional: copie `.env.example` para `.env` e defina
`GITHUB_TOKEN` se a cota da API pública do GitHub (checagem de tamanho)
ficar curta. A aplicação lê `GITHUB_TOKEN` do ambiente; não commite o
arquivo `.env`.

## Docker

```bash
docker build -t analisador-commits .
docker run --rm -p 8080:8080 analisador-commits
```

A aplicação fica em http://127.0.0.1:8080. O container inclui `git`.

## Testes

```bash
pytest
```

Os testes de clone/extração usam repositórios Git sintéticos locais —
não dependem de rede.

## Limites (ajustáveis em `config.py`)

- Timeout do clone: 60s
- Timeout total do pipeline: 90s
- Tamanho máximo do repositório: 200 MB
- Máximo de commits processados: 5000 (os mais recentes)

## Deploy

Pensado para o **Google Cloud Run** (container Docker, escala a zero, sem banco).
O repositório já inclui `Dockerfile`, `.dockerignore` e `.gcloudignore` prontos.

No Windows (PowerShell), utilize o script auxiliar:

```powershell
.\deploy.ps1 -ProjectId "seu-projeto-gcp"
```

Ou execute o comando diretamente via Google Cloud SDK:

```bash
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

