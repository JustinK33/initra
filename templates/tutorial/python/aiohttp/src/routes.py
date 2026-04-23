"""Route handlers for aiohttp application.

aiohttp uses async functions as route handlers. Each handler receives
the request object and must return a Response (or subclass) object.

Key concepts:
- async/await: aiohttp uses Python's async syntax for non-blocking I/O
- Request: represents the HTTP request (method, headers, body, etc.)
- Response: represents the HTTP response (status, body, headers)
"""
from aiohttp import web

from src.config import settings
from src.db import users


# Track the next available ID for new users
next_id = 1


async def health(request: web.Request) -> web.Response:
    """Health check endpoint - returns basic status info.

    Handlers are async functions - they can handle many concurrent requests.
    The 'request' parameter contains info about the HTTP request.
    """
    return web.json_response({"status": "ok", "project": "{{project_name}}", "env": settings.env})


async def list_users(request: web.Request) -> web.Response:
    """GET /users - List all users in the system."""
    return web.json_response({"users": users})


async def get_user(request: web.Request) -> web.Response:
    """GET /users/:id - Get a specific user by ID.

    request.match_info extracts path parameters defined with {}.
    For example, /users/42 gives user_id = "42"
    """
    user_id = int(request.match_info["user_id"])
    for user in users:
        if user["id"] == user_id:
            return web.json_response(user)
    return web.json_response({"error": "User not found"}, status=404)
    # 404 is "Not Found" - the user doesn't exist


async def create_user(request: web.Request) -> web.Response:
    """POST /users - Create a new user.

    await request.json() asynchronously reads the request body.
    This is non-blocking - other requests can be processed while waiting.
    """
    global next_id
    payload = await request.json()
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()

    # Simple validation
    if len(name) < 2 or "@" not in email:
        return web.json_response({"error": "Invalid name or email"}, status=400)
        # 400 is "Bad Request" - the input wasn't valid

    user = {"id": next_id, "name": name, "email": email.lower()}
    next_id += 1
    users.append(user)

    return web.json_response(user, status=201)
    # 201 is "Created" - a new resource was successfully created


async def update_user(request: web.Request) -> web.Response:
    """PUT /users/:id - Update an existing user."""
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
    """DELETE /users/:id - Delete a user by ID."""
    user_id = int(request.match_info["user_id"])
    for index, user in enumerate(users):
        if user["id"] == user_id:
            users.pop(index)
            return web.json_response({"status": "deleted"})
    return web.json_response({"error": "User not found"}, status=404)


def register_routes(app: web.Application) -> None:
    """Register all routes with the application.

    Each route is added using app.router.add_METHOD(PATH, HANDLER).
    This maps URLs to the async handler functions above.
    """
    app.router.add_get("/", health)
    app.router.add_get("/users", list_users)
    app.router.add_get("/users/{user_id}", get_user)
    app.router.add_post("/users", create_user)
    app.router.add_put("/users/{user_id}", update_user)
    app.router.add_delete("/users/{user_id}", delete_user)