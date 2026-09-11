"""Aplicação Flask — factory sem banco nem sessões."""

from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    @app.context_processor
    def inject_static_version() -> dict[str, str]:
        return {"static_version": "5"}

    from routes.analyzer import bp

    app.register_blueprint(bp)
    return app


app = create_app()

