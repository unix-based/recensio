"""
Recensio - Main FastAPI Application
Hackathon-focused simple architecture
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import agents, evaluations, dashboard, target_audience, cache, chat
from app.middleware import (
    RequestLoggingMiddleware,
    PerformanceMonitoringMiddleware,
    SecurityHeadersMiddleware,
    ErrorHandlingMiddleware
)
from app.exceptions import AppException
from app.logger import get_module_logger

logger = get_module_logger(__name__)

app = FastAPI(
    title="Recensio",
    description="Simulate 30 independent users evaluating your product",
    version="1.0.0"
)

# Add modern middleware stack
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(PerformanceMonitoringMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hackathon: allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["evaluations"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(target_audience.router, prefix="/api/target-audience", tags=["target_audience"])
app.include_router(cache.router, prefix="/api/cache", tags=["cache"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Recensio application...")
    logger.info("Valkey/Redis storage ready")
    logger.info("Recensio application started successfully")

@app.get("/")
async def root():
    return {"message": "Recensio", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
