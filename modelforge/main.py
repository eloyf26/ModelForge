from fastapi import FastAPI
from modelforge.logging.logger import get_logger

# Create logger for this module
logger = get_logger(__name__)

app = FastAPI(
    title="ModelForge AI",
    description="AutoML platform that transforms plain-language requirements into production-ready ML models",
    version="1.0.0"
)

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to ModelForge AI"}