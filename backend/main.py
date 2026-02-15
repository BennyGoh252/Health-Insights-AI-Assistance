from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.routes import chat
from core.session import SessionManager
from core.mock_redis import MockRedisClient
from dotenv import load_dotenv
import logging
import os

# Configure logging globally
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s\n",
)
logger = logging.getLogger("main")

# Lifespan context manager
async def lifespan(app: FastAPI):
    # Startup
    
    # Use mock Redis for development, real Redis for production
    use_mock_redis = os.getenv("USE_MOCK_REDIS", "true").lower() == "true"
    
    if use_mock_redis:
        logger.info("Using in-memory mock Redis for development")
        redis_client = MockRedisClient()
    else:
        logger.info("Using real Redis at localhost:6379")
        from redis.asyncio import Redis
        redis_client = Redis.from_url("redis://localhost:6379", decode_responses=True)
    
    app.state.session_manager = SessionManager(redis_client)
    
    # Override, so it would use your local .env file
    load_dotenv(override=True)  

    # Build graph once
    app.state.graph = chat.build_graph()
    logger.info(app.state.graph.get_graph().draw_ascii())

    yield  # <-- app running after startup

    # Shutdown
    await app.state.session_manager.redis.close()

# Create FastAPI app
app = FastAPI(
    title="Health Insights AI",
    description="AI-powered medical document analysis and health Q&A",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "details": str(exc)},
    )

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)