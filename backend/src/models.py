from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserQuestion(BaseModel):
    """
    Request model for user questions to the chatbot
    """
    question: str
    module_context: Optional[str] = None
    chapter_context: Optional[str] = None
    selected_text: Optional[str] = None


class ChatbotResponse(BaseModel):
    """
    Response model for chatbot answers
    """
    answer: str
    sources: List[str]
    confidence: float
    grounded_in_book: bool
    timestamp: datetime = datetime.now()


class SearchQuery(BaseModel):
    """
    Request model for searching book content
    """
    query: str
    module_filter: Optional[str] = None
    limit: int = 10


class SearchResult(BaseModel):
    """
    Response model for search results
    """
    id: str
    title: str
    content: str
    module: str
    chapter: str
    relevance: float


class BookContent(BaseModel):
    """
    Model representing book content for RAG system
    """
    id: str
    title: str
    body: str
    module_id: Optional[str] = None
    chapter_id: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    version: str = "1.0"


class ChatMessage(BaseModel):
    """
    Model representing a chat message in the conversation history
    """
    id: str
    question: str
    answer: str
    timestamp: datetime = datetime.now()
    sources: List[str] = []