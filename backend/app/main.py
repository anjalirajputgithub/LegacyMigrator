from fastapi import FastAPI

from app.api.routes import analyze, migrate

app = FastAPI(
    title="Legacy Migrator API",
    description="Detects legacy code patterns in JS and Python using tree-sitter.",
    version="0.1.0",
)

app.include_router(analyze.router, tags=["analysis"])
app.include_router(migrate.router, tags=["migration"])


@app.get("/health")
def health():
    return {"status": "ok"}
