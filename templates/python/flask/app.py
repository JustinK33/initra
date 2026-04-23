from flask import Flask

from src.routes import health_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(health_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
