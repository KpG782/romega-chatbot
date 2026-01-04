"""
FastAPI Application for Romega Chatbot
Exposes RAG-powered chatbot as REST API with rate limiting and caching
"""

import os
import logging
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
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

# 💬 IMPROVEMENT #1: Conversation sessions storage
conversation_sessions: Dict[str, Dict[str, Any]] = {}
SESSION_TTL = 1800  # 30 minutes in seconds
MAX_HISTORY_LENGTH = 10  # Keep last 10 messages per session

# 📊 IMPROVEMENT #3: Analytics storage (in-memory, move to database in production)
analytics_log: List[Dict[str, Any]] = []

# Global chatbot instance
chatbot: Optional[RomegaChatbotAgent] = None


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # For conversation context
    use_cache: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What services does Romega offer?",
                "session_id": "abc123",
                "use_cache": True
            }
        }


class ChatResponse(BaseModel):
    response: str
    session_id: str  # Return session_id for client to track
    status: str = "success"
    cached: bool = False
    confidence: Optional[str] = None  # high/medium/low
    sources_used: Optional[int] = None  # Number of knowledge base chunks used
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Romega Solutions offers Recruitment Process Outsourcing (RPO)...",
                "session_id": "abc123",
                "status": "success",
                "cached": False,
                "confidence": "high",
                "sources_used": 3
            }
        }


class HealthResponse(BaseModel):
    status: str
    message: str
    api_version: str
    cache_size: Optional[int] = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_cache_key(message: str) -> str:
    """Generate cache key from message"""
    return hashlib.md5(message.lower().strip().encode()).hexdigest()


# 💬 IMPROVEMENT #1: Session Management Functions
def get_or_create_session(session_id: Optional[str] = None) -> tuple[str, List[Dict[str, str]]]:
    """
    Get existing session or create new one
    Returns: (session_id, conversation_history)
    """
    # Clean up expired sessions first
    cleanup_expired_sessions()
    
    if session_id and session_id in conversation_sessions:
        # Existing session found
        session = conversation_sessions[session_id]
        session["last_activity"] = datetime.now()
        return session_id, session["history"]
    else:
        # Create new session
        new_session_id = str(uuid.uuid4())
        conversation_sessions[new_session_id] = {
            "history": [],
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "metadata": {}
        }
        logger.info(f"Created new session: {new_session_id}")
        return new_session_id, []


def add_to_session_history(session_id: str, role: str, content: str):
    """Add message to session history with sliding window"""
    if session_id in conversation_sessions:
        history = conversation_sessions[session_id]["history"]
        history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last N messages (sliding window)
        if len(history) > MAX_HISTORY_LENGTH:
            conversation_sessions[session_id]["history"] = history[-MAX_HISTORY_LENGTH:]


def get_conversation_context(session_id: str) -> str:
    """Format conversation history for context injection"""
    if session_id not in conversation_sessions:
        return ""
    
    history = conversation_sessions[session_id]["history"]
    if not history:
        return ""
    
    # Format last few exchanges as context
    context_parts = []
    for msg in history[-6:]:  # Last 3 exchanges (6 messages)
        role = "User" if msg["role"] == "user" else "Assistant"
        context_parts.append(f"{role}: {msg['content']}")
    
    return "\\n".join(context_parts)


def cleanup_expired_sessions():
    """Remove sessions that have been inactive for > SESSION_TTL"""
    now = datetime.now()
    expired_sessions = [
        sid for sid, session in conversation_sessions.items()
        if (now - session["last_activity"]).total_seconds() > SESSION_TTL
    ]
    
    for sid in expired_sessions:
        del conversation_sessions[sid]
        logger.debug(f"Removed expired session: {sid}")


# 📊 IMPROVEMENT #3: Analytics Logging Function
def log_analytics(event_data: Dict[str, Any]):
    """Log analytics event (in production, send to database/analytics service)"""
    analytics_log.append({
        **event_data,
        "logged_at": datetime.now().isoformat()
    })
    
    # Keep only last 1000 events in memory
    if len(analytics_log) > 1000:
        analytics_log.pop(0)
    
    # Log to file for analysis
    logger.info(f"Analytics: {json.dumps(event_data)}")


# 🛡️ IMPROVEMENT #4: Confidence Scoring Function
def calculate_confidence(retrieved_chunks: List[Dict], query: str) -> str:
    """
    Calculate confidence level based on retrieval quality
    Returns: 'high', 'medium', or 'low'
    """
    if not retrieved_chunks:
        return "low"
    
    # Simple heuristic: use the similarity scores from retrieval
    # In a real system, you'd use more sophisticated metrics
    num_chunks = len(retrieved_chunks)
    
    if num_chunks >= 3:
        return "high"
    elif num_chunks >= 2:
        return "medium"
    else:
        return "low"


