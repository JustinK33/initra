from aiohttp import web

from src.config import settings
from src.db import users


next_id = 1


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "project": "{{project_name}}", "env": settings.env})


async def list_users(request: web.Request) -> web.Response:
    return web.json_response({"users": users})


async def get_user(request: web.Request) -> web.Response:
    user_id = int(request.match_info["user_id"])
    for user in users:
        if user["id"] == user_id:
            return web.json_response(user)
    return web.json_response({"error": "User not found"}, status=404)


async def create_user(request: web.Request) -> web.Response:
    global next_id
    payload = await request.json()
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    if len(name) < 2 or "@" not in email:
        return web.json_response({"error": "Invalid name or email"}, status=400)

    user = {"id": next_id, "name": name, "email": email.lower()}
    next_id += 1
    users.append(user)
    return web.json_response(user, status=201)


async def update_user(request: web.Request) -> web.Response:
    user_id = int(request.match_info["user_id"])
    payload = await request.json()
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    if len(name) < 2 or "@" not in email:
        return web.json_response({"error": "Invalid name or email"}, status=400)

    for user in users:
        if user["id"] == user_id:
            user["name"] = name
            user["email"] = email.lower()
            return web.json_response(user)
    return web.json_response({"error": "User not found"}, status=404)


async def delete_user(request: web.Request) -> web.Response:
    user_id = int(request.match_info["user_id"])
    for index, user in enumerate(users):
        if user["id"] == user_id:
            users.pop(index)
            return web.json_response({"status": "deleted"})
    return web.json_response({"error": "User not found"}, status=404)


def register_routes(app: web.Application) -> None:
    app.router.add_get("/", health)
    app.router.add_get("/users", list_users)
    app.router.add_get("/users/{user_id}", get_user)
    app.router.add_post("/users", create_user)
    app.router.add_put("/users/{user_id}", update_user)
    app.router.add_delete("/users/{user_id}", delete_user)
