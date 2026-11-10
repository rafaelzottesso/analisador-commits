"""Aplicação Flask — factory sem banco nem sessões."""

from flask import Flask

from services.formatting import format_number


def create_app() -> Flask:
    app = Flask(__name__)
    app.add_template_filter(format_number, "num")

    @app.context_processor
    def inject_static_version() -> dict[str, str]:
        return {"static_version": "10"}

    from routes.analyzer import bp

    app.register_blueprint(bp)
    return app


app = create_app()

