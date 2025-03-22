from fastapi import FastAPI

app = FastAPI(
    title="ModelForge AI",
    description="AutoML platform that transforms plain-language requirements into production-ready ML models",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Welcome to ModelForge AI"}