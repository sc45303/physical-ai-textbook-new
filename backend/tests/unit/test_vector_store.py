import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock, patch
from src.vector_store import VectorStore
from src.models import BookContent


@pytest.fixture
def vector_store():
    """Create a vector store instance for testing"""
    with patch('src.vector_store.QdrantClient') as mock_qdrant:
        vs = VectorStore()
        
        # Mock the encoder
        vs.encoder = MagicMock()
        vs.encoder.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        
        # Mock Qdrant client
        vs.client = mock_qdrant
        vs.client.get_collections.return_value = MagicMock()
        vs.client.get_collections().collections = []
        vs.client.create_collection = MagicMock()
        vs.client.upload_points = MagicMock()
        vs.client.search = MagicMock()
        vs.client.retrieve = MagicMock()
        
        return vs


@pytest.mark.asyncio
async def test_initialize_new_collection(vector_store):
    """Test initialization of a new collection"""
    # Arrange
    vector_store.client.get_collections().collections = []
    
    # Act
    await vector_store.initialize()
    
    # Assert
    vector_store.client.create_collection.assert_called_once()
    assert vector_store.client.create_collection.called_with(
        collection_name=vector_store.collection_name,
        vectors_config=pytest.helpers.anything()
    )


@pytest.mark.asyncio
async def test_initialize_existing_collection(vector_store):
    """Test initialization when collection already exists"""
    # Arrange
    existing_collection = MagicMock()
    existing_collection.name = "book_content"
    vector_store.client.get_collections().collections = [existing_collection]
    
    # Act
    await vector_store.initialize()
    
    # Assert
    vector_store.client.create_collection.assert_not_called()


@pytest.mark.asyncio
async def test_search(vector_store):
    """Test the search functionality"""
    # Arrange
    mock_result = MagicMock()
    mock_result.id = "test_id"
    mock_result.score = 0.8
    vector_store.client.search.return_value = [mock_result]
    
    # Act
    results = await vector_store.search("test query", limit=5)
    
    # Assert
    assert len(results) == 1
    assert results[0][0] == "test_id"
    assert results[0][1] == 0.8
    vector_store.client.search.assert_called_once()


@pytest.mark.asyncio
async def test_get_content_by_id_cached(vector_store):
    """Test getting content by ID when it's in the cache"""
    # Arrange
    test_id = "cached_content_id"
    expected_content = BookContent(
        id=test_id,
        title="Cached Title",
        body="Cached content body",
        module_id="test_module",
        chapter_id="test_chapter"
    )
    vector_store.content_cache[test_id] = expected_content
    
    # Act
    result = await vector_store.get_content_by_id(test_id)
    
    # Assert
    assert result == expected_content
    vector_store.client.retrieve.assert_not_called()


@pytest.mark.asyncio
async def test_get_content_by_id_not_cached(vector_store):
    """Test getting content by ID when it's not in the cache"""
    # Arrange
    test_id = "new_content_id"
    
    # Mock the record returned from Qdrant
    mock_record = MagicMock()
    mock_record.id = test_id
    mock_record.payload = {
        "title": "New Title",
        "content": "New content body",
        "module": "new_module",
        "chapter": "new_chapter"
    }
    vector_store.client.retrieve.return_value = [mock_record]
    
    # Act
    result = await vector_store.get_content_by_id(test_id)
    
    # Assert
    assert result is not None
    assert result.id == test_id
    assert result.title == "New Title"
    assert result.body == "New content body"
    assert result.module_id == "new_module"
    assert result.chapter_id == "new_chapter"
    
    # Verify it was added to cache
    assert test_id in vector_store.content_cache


@pytest.mark.asyncio
async def test_get_content_by_id_not_found(vector_store):
    """Test getting content by ID when it's not found"""
    # Arrange
    test_id = "nonexistent_id"
    vector_store.client.retrieve.return_value = []
    
    # Act
    result = await vector_store.get_content_by_id(test_id)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_content_batch(vector_store):
    """Test getting multiple content items by IDs"""
    # Arrange
    content_ids = ["id1", "id2", "id3"]
    
    # Pre-populate cache for some items
    cached_content = BookContent(
        id="id1",
        title="Cached Title",
        body="Cached content",
        module_id="test_module",
        chapter_id="test_chapter"
    )
    vector_store.content_cache["id1"] = cached_content
    
    # Mock retrieval for uncached items
    def mock_retrieve(collection_name, ids):
        if "id2" in ids:
            mock_record = MagicMock()
            mock_record.id = "id2"
            mock_record.payload = {
                "title": "Uncached Title",
                "content": "Uncached content",
                "module": "test_module",
                "chapter": "test_chapter"
            }
            return [mock_record]
        return []
    vector_store.client.retrieve.side_effect = mock_retrieve
    
    # Act
    results = await vector_store.get_content_batch(content_ids)
    
    # Assert
    assert len(results) == 2  # id1 (cached) and id2 (retrieved)
    assert results[0].id == "id1"
    assert results[1].id == "id2"


def test_split_into_chunks_short_text():
    """Test splitting short text"""
    # Arrange
    vector_store = VectorStore()  # This won't actually call external services
    text = "This is a short text."
    
    # Act
    chunks = vector_store.split_into_chunks(text, max_length=50)
    
    # Assert
    assert len(chunks) == 1
    assert chunks[0] == text


def test_split_into_chunks_long_text():
    """Test splitting long text"""
    # Arrange
    vector_store = VectorStore()
    long_text = "Sentence 1. " * 20  # Create a longer text
    
    # Act
    chunks = vector_store.split_into_chunks(long_text, max_length=50)
    
    # Assert
    assert len(chunks) > 1  # Should be split into multiple chunks
    total_length = sum(len(chunk) for chunk in chunks)
    # Allow for some splitting overhead but should be close to original
    assert total_length >= len(long_text) * 0.9


def test_split_into_chunks_by_paragraphs():
    """Test splitting text by paragraphs"""
    # Arrange
    vector_store = VectorStore()
    text_with_paragraphs = "Paragraph 1 sentence 1. Paragraph 1 sentence 2.\n\nParagraph 2 sentence 1.\n\nParagraph 3 sentence 1. Paragraph 3 sentence 2. Paragraph 3 sentence 3."
    
    # Act
    chunks = vector_store.split_into_chunks(text_with_paragraphs, max_length=40)
    
    # Assert
    assert len(chunks) >= 1  # May or may not be split depending on length
    # Check that paragraphs weren't unnecessarily split
    for chunk in chunks:
        assert "\n\n" in chunk or len(chunk) < 40  # Either contains paragraph breaks or is shorter than limit


if __name__ == "__main__":
    pytest.main([__file__, "-v"])