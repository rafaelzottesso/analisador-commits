"""Script de automação para deploy do Analisador de Commits no Google Cloud Run.

Lê as configurações da seguinte ordem de prioridade:
  1. Argumentos de linha de comando (--project, --account, --region)
  2. Arquivo local '.env' (ignorado pelo git, veja '.env.example')
  3. Variáveis de ambiente (GCP_PROJECT, GCP_ACCOUNT, GCP_REGION)
  4. Configuração ativa no seu gcloud CLI local

Uso:
  python deploy.py                 # Valida testes e executa o deploy
  python deploy.py --dry-run       # Apenas exibe os comandos que seriam executados
  python deploy.py --skip-tests    # Executa o deploy sem rodar o pytest antes
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Garante suporte a UTF-8 no terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ativa cores ANSI no Windows caso suportado
if os.name == "nt":
    os.system("")

# Configurações padrão de infraestrutura
DEFAULT_SERVICE_NAME = "analisador-commits"
DEFAULT_REGION = "us-east1"  # Suporta Cloud Run Domain Mapping com menor latência para o Brasil
DEFAULT_RESOURCES = {
    "memory": "1Gi",
    "cpu": "1",
    "concurrency": "30",
    "min_instances": "0",
    "max_instances": "5",
    "timeout": "120s",
    "source": ".",
}


# Caminho do executável do gcloud (no Windows é gcloud.cmd)
GCLOUD_BIN = shutil.which("gcloud") or "gcloud"


def carregar_env_local() -> dict[str, str]:
    """Lê pares CHAVE=VALOR de um arquivo .env local, se existir."""
    env_vars: dict[str, str] = {}
    caminho_env = Path(".env")
    if not caminho_env.is_file():
        return env_vars

    try:
        with open(caminho_env, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, valor = linha.split("=", 1)
                chave = chave.strip()
                valor = valor.strip().strip("'\"")
                if chave:
                    env_vars[chave] = valor
    except Exception as exc:
        print(f"\033[93m⚠ Aviso: Não foi possível ler o arquivo .env: {exc}\033[0m")

    return env_vars


def obter_gcloud_config(chave: str) -> str | None:
    """Consulta um valor da configuração ativa do gcloud (ex.: 'account', 'project')."""
    if not shutil.which("gcloud"):
        return None
    try:
        resultado = subprocess.run(
            [GCLOUD_BIN, "config", "get-value", chave],
            capture_output=True,
            text=True,
            check=False,
        )
        if resultado.returncode == 0:
            val = resultado.stdout.strip()
            # gcloud pode retornar '(unset)' quando a chave não está definida
            if val and val != "(unset)":
                return val
    except Exception:
        pass
    return None


def _imprimir_banner(titulo: str, cor: str = "\033[94m") -> None:
    reset = "\033[0m"
    print(f"\n{cor}{'=' * 70}")
    print(f"  {titulo}")
    print(f"{'=' * 70}{reset}\n")


def verificar_pre_requisitos(skip_tests: bool = False) -> None:
    """Valida disponibilidade do gcloud e executa testes locais antes do deploy."""
    print("🔍 Verificando pré-requisitos...")

    # 1. Verifica se gcloud CLI está no PATH
    if not shutil.which("gcloud"):
        print(
            "\n\033[91m❌ Erro: 'gcloud' não encontrado no PATH do sistema.\n"
            "   Instale o Google Cloud SDK ou adicione-o às variáveis de ambiente.\033[0m"
        )
        sys.exit(1)

    # 2. Executa testes unitários para evitar deploy de código quebrado
    if not skip_tests:
        print("🧪 Executando suíte de testes (pytest)...")
        resultado = subprocess.run([sys.executable, "-m", "pytest"], check=False)
        if resultado.returncode != 0:
            print(
                "\n\033[91m❌ Testes falharam! O deploy foi cancelado para proteger a produção.\n"
                "   Corrija os erros acima ou use '--skip-tests' se tiver certeza.\033[0m"
            )
            sys.exit(1)
        print("   \033[92m✔ Todos os testes passaram com sucesso!\033[0m\n")
    else:
        print("   \033[93m⚠ Testes ignorados por solicitação (--skip-tests).\033[0m\n")


def deploy_cloudrun(
    project: str,
    account: str | None,
    region: str,
    dry_run: bool = False,
) -> None:
    """Executa as etapas de configuração e deploy no Google Cloud Run."""
    _imprimir_banner("DEPLOY — ANALISADOR DE COMMITS NO CLOUD RUN", "\033[96m")

    print(f"  📌 Projeto GCP:  \033[92m{project}\033[0m")
    if account:
        print(f"  👤 Conta:        \033[92m{account}\033[0m")
    else:
        print("  👤 Conta:        (usando a conta ativa atual no gcloud)")
    print(f"  🌍 Região:       \033[92m{region}\033[0m (com suporte a Domain Mapping)")
    print(f"  ⚙️  Serviço:      \033[92m{DEFAULT_SERVICE_NAME}\033[0m")
    print(
        f"  💻 Recursos:     {DEFAULT_RESOURCES['memory']} RAM, {DEFAULT_RESOURCES['cpu']} vCPU, concorrência {DEFAULT_RESOURCES['concurrency']}"
    )
    print(
        f"  📈 Instâncias:   min {DEFAULT_RESOURCES['min_instances']}, max {DEFAULT_RESOURCES['max_instances']}"
    )
    print()

    # Comandos gcloud (usa GCLOUD_BIN resolvido para suportar gcloud.cmd no Windows)
    cmd_account = [GCLOUD_BIN, "config", "set", "account", account] if account else None
    cmd_project = [GCLOUD_BIN, "config", "set", "project", project]
    cmd_deploy = [
        GCLOUD_BIN,
        "run",
        "deploy",
        DEFAULT_SERVICE_NAME,
        "--source",
        DEFAULT_RESOURCES["source"],
        "--project",
        project,
        "--region",
        region,
        "--allow-unauthenticated",
        "--memory",
        DEFAULT_RESOURCES["memory"],
        "--cpu",
        DEFAULT_RESOURCES["cpu"],
        "--concurrency",
        DEFAULT_RESOURCES["concurrency"],
        "--min-instances",
        DEFAULT_RESOURCES["min_instances"],
        "--max-instances",
        DEFAULT_RESOURCES["max_instances"],
        "--timeout",
        DEFAULT_RESOURCES["timeout"],
    ]

    if dry_run:
        print("\033[93mMODO DRY-RUN ATIVO: Os comandos a seguir NÃO serão executados.\033[0m\n")
        passo = 1
        if cmd_account:
            print(f"{passo}. Definir conta:")
            print(f"   gcloud config set account {account}")
            passo += 1
        print(f"\n{passo}. Definir projeto:")
        print(f"   gcloud config set project {project}")
        passo += 1
        print(f"\n{passo}. Publicar no Cloud Run:")
        # Exibe com 'gcloud' para legibilidade na tela
        cmd_exibicao = ["gcloud"] + cmd_deploy[1:]
        print("   " + " ".join(cmd_exibicao))
        print("\n\033[92m✔ Dry-run concluído com sucesso. Script pronto para execução!\033[0m")
        return

    # 1. Definir conta se fornecida
    if cmd_account:
        try:
            print(f"🔄 Definindo conta gcloud para {account}...")
            subprocess.run(cmd_account, check=True)
        except subprocess.CalledProcessError:
            print(f"\n\033[91m❌ Falha ao definir conta '{account}'.")
            print("   Se a sessão tiver expirado, execute: gcloud auth login\033[0m")
            sys.exit(1)

    # 2. Definir projeto
    try:
        print(f"🔄 Definindo projeto gcloud para {project}...")
        subprocess.run(cmd_project, check=True)
    except subprocess.CalledProcessError:
        print(f"\n\033[91m❌ Falha ao definir projeto '{project}'.")
        print("   Se a sessão tiver expirado, execute: gcloud auth login\033[0m")
        sys.exit(1)

    # 3. Executar o deploy
    try:
        print("\n🚀 Iniciando build e deploy no Google Cloud Run...")
        cmd_exibicao = ["gcloud"] + cmd_deploy[1:]
        print("   " + " ".join(cmd_exibicao) + "\n")
        subprocess.run(cmd_deploy, check=True)
        print("\n\033[92m🎉 Deploy finalizado com sucesso no Google Cloud Run!\033[0m")
        print("\n💡 Dica para mapear seu domínio próprio nesta região:")
        print(f"   gcloud beta run domain-mappings create \\")
        print(f"     --service {DEFAULT_SERVICE_NAME} \\")
        print(f"     --domain seu-dominio.com \\")
        print(f"     --region {region}")
    except subprocess.CalledProcessError:
        print("\n\033[91m❌ Ocorreu um erro durante o deploy no Cloud Run.\033[0m")
        sys.exit(1)


def main() -> None:
    env_local = carregar_env_local()

    # Resolução de valores padrão na hierarquia (.env > env vars > gcloud config ativo)
    default_project = (
        env_local.get("GCP_PROJECT")
        or os.environ.get("GCP_PROJECT")
        or obter_gcloud_config("project")
    )
    default_account = (
        env_local.get("GCP_ACCOUNT")
        or os.environ.get("GCP_ACCOUNT")
        or obter_gcloud_config("account")
    )
    default_region = (
        env_local.get("GCP_REGION")
        or os.environ.get("GCP_REGION")
        or DEFAULT_REGION
    )

    parser = argparse.ArgumentParser(
        description="Deploy do Analisador de Commits no Google Cloud Run"
    )
    parser.add_argument(
        "--project",
        default=default_project,
        help="ID do projeto no GCP (padrão: lido do .env, env var ou gcloud config)",
    )
    parser.add_argument(
        "--account",
        default=default_account,
        help="Conta Google para deploy (padrão: lido do .env, env var ou gcloud config)",
    )
    parser.add_argument(
        "--region",
        default=default_region,
        help=f"Região do Cloud Run com suporte a custom domain (padrão: {default_region})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas exibe os comandos que seriam executados, sem fazer o deploy",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Ignora a execução da suíte de testes antes do deploy",
    )

    args = parser.parse_args()

    if not args.project:
        print(
            "\n\033[91m❌ Erro: Nenhum projeto GCP foi informado.\n"
            "   Defina 'GCP_PROJECT' no seu arquivo '.env' ou passe '--project SEU_PROJETO'.\033[0m"
        )
        sys.exit(1)

    verificar_pre_requisitos(skip_tests=args.skip_tests or args.dry_run)
    deploy_cloudrun(
        project=args.project,
        account=args.account,
        region=args.region,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()