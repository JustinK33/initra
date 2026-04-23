from aiohttp import web

from src.routes import register_routes


def create_app() -> web.Application:
    app = web.Application()
    register_routes(app)
    return app


def main() -> None:
    web.run_app(create_app(), port=8000)


if __name__ == "__main__":
    main()
