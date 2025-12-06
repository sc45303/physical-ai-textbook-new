from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import required modules
from src.vector_store import VectorStore
from src.rag_service import RAGService
from src.models import UserQuestion, ChatbotResponse, SearchQuery, SearchResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Physical AI & Humanoid Robotics Course RAG Chatbot API",
    description="API for the retrieval-augmented generation chatbot embedded in the Physical AI & Humanoid Robotics Course Book",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the exact frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
try:
    vector_store = VectorStore()
    rag_service = RAGService(vector_store=vector_store)
    logger.info("Backend services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize backend services: {e}")
    raise

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up RAG Chatbot API...")
    # Initialize vector store with course content
    await vector_store.initialize()
    logger.info("Vector store initialized")

@app.post("/chat", response_model=ChatbotResponse)
async def process_question(question: UserQuestion):
    """
    Process user question and return answer based on book content
    """
    try:
        logger.info(f"Processing question: {question.question}")
        
        # Process the question through the RAG pipeline
        response = await rag_service.process_question(
            question.question,
            module_context=question.module_context,
            chapter_context=question.chapter_context,
            selected_text=question.selected_text
        )
        
        return response
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.post("/search", response_model=List[SearchResult])
async def search_content(query: SearchQuery):
    """
    Search book content based on user query
    """
    try:
        logger.info(f"Searching for query: {query.query}")
        
        results = await rag_service.search_content(
            query=query.query,
            module_filter=query.module_filter,
            limit=query.limit
        )
        
        return results
    except Exception as e:
        logger.error(f"Error searching content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching content: {str(e)}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "RAG Chatbot API"}


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Physical AI & Humanoid Robotics Course RAG Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat": "Process user question and return answer",
            "POST /search": "Search book content",
            "GET /health": "Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", 8000)), 
        reload=True
    )