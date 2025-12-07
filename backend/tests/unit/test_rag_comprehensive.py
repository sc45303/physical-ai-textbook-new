import os
import sys
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.rag_service import RAGService
from src.vector_store import VectorStore
from src.models import UserQuestion, ChatbotResponse, SearchResult


# Mock the OpenAI API to avoid actual API calls during testing
@pytest.fixture
def mock_openai():
    with patch('src.rag_service.openai') as mock_openai:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = {'content': 'This is a test response from the LLM.'}
        mock_openai.ChatCompletion.create.return_value = mock_response
        yield mock_openai


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store for testing"""
    mock_vs = MagicMock(spec=VectorStore)
    
    # Mock the search method
    async def mock_search(query, limit=10):
        return [("content_id_1", 0.8), ("content_id_2", 0.7)]
    mock_vs.search = mock_search
    
    # Mock the get_content_batch method
    async def mock_get_content_batch(content_ids):
        from src.models import BookContent
        contents = []
        for i, cid in enumerate(content_ids):
            content = BookContent(
                id=cid,
                title=f"Test Content {i}",
                body=f"This is test content {i} for the RAG system.",
                module_id=f"module_{i}",
                chapter_id=f"chapter_{i}"
            )
            contents.append(content)
        return contents
    mock_vs.get_content_batch = mock_get_content_batch
    
    # Mock the get_content_by_id method
    async def mock_get_content_by_id(content_id):
        from src.models import BookContent
        return BookContent(
            id=content_id,
            title="Test Content",
            body="This is test content for the RAG system.",
            module_id="test_module",
            chapter_id="test_chapter"
        )
    mock_vs.get_content_by_id = mock_get_content_by_id
    
    return mock_vs


@pytest.fixture
def rag_service(mock_vector_store):
    """Create a RAG service instance for testing"""
    service = RAGService(vector_store=mock_vector_store)
    # Disable OpenAI usage for testing
    service.use_openai = False
    return service


@pytest.mark.asyncio
async def test_process_question_success(rag_service):
    """Test the process_question method with valid input"""
    # Act
    result = await rag_service.process_question(
        "What is ROS 2?",
        module_context="ros2",
        chapter_context="intro"
    )
    
    # Assert
    assert isinstance(result, ChatbotResponse)
    assert result.answer is not None
    assert len(result.sources) >= 0
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.grounded_in_book, bool)


@pytest.mark.asyncio
async def test_process_question_no_content_found(rag_service, mock_vector_store):
    """Test the process_question method when no content is found"""
    # Arrange
    async def mock_search_empty(query, limit=10):
        return []
    mock_vector_store.search = mock_search_empty
    
    async def mock_get_content_batch_empty(content_ids):
        return []
    mock_vector_store.get_content_batch = mock_get_content_batch_empty
    
    # Act
    result = await rag_service.process_question("What is a non-existent topic?")
    
    # Assert
    assert isinstance(result, ChatbotResponse)
    assert result.grounded_in_book is False


@pytest.mark.asyncio
async def test_retrieve_relevant_content(rag_service):
    """Test the retrieve_relevant_content method"""
    # Act
    result = await rag_service.retrieve_relevant_content("test query", limit=3)
    
    # Assert
    assert len(result) >= 0


@pytest.mark.asyncio
async def test_search_content(rag_service):
    """Test the search_content method"""
    # Act
    result = await rag_service.search_content("test query", limit=5)
    
    # Assert
    assert isinstance(result, list)
    if result:
        assert all(isinstance(item, SearchResult) for item in result)


@pytest.mark.asyncio
async def test_generate_answer_with_llm_local(rag_service, mock_vector_store):
    """Test the local LLM generation method"""
    # Arrange
    mock_content_item = MagicMock()
    mock_content_item.module_id = "test_module"
    mock_content_item.chapter_id = "test_chapter"
    mock_content_item.title = "Test Title"
    mock_content_item.body = "The robot operating system ROS 2 is a middleware."
    
    # Act
    result = await rag_service._generate_with_openai_api(
        "Context: The robot operating system ROS 2 is a middleware.\nQuestion: What is ROS 2?",
        "What is ROS 2?"
    )
    
    # Assert - this will call the fallback method since we don't have actual API key
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_validate_answer_grounding(rag_service, mock_vector_store):
    """Test the validate_answer_grounding method"""
    # Arrange
    mock_content = MagicMock()
    mock_content.body = "The robot operating system ROS 2 is a middleware."
    
    async def mock_get_content_by_id(content_id):
        return mock_content
    mock_vector_store.get_content_by_id = mock_get_content_by_id
    
    # Act
    result = await rag_service.validate_answer_grounding(
        "ROS 2 is a robot operating system middleware.",
        ["content_id_1"]
    )
    
    # Assert
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_format_context_for_llm(rag_service):
    """Test the format_context_for_llm method"""
    # Arrange
    from src.models import BookContent
    content_item = BookContent(
        id="test_id",
        title="Test Title",
        body="Test body content about robotics.",
        module_id="test_module",
        chapter_id="test_chapter"
    )
    
    # Act
    context = rag_service.format_context_for_llm([content_item], "What is robotics?")
    
    # Assert
    assert "What is robotics?" in context
    assert "test_module" in context
    assert "test_chapter" in context
    assert "Test Title" in context
    assert "Test body content about robotics." in context


def test_matches_module():
    """Test the matches_module helper function"""
    # This test would be part of a class, so we'll access it differently
    from src.rag_service import RAGService
    service = RAGService(MagicMock())
    
    # Test exact match
    assert service.matches_module("ros2", "ros2") is True
    
    # Test partial match
    assert service.matches_module("ros2_concepts", "ros2") is True
    
    # Test no match
    assert service.matches_module("simulation", "ros2") is False


def test_matches_chapter():
    """Test the matches_chapter helper function"""
    from src.rag_service import RAGService
    service = RAGService(MagicMock())
    
    # Test exact match
    assert service.matches_chapter("intro", "intro") is True
    
    # Test partial match
    assert service.matches_chapter("introduction_to_ros", "intro") is True
    
    # Test no match
    assert service.matches_chapter("advanced", "intro") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])