from fastapi import FastAPI

from src.api.routes.health import router as health_router
from src.api.routes.users import router as users_router

app = FastAPI(title="{{project_name}}")
app.include_router(health_router)
app.include_router(users_router)


@app.get("/readyz")
def ready() -> dict[str, str]:
    return {"status": "ready", "project": "{{project_name}}"}
