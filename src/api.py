"""
FastAPI Application for Romega Chatbot
Exposes RAG-powered chatbot as REST API with rate limiting and caching
"""

import os
import logging
import hashlib
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import our chatbot agent
from src.agent import RomegaChatbotAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="Romega Solutions Chatbot API",
    description="RAG-powered chatbot API for Romega Solutions with rate limiting and caching",
    version="1.1.0"
)

# Add rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache (use Redis in production for distributed systems)
query_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 3600  # 1 hour in seconds

# Global chatbot instance
chatbot: Optional[RomegaChatbotAgent] = None


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    use_cache: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What services does Romega offer?",
                "use_cache": True
            }
        }


class ChatResponse(BaseModel):
    response: str
    status: str = "success"
    cached: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Romega Solutions offers Recruitment Process Outsourcing (RPO)...",
                "status": "success",
                "cached": False
            }
        }


class HealthResponse(BaseModel):
    status: str
    message: str
    api_version: str
    cache_size: Optional[int] = None


def get_cache_key(message: str) -> str:
    """Generate cache key from message"""
    return hashlib.md5(message.lower().strip().encode()).hexdigest()


def get_cached_response(message: str) -> Optional[str]:
    """Get cached response if available and not expired"""
    cache_key = get_cache_key(message)
    
    if cache_key in query_cache:
        cached_data = query_cache[cache_key]
        expires_at = cached_data.get("expires_at")
        
        if expires_at and datetime.now() < expires_at:
            logger.info(f"Cache hit for query: {message[:50]}...")
            return cached_data.get("response")
        else:
            # Expired, remove from cache
            logger.debug("Cache expired, removing entry")
            del query_cache[cache_key]
    
    logger.debug(f"Cache miss for query: {message[:50]}...")
    return None


def set_cached_response(message: str, response: str):
    """Cache a response"""
    cache_key = get_cache_key(message)
    query_cache[cache_key] = {
        "response": response,
        "expires_at": datetime.now() + timedelta(seconds=CACHE_TTL),
        "created_at": datetime.now()
    }
    logger.debug(f"Cached response for query: {message[:50]}...")


@app.on_event("startup")
async def startup_event():
    """Initialize chatbot on startup"""
    global chatbot
    try:
        logger.info("🚀 Initializing Romega Chatbot...")
        chatbot = RomegaChatbotAgent()
        logger.info("✅ Chatbot initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Error initializing chatbot: {e}", exc_info=True)
        raise


@app.get("/", response_model=HealthResponse)
@limiter.limit("60/minute")
async def root(request: Request):
    """Root endpoint - API information"""
    return HealthResponse(
        status="online",
        message="Romega Solutions Chatbot API is running",
        api_version="1.1.0",
        cache_size=len(query_cache)
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint (no rate limit for health checks)"""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    return HealthResponse(
        status="healthy",
        message="Chatbot is ready to serve requests",
        api_version="1.1.0",
        cache_size=len(query_cache)
    )


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")  # Rate limit: 20 requests per minute per IP
async def chat(chat_request: ChatRequest, request: Request):
    """
    Main chat endpoint with rate limiting and caching
    
    Send a message and get an AI-powered response based on Romega's knowledge base.
    
    Rate limit: 20 requests per minute per IP address
    Responses are cached for 1 hour to improve performance
    """
    if chatbot is None:
        logger.error("Chat request received but chatbot not initialized")
        raise HTTPException(
            status_code=503,
            detail="Chatbot not initialized. Please try again later."
        )
    
    if not chat_request.message or not chat_request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )
    
    try:
        # Check cache first if enabled
        cached_response = None
        if chat_request.use_cache:
            cached_response = get_cached_response(chat_request.message)
        
        if cached_response:
            logger.info("Returning cached response")
            return ChatResponse(
                response=cached_response,
                status="success",
                cached=True
            )
        
        # Get response from chatbot
        logger.info(f"Processing chat request: {chat_request.message[:50]}...")
        response_text = chatbot.query_with_rag(chat_request.message)
        
        # Cache the response
        if chat_request.use_cache:
            set_cached_response(chat_request.message, response_text)
        
        return ChatResponse(
            response=response_text,
            status="success",
            cached=False
        )
    
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.delete("/cache")
@limiter.limit("5/minute")
async def clear_cache(request: Request):
    """Clear the query cache (admin endpoint)"""
    global query_cache
    cache_size = len(query_cache)
    query_cache = {}
    logger.info(f"Cache cleared. Removed {cache_size} entries")
    return {"message": f"Cache cleared. Removed {cache_size} entries"}


@app.get("/cache/stats")
@limiter.limit("30/minute")
async def cache_stats(request: Request):
    """Get cache statistics"""
    total_entries = len(query_cache)
    
    if total_entries == 0:
        return {
            "total_entries": 0,
            "message": "Cache is empty"
        }
    
    # Calculate some stats
    now = datetime.now()
    expired = sum(1 for entry in query_cache.values() 
                  if entry.get("expires_at", now) < now)
    valid = total_entries - expired
    
    return {
        "total_entries": total_entries,
        "valid_entries": valid,
        "expired_entries": expired,
        "cache_ttl_seconds": CACHE_TTL
    }


@app.get("/docs-info")
async def docs_info():
    """Information about API documentation"""
    return {
        "message": "API documentation available at /docs (Swagger UI) and /redoc (ReDoc)",
        "endpoints": {
            "GET /": "API information",
            "GET /health": "Health check",
            "POST /chat": "Send a message to the chatbot",
            "GET /docs": "Swagger UI documentation",
            "GET /redoc": "ReDoc documentation"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", "8000"))
    
    print(f"\n🚀 Starting Romega Chatbot API on port {port}...")
    print(f"📖 API Documentation: http://localhost:{port}/docs")
    print(f"🏥 Health Check: http://localhost:{port}/health")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
