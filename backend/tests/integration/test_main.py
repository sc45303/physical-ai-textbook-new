import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from src.main import app, vector_store, rag_service


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.mark.asyncio
@patch('src.main.rag_service')
async def test_root_endpoint(mock_rag_service, client):
    """Test the root endpoint"""
    # Act
    response = client.get("/")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Physical AI & Humanoid Robotics Course RAG Chatbot API" in data["message"]
    assert "endpoints" in data
    assert "POST /chat" in str(data["endpoints"])


@pytest.mark.asyncio
@patch('src.main.rag_service')
async def test_health_check(mock_rag_service, client):
    """Test the health check endpoint"""
    # Act
    response = client.get("/health")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "RAG Chatbot API"


@pytest.mark.asyncio
@patch('src.main.rag_service')
async def test_process_question_success(mock_rag_service, client):
    """Test the chat endpoint with a successful request"""
    # Arrange
    from src.models import ChatbotResponse
    mock_response = ChatbotResponse(
        answer="This is a test answer.",
        sources=["source1", "source2"],
        confidence=0.95,
        grounded_in_book=True
    )
    mock_rag_service.process_question = AsyncMock(return_value=mock_response)
    
    # Act
    response = client.post("/chat", json={
        "question": "What is ROS 2?",
        "module_context": "ros2",
        "chapter_context": "intro"
    })
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This is a test answer."
    assert data["sources"] == ["source1", "source2"]
    assert data["confidence"] == 0.95
    assert data["grounded_in_book"] is True


@pytest.mark.asyncio
@patch('src.main.rag_service')
async def test_process_question_error(mock_rag_service, client):
    """Test the chat endpoint with an error in processing"""
    # Arrange
    mock_rag_service.process_question.side_effect = Exception("Processing error")
    
    # Act
    response = client.post("/chat", json={
        "question": "What is a problematic question?",
        "module_context": "ros2",
        "chapter_context": "intro"
    })
    
    # Assert
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Processing error" in data["detail"]


@pytest.mark.asyncio
@patch('src.main.rag_service')
async def test_search_content_success(mock_rag_service, client):
    """Test the search endpoint with a successful request"""
    # Arrange
    from src.models import SearchResult
    mock_results = [
        SearchResult(
            id="result1",
            title="Test Result 1",
            content="Test content for result 1...",
            module="test_module",
            chapter="test_chapter",
            relevance=0.9
        ),
        SearchResult(
            id="result2",
            title="Test Result 2", 
            content="Test content for result 2...",
            module="test_module",
            chapter="test_chapter",
            relevance=0.8
        )
    ]
    mock_rag_service.search_content = AsyncMock(return_value=mock_results)
    
    # Act
    response = client.post("/search", json={
        "query": "search term",
        "module_filter": "test_module",
        "limit": 10
    })
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "result1"
    assert data[1]["id"] == "result2"


@pytest.mark.asyncio
@patch('src.main.rag_service')
async def test_search_content_error(mock_rag_service, client):
    """Test the search endpoint with an error in processing"""
    # Arrange
    mock_rag_service.search_content.side_effect = Exception("Search error")
    
    # Act
    response = client.post("/search", json={
        "query": "problematic search",
        "module_filter": "test_module",
        "limit": 10
    })
    
    # Assert
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Search error" in data["detail"]


@pytest.mark.asyncio
@patch('src.main.vector_store')
async def test_startup_event(mock_vector_store, client):
    """Test the startup event functionality"""
    # Arrange
    mock_vector_store.initialize = AsyncMock()
    
    # In the actual app, startup_event is triggered automatically
    # For testing, we'll just verify that if it were called, it would work
    from src.main import startup_event
    
    # Act & Assert - just make sure it doesn't throw an exception
    await startup_event()
    mock_vector_store.initialize.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])