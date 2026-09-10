"""Script de inicialização simplificada da aplicação Flask."""

from __future__ import annotations

import os
import sys

from app import app

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8080))
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        porta = int(sys.argv[1])

    host = os.environ.get("HOST", "127.0.0.1")
    debug = os.environ.get("FLASK_DEBUG", "0") in ("1", "true", "True")

    print(f" * Servidor do Analisador de Commits iniciando em http://{host}:{porta}")
    app.run(host=host, port=porta, debug=debug)
