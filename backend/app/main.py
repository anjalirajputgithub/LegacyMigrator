from fastapi import FastAPI

from app.api.routes import analyze

app = FastAPI(
    title="Legacy Migrator API",
    description="Detects legacy code patterns in JS and Python using tree-sitter.",
    version="0.1.0",
)

app.include_router(analyze.router, tags=["analysis"])


@app.get("/health")
def health():
    return {"status": "ok"}
