"""Aplicação Flask — factory sem banco nem sessões."""

from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)
    from routes.analyzer import bp

    app.register_blueprint(bp)
    return app


app = create_app()
