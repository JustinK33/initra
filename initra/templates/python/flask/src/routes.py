from flask import Blueprint, jsonify, request

from src.config import settings
from src.db import users


health_bp = Blueprint("health", __name__)
next_id = 1


@health_bp.get("/")
def health() -> tuple[dict[str, str], int]:
    return jsonify(status="ok", project="{{project_name}}", env=settings.env), 200


@health_bp.get("/users")
def list_users() -> tuple[dict[str, object], int]:
    return jsonify(users=users), 200


@health_bp.get("/users/<int:user_id>")
def get_user(user_id: int) -> tuple[dict[str, object], int]:
    for user in users:
        if user["id"] == user_id:
            return jsonify(user), 200
    return jsonify(error="User not found"), 404


@health_bp.post("/users")
def create_user() -> tuple[dict[str, object], int]:
    global next_id
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    if len(name) < 2 or "@" not in email:
        return jsonify(error="Invalid name or email"), 400

    user = {"id": next_id, "name": name, "email": email.lower()}
    next_id += 1
    users.append(user)
    return jsonify(user), 201


@health_bp.put("/users/<int:user_id>")
def update_user(user_id: int) -> tuple[dict[str, object], int]:
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    if len(name) < 2 or "@" not in email:
        return jsonify(error="Invalid name or email"), 400

    for user in users:
        if user["id"] == user_id:
            user["name"] = name
            user["email"] = email.lower()
            return jsonify(user), 200
    return jsonify(error="User not found"), 404


@health_bp.delete("/users/<int:user_id>")
def delete_user(user_id: int) -> tuple[dict[str, str], int]:
    for index, user in enumerate(users):
        if user["id"] == user_id:
            users.pop(index)
            return jsonify(status="deleted"), 200
    return jsonify(error="User not found"), 404
