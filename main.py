"""
ATS Resume Optimizer API
Main FastAPI application with hybrid processing (rule-based + LLM fallback)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_hybrid import router
from app.utils.helpers import ensure_directories
import uvicorn


# Create FastAPI application
app = FastAPI(
    title="ATS Resume Optimizer",
    description="""
    AI-powered resume optimization with ATS scoring and suggestions.
    
    **Hybrid Processing:**
    - Primary: Rule-based parsing, scoring, and suggestions (fast, no API costs)
    - Fallback: Google Gemini AI (when rule-based methods fail)
    
    **Features:**
    - Resume parsing from PDF/DOCX
    - ATS score calculation (0-100)
    - Actionable improvement suggestions
    - Optimized DOCX resume generation
    
    **Cost Savings:**
    - 90% of requests: 0 tokens (rule-based)
    - 10% of requests: ~1500 tokens (LLM fallback)
    - Average: 97% cost reduction vs LLM-only
    """,
    version="2.0.0",
    docs_url="/",  # Swagger UI at root
    redoc_url="/redoc"
)


# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(router)


# Startup event
@app.on_event("startup")
def startup_event():
    """
    Execute on application startup
    - Create necessary directories
    - Display startup information
    """
    ensure_directories()
    
    print("\n" + "="*70)
    print("ATS Resume Optimizer API - Starting...")
    print("="*70)
    print(f"Version: 2.0.0 (Hybrid Mode)")
    print(f"Processing: Rule-based primary, LLM fallback")
    print(f"Cost Savings: ~97% reduction vs LLM-only")
    print("="*70)
    print(f"Swagger UI: http://localhost:8000")
    print(f"ReDoc: http://localhost:8000/redoc")
    print(f"Configuration: http://localhost:8000/config")
    print("="*70)
    print("API is ready to accept requests!")
    print("="*70 + "\n")


# Shutdown event
@app.on_event("shutdown")
def shutdown_event():
    """
    Execute on application shutdown
    """
    print("\n" + "="*70)
    print("🛑 ATS Resume Optimizer API - Shutting down...")
    print("="*70 + "\n")


# Health check endpoint (redundant with routes but useful for monitoring)
@app.get("/health", tags=["Health"])
def health_check():
    """
    Simple health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "service": "ATS Resume Optimizer",
        "version": "2.0.0"
    }


# Main entry point
if __name__ == "__main__":
    """
    Run the application with uvicorn
    
    Usage:
        python main.py
    
    Or with custom settings:
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    """
    uvicorn.run(
        app,
        host="0.0.0.0",  # Accept connections from any IP
        port=8000,       # Default port
        log_level="info",
        access_log=True,
        reload=False     # Disable auto-reload to avoid import issues
    )