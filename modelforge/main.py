import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ModelForge AI",
    description="AutoML platform that transforms plain-language requirements into production-ready ML models",
    version="1.0.0"
)

@app.get("/")
async def root():
    logger.info("Received request to root endpoint")
    return {"message": "Welcome to ModelForge AI"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting ModelForge AI application")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down ModelForge AI application")