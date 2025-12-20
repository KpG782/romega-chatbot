"""
FastAPI Application for Romega Chatbot
Exposes RAG-powered chatbot as REST API
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Import our chatbot agent
from src.agent import RomegaChatbotAgent

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Romega Solutions Chatbot API",
    description="RAG-powered chatbot API for Romega Solutions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chatbot instance
chatbot: Optional[RomegaChatbotAgent] = None


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What services does Romega offer?"
            }
        }


class ChatResponse(BaseModel):
    response: str
    status: str = "success"
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Romega Solutions offers Recruitment Process Outsourcing (RPO)...",
                "status": "success"
            }
        }


class HealthResponse(BaseModel):
    status: str
    message: str
    api_version: str


@app.on_event("startup")
async def startup_event():
    """Initialize chatbot on startup"""
    global chatbot
    try:
        print("🚀 Initializing Romega Chatbot...")
        chatbot = RomegaChatbotAgent()
        print("✅ Chatbot initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing chatbot: {e}")
        raise


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - API information"""
    return HealthResponse(
        status="online",
        message="Romega Solutions Chatbot API is running",
        api_version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    return HealthResponse(
        status="healthy",
        message="Chatbot is ready to serve requests",
        api_version="1.0.0"
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint
    
    Send a message and get an AI-powered response based on Romega's knowledge base.
    """
    if chatbot is None:
        raise HTTPException(
            status_code=503,
            detail="Chatbot not initialized. Please try again later."
        )
    
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )
    
    try:
        # Get response from chatbot
        response_text = chatbot.query_with_rag(request.message)
        
        return ChatResponse(
            response=response_text,
            status="success"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


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
