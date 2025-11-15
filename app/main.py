"""
FastAPI entrypoint for the Insight Agent IDP application.
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.schemas import QueryRequest, QueryResponse
from app.services.rag import RAGService
from app.agents.insight_agent import InsightAgent
from app.db import get_db
from sqlalchemy.orm import Session

app = FastAPI(
    title="Insight Agent IDP",
    description="Intelligent Document Processing with RAG capabilities",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services (singleton pattern)
_rag_service = None
_agent = None

def get_rag_service() -> RAGService:
    """Get or create RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

def get_agent() -> InsightAgent:
    """Get or create agent instance."""
    global _agent
    if _agent is None:
        rag_service = get_rag_service()
        _agent = InsightAgent(rag_service=rag_service)
    return _agent

@app.get("/")
async def root():
    return {
        "message": "Insight Agent IDP API",
        "version": "1.0.0",
        "endpoints": {
            "/chat/insights": "POST - Main endpoint for insight queries",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/chat/insights", response_model=QueryResponse)
async def chat_insights(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Main endpoint for the Insight Agent.
    
    Accepts natural language queries and returns insights using:
    - SQL queries on structured data
    - RAG for document retrieval
    - Precomputed metrics
    """
    try:
        agent = get_agent()
        
        response = agent.process_query(
            query=request.query,
            use_rag=request.use_rag,
            use_sql=request.use_sql
        )
        
        return QueryResponse(
            answer=response.get("answer", "No answer generated"),
            sources=response.get("sources", []),
            sql_query=response.get("sql_query")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)

