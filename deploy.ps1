# Script auxiliar para deploy no Google Cloud Run
# Uso:
#   .\deploy.ps1
#   Ou especificando o projeto:
#   .\deploy.ps1 -ProjectId "seu-id-do-gcp"

param (
    [Parameter(Mandatory=$false)]
    [string]$ProjectId,

    [Parameter(Mandatory=$false)]
    [string]$Region = "southamerica-east1"
)

if ($ProjectId) {
    Write-Host "Definindo projeto GCP: $ProjectId" -ForegroundColor Cyan
    gcloud config set project $ProjectId
}

Write-Host "Iniciando deploy no Cloud Run (Regiao: $Region, Concorrencia: 30)..." -ForegroundColor Green

gcloud run deploy analisador-commits `
  --source . `
  --region $Region `
  --allow-unauthenticated `
  --memory 1Gi `
  --cpu 1 `
  --concurrency 30 `
  --min-instances 0 `
  --max-instances 5 `
  --timeout 120s
