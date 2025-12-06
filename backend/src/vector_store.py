from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.models import BookContent
import logging
import uuid

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Vector store for storing and retrieving book content embeddings
    """
    def __init__(self, collection_name: str = "book_content"):
        # Initialize sentence transformer model for embeddings
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize Qdrant client 
        # In production, use proper credentials and hosted cluster
        try:
            self.client = QdrantClient(
                url="http://localhost:6333"  # Default Qdrant URL
            )
        except:
            # If local Qdrant is not available, try using in-memory mode
            self.client = QdrantClient(":memory:")
        
        self.collection_name = collection_name
        self.vector_size = 384  # Size of all-MiniLM-L6-v2 embeddings
        
        # Book content cache for faster access
        self.content_cache: Dict[str, BookContent] = {}

    async def initialize(self):
        """
        Initialize the vector store collection
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
                # Create collection if it doesn't exist
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
                
                # Index the book content
                await self.index_course_content()
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise

    async def index_course_content(self):
        """
        Index the course content from the documentation into the vector store
        """
        logger.info("Indexing course content into vector store...")
        
        # This would normally read from the actual course files
        # For now, I'll create a function to process the actual content
        await self.load_and_index_documentation()
        logger.info("Course content indexed successfully")

    async def load_and_index_documentation(self):
        """
        Load course documentation and index it in the vector store
        """
        import os
        import glob
        
        # Define the path where course materials are stored
        docs_path = "../../website/docs"  # Relative to backend/src/
        
        points_to_upload = []
        
        # Walk through all markdown files in the docs directory
        for root, dirs, files in os.walk(docs_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    
                    # Extract module and chapter info from path
                    rel_path = os.path.relpath(file_path, docs_path)
                    path_parts = rel_path.split(os.sep)
                    
                    module = "unknown"
                    chapter = "unknown"
                    
                    if len(path_parts) >= 2:
                        module = path_parts[0]
                        chapter = path_parts[1].replace('.md', '') if path_parts[1].endswith('.md') else path_parts[1]
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Split content into chunks to handle large files
                            chunks = self.split_into_chunks(content, max_length=1000)
                            
                            for i, chunk in enumerate(chunks):
                                if chunk.strip():  # Only process non-empty chunks
                                    # Create embeddings for the chunk
                                    embedding = self.encoder.encode(chunk).tolist()
                                    
                                    # Create a unique ID for this chunk
                                    point_id = str(uuid.uuid4())
                                    
                                    # Create payload with metadata
                                    payload = {
                                        "title": f"{module} - {chapter} - Part {i+1}",
                                        "content": chunk,
                                        "module": module,
                                        "chapter": chapter,
                                        "source_file": rel_path,
                                        "chunk_index": i
                                    }
                                    
                                    # Create a point to upload
                                    point = models.PointStruct(
                                        id=point_id,
                                        vector=embedding,
                                        payload=payload
                                    )
                                    
                                    points_to_upload.append(point)
                                    
                                    # Add to cache
                                    book_content = BookContent(
                                        id=point_id,
                                        title=payload["title"],
                                        body=chunk,
                                        module_id=module,
                                        chapter_id=chapter
                                    )
                                    self.content_cache[point_id] = book_content
                                    
                    except Exception as e:
                        logger.warning(f"Error processing file {file_path}: {str(e)}")
                        continue
        
        # Upload all points in batches
        if points_to_upload:
            batch_size = 100  # Process in batches to avoid memory issues
            for i in range(0, len(points_to_upload), batch_size):
                batch = points_to_upload[i:i+batch_size]
                self.client.upload_points(
                    collection_name=self.collection_name,
                    points=batch
                )
                
                logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(points_to_upload)-1)//batch_size + 1}")
        
        logger.info(f"Indexed {len(points_to_upload)} content chunks from course materials")

    def split_into_chunks(self, text: str, max_length: int = 1000) -> List[str]:
        """
        Split text into chunks of approximately max_length characters
        """
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        for paragraph in paragraphs:
            # If adding this paragraph would exceed max length
            if len(current_chunk) + len(paragraph) > max_length and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph
            
            # If current chunk is still too big, split it by sentences
            if len(current_chunk) > max_length:
                # Split large paragraph into sentences
                sentences = paragraph.split('. ')
                temp_chunk = ""
                
                for sentence in sentences:
                    if len(temp_chunk + ". " + sentence) <= max_length:
                        temp_chunk += ". " + sentence
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                        temp_chunk = sentence
                
                if temp_chunk:
                    current_chunk = temp_chunk
                else:
                    current_chunk = ""
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    async def search(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Search for similar content based on query
        Returns list of (content_id, similarity_score) tuples
        """
        # Encode the query
        query_embedding = self.encoder.encode(query).tolist()
        
        # Search in Qdrant
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )
        
        # Extract results
        results = []
        for hit in search_results:
            results.append((hit.id, hit.score))
        
        return results

    async def get_content_by_id(self, content_id: str) -> Optional[BookContent]:
        """
        Retrieve content by ID
        """
        if content_id in self.content_cache:
            return self.content_cache[content_id]
        
        # If not in cache, fetch from vector store
        records = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[content_id]
        )
        
        if records:
            record = records[0]
            payload = record.payload
            content = BookContent(
                id=record.id,
                title=payload.get("title", ""),
                body=payload.get("content", ""),
                module_id=payload.get("module", ""),
                chapter_id=payload.get("chapter", "")
            )
            # Add to cache for future use
            self.content_cache[content_id] = content
            return content
        
        return None

    async def get_content_batch(self, content_ids: List[str]) -> List[BookContent]:
        """
        Retrieve multiple content items by IDs
        """
        results = []
        for content_id in content_ids:
            content = await self.get_content_by_id(content_id)
            if content:
                results.append(content)
        return results