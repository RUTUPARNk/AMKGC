from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config.config import settings
from api.router import router
from services.health_service import start_background_health_checks
from services.ollama_warmup import ollama_warmup_service
from services.ollama_supervisor import ollama_supervisor_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Node-Based LLM System API",
    description="A comprehensive platform for managing and interacting with LLM-powered nodes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting Node LLM System API...")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info(f"API Host: {settings.API_HOST}")
    logger.info(f"API Port: {settings.API_PORT}")
    logger.info(f"Ollama Model: {settings.OLLAMA_MODEL}")
    
    # Warm up Ollama model
    if settings.LLM_PROVIDER == "ollama":
        logger.info("Warming up Ollama model...")
        warmup_success = ollama_warmup_service.warmup_model()
        if warmup_success:
            logger.info("Ollama model warmed up successfully!")
            # Start keep-alive daemon to maintain model in memory
            logger.info("Starting keep-alive daemon...")
            ollama_warmup_service.start_keep_alive_daemon()
        else:
            logger.warning("Ollama model warmup failed. Service may be slow on first request.")
    
    logger.info("Node LLM System API started successfully!")

    # Start background health checks (every 10 seconds)
    start_background_health_checks(interval_seconds=10)
    
    # Start Ollama supervisor service
    logger.info("Starting Ollama supervisor service...")
    ollama_supervisor_service.start_supervisor()

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down Node LLM System API...")
    # Stop Ollama supervisor service
    logger.info("Stopping Ollama supervisor service...")
    ollama_supervisor_service.stop_supervisor()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 