# 🛡️ IMPROVEMENT #4: Fallback Response Generator
def get_fallback_response(query: str, confidence: str) -> str:
    """Generate appropriate fallback response based on query and confidence"""
    query_lower = query.lower()
    
    # Detect intent categories
    if any(word in query_lower for word in ["price", "cost", "fee", "pricing", "charge"]):
        return (
            "Pricing varies based on your specific needs and scale. "
            "I'd love to connect you with our team for a personalized quote! "
            "📅 [Schedule a free consultation](https://www.romega-solutions.com) or email us at info@romega-solutions.com"
        )
    
    elif any(word in query_lower for word in ["contact", "call", "talk", "speak", "meeting", "demo"]):
        return (
            "I'd be happy to connect you with our team! You can:\\n\\n"
            "📧 Email: info@romega-solutions.com\\n"
            "🌐 Website: www.romega-solutions.com\\n"
            "📅 Or schedule a free consultation directly through our website!\\n\\n"
            "What specific area would you like to discuss?"
        )
    
    elif any(word in query_lower for word in ["how", "when", "where", "who", "which"]):
        return (
            f"That's a great question! While I don't have specific details on that right now, "
            f"our team can provide you with accurate information. "
            f"Would you like to schedule a quick call or send an email to info@romega-solutions.com?"
        )
    
    else:
        return (
            "I want to make sure you get the most accurate information. "
            "Could you rephrase your question, or would you prefer to speak directly with our team? "
            "You can reach us at info@romega-solutions.com or schedule a consultation on our website."
        )


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
    💬 Enhanced Chat Endpoint with Conversation Context
    
    Features:
    - Multi-turn conversations with session tracking
    - Response caching for common questions
    - Analytics logging
    - Graceful fallbacks for low-confidence answers
    - Rate limiting (20 requests/minute per IP)
    """
    # Start tracking request time for analytics
    start_time = datetime.now()
    
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
        # ✅ IMPROVEMENT #1: Get or create session
        session_id, conversation_history = get_or_create_session(chat_request.session_id)
        
        # Check cache first if enabled (only for standalone questions, not follow-ups)
        cached_response = None
        if chat_request.use_cache and not conversation_history:  # No history = new question
            cached_response = get_cached_response(chat_request.message)
        
        if cached_response:
            logger.info("Returning cached response")
            
            # Still add to session history
            add_to_session_history(session_id, "user", chat_request.message)
            add_to_session_history(session_id, "assistant", cached_response)
            
            # ✅ IMPROVEMENT #3: Log analytics
            log_analytics({
                "event": "chat_response",
                "session_id": session_id,
                "query": chat_request.message,
                "response_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "cached": True,
                "has_context": len(conversation_history) > 0
            })
            
            return ChatResponse(
                response=cached_response,
                session_id=session_id,
                status="success",
                cached=True
            )
        
        # ✅ IMPROVEMENT #1: Build context from conversation history
        conversation_context = get_conversation_context(session_id)
        
        # Get response from chatbot with context
        logger.info(f"Processing chat request: {chat_request.message[:50]}... (Session: {session_id[:8]})")
        
        # Prepare enhanced query with conversation context
        if conversation_context:
            enhanced_query = f"Previous conversation:\\n{conversation_context}\\n\\nCurrent question: {chat_request.message}"
            logger.info(f"Using conversation context ({len(conversation_history)} previous messages)")
        else:
            enhanced_query = chat_request.message
        
        # Get RAG response
        response_text, retrieved_chunks = chatbot.query_with_rag_and_metadata(enhanced_query)
        
        # ✅ IMPROVEMENT #4: Calculate confidence and apply fallbacks if needed
        confidence = calculate_confidence(retrieved_chunks, chat_request.message)
        
        # If confidence is low, use fallback response
        if confidence == "low":
            logger.warning(f"Low confidence response, using fallback")
            response_text = get_fallback_response(chat_request.message, confidence)
        
        # Add to session history
        add_to_session_history(session_id, "user", chat_request.message)
        add_to_session_history(session_id, "assistant", response_text)
        
        # Cache the response (only for standalone questions)
        if chat_request.use_cache and not conversation_history:
            set_cached_response(chat_request.message, response_text)
        
        # Calculate response time
        response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # ✅ IMPROVEMENT #3: Log detailed analytics
        log_analytics({
            "event": "chat_response",
            "session_id": session_id,
            "query": chat_request.message,
            "query_length": len(chat_request.message),
            "response_length": len(response_text),
            "response_time_ms": response_time_ms,
            "cached": False,
            "confidence": confidence,
            "sources_used": len(retrieved_chunks),
            "has_context": len(conversation_history) > 0,
            "conversation_turn": len(conversation_history) // 2 + 1,
            "ip": request.client.host if request.client else "unknown"
        })
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            status="success",
            cached=False,
            confidence=confidence,
            sources_used=len(retrieved_chunks)
        )
    
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        
        # Log error analytics
        log_analytics({
            "event": "chat_error",
            "query": chat_request.message,
            "error": str(e),
            "error_type": type(e).__name__
        })
        
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
            "GET /analytics": "View usage analytics",
            "GET /analytics/summary": "View analytics summary",
            "GET /docs": "Swagger UI documentation",
            "GET /redoc": "ReDoc documentation"
        }
    }


# ============================================================================
# 📊 IMPROVEMENT #3: ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/analytics")
@limiter.limit("10/minute")
async def get_analytics(request: Request, limit: int = 100):
    """
    Get recent analytics events
    
    Parameters:
    - limit: Number of recent events to return (default: 100, max: 1000)
    """
    limit = min(limit, 1000)  # Cap at 1000
    recent_events = analytics_log[-limit:] if analytics_log else []
    
    return {
        "total_events": len(analytics_log),
        "showing": len(recent_events),
        "events": recent_events
    }


@app.get("/analytics/summary")
@limiter.limit("10/minute")
async def get_analytics_summary(request: Request):
    """
    Get analytics summary with insights
    
    Provides:
    - Total queries processed
    - Average response time
    - Most common questions
    - Confidence distribution
    - Session statistics
    """
    if not analytics_log:
        return {
            "message": "No analytics data available yet",
            "total_queries": 0
        }
    
    # Filter chat response events
    chat_events = [e for e in analytics_log if e.get("event") == "chat_response"]
    
    if not chat_events:
        return {
            "message": "No chat events recorded yet",
            "total_queries": 0
        }
    
    # Calculate metrics
    total_queries = len(chat_events)
    cached_queries = sum(1 for e in chat_events if e.get("cached"))
    
    # Average response time
    response_times = [e.get("response_time_ms", 0) for e in chat_events if "response_time_ms" in e]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Confidence distribution
    confidence_dist = {"high": 0, "medium": 0, "low": 0}
    for e in chat_events:
        conf = e.get("confidence", "unknown")
        if conf in confidence_dist:
            confidence_dist[conf] += 1
    
    # Most common queries (top 10)
    from collections import Counter
    query_counter = Counter(e.get("query", "").lower() for e in chat_events if e.get("query"))
    top_questions = query_counter.most_common(10)
    
    # Session stats
    unique_sessions = len(set(e.get("session_id") for e in chat_events if e.get("session_id")))
    
    # Questions with conversation context
    context_queries = sum(1 for e in chat_events if e.get("has_context"))
    
    return {
        "overview": {
            "total_queries": total_queries,
            "unique_sessions": unique_sessions,
            "cached_responses": cached_queries,
            "cache_hit_rate": f"{(cached_queries/total_queries*100):.1f}%" if total_queries > 0 else "0%",
            "queries_with_context": context_queries,
            "multi_turn_rate": f"{(context_queries/total_queries*100):.1f}%" if total_queries > 0 else "0%"
        },
        "performance": {
            "avg_response_time_ms": round(avg_response_time, 2),
            "fastest_response_ms": min(response_times) if response_times else 0,
            "slowest_response_ms": max(response_times) if response_times else 0
        },
        "confidence_distribution": {
            "high": confidence_dist["high"],
            "medium": confidence_dist["medium"],
            "low": confidence_dist["low"],
            "high_confidence_rate": f"{(confidence_dist['high']/total_queries*100):.1f}%" if total_queries > 0 else "0%"
        },
        "top_10_questions": [
            {"question": q, "count": c} 
            for q, c in top_questions
        ],
        "active_sessions": len(conversation_sessions),
        "data_collection_period": {
            "oldest_event": analytics_log[0].get("logged_at") if analytics_log else None,
            "newest_event": analytics_log[-1].get("logged_at") if analytics_log else None
        }
    }


@app.delete("/sessions/{session_id}")
@limiter.limit("10/minute")
async def clear_session(session_id: str, request: Request):
    """Clear a specific session's conversation history"""
    if session_id in conversation_sessions:
        del conversation_sessions[session_id]
        logger.info(f"Cleared session: {session_id}")
        return {"message": f"Session {session_id} cleared successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/sessions/stats")
@limiter.limit("30/minute")
async def session_stats(request: Request):
    """Get statistics about active sessions"""
    if not conversation_sessions:
        return {
            "active_sessions": 0,
            "message": "No active sessions"
        }
    
    now = datetime.now()
    session_ages = [(now - s["created_at"]).total_seconds() for s in conversation_sessions.values()]
    
    return {
        "active_sessions": len(conversation_sessions),
        "session_ttl_seconds": SESSION_TTL,
        "avg_session_age_seconds": round(sum(session_ages) / len(session_ages), 2) if session_ages else 0,
        "total_messages": sum(len(s["history"]) for s in conversation_sessions.values()),
        "avg_messages_per_session": round(
            sum(len(s["history"]) for s in conversation_sessions.values()) / len(conversation_sessions), 2
        ) if conversation_sessions else 0
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
            "GET /analytics": "View usage analytics",
            "GET /analytics/summary": "View analytics summary",
            "GET /sessions/stats": "View session statistics",
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
