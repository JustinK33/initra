from fastapi import FastAPI

app = FastAPI(title="{{project_name}}")


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok", "project": "{{project_name}}"}
