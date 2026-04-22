from aiohttp import web


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "project": "{{project_name}}"})


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", health)
    return app


def main() -> None:
    web.run_app(create_app(), port=8000)


if __name__ == "__main__":
    main()
