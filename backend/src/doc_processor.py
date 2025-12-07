import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import markdown
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class DocumentationProcessor:
    """
    Helper class to process Docusaurus documentation for the RAG system
    """
    
    def __init__(self, docs_path: str = "../../website/docs"):
        self.docs_path = Path(docs_path)
        self.content_cache: Dict[str, Any] = {}
        
    async def extract_content_from_docs(self) -> List[Dict[str, str]]:
        """
        Extract content from Docusaurus markdown files
        """
        all_content = []
        
        # Walk through all markdown files in the docs directory
        for md_file in self.docs_path.rglob("*.md"):
            try:
                content = await self._process_markdown_file(md_file)
                all_content.extend(content)
            except Exception as e:
                logger.error(f"Error processing file {md_file}: {str(e)}")
                continue
        
        return all_content
    
    async def _process_markdown_file(self, file_path: Path) -> List[Dict[str, str]]:
        """
        Process a single markdown file and extract content segments
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use markdown library to convert to HTML, then extract text
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title from the first header
        title_tag = soup.find(['h1', 'h2'])
        title = title_tag.get_text() if title_tag else file_path.stem
        
        # Extract the main content (remove headers and structural elements)
        for element in soup(['script', 'style', 'header', 'footer', 'nav']):
            element.decompose()
        
        raw_text = soup.get_text(separator=' ')
        
        # Clean up the text
        content_text = self._clean_text(raw_text)
        
        # Split into meaningful chunks (sections between headers)
        chunks = self._split_into_chunks(content_text, max_length=1000)
        
        # Determine module and chapter from file path
        relative_path = file_path.relative_to(self.docs_path)
        path_parts = relative_path.parts
        
        module = path_parts[0] if len(path_parts) > 0 else "intro"
        chapter = path_parts[1] if len(path_parts) > 1 else file_path.stem
        
        # Create content items for each chunk
        content_items = []
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) > 50:  # Only include substantial chunks
                content_items.append({
                    "id": f"{relative_path.as_posix()}_chunk_{i}",
                    "title": f"{title} - Part {i+1}",
                    "body": chunk,
                    "module": module,
                    "chapter": chapter,
                    "source_file": str(relative_path)
                })
        
        return content_items
    
    def _clean_text(self, text: str) -> str:
        """
        Clean up extracted text
        """
        # Remove extra whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might be parsing artifacts
        text = re.sub(r'\\n+', ' ', text)
        return text.strip()
    
    def _split_into_chunks(self, text: str, max_length: int = 1000) -> List[str]:
        """
        Split text into chunks not exceeding max_length
        """
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) <= max_length:
                current_chunk += "\n\n" + paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
                # If a single paragraph is too long, split it by sentences
                if len(current_chunk) > max_length:
                    sentences = self._split_long_paragraph(current_chunk, max_length)
                    chunks.extend(sentences[:-1])  # Add all but the last sentence
                    current_chunk = sentences[-1] if sentences else ""  # Use last sentence as start of next chunk
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_long_paragraph(self, paragraph: str, max_length: int) -> List[str]:
        """
        Split a long paragraph into smaller chunks
        """
        sentences = []
        current_sentence = ""
        
        # Split by sentence endings
        parts = re.split(r'([.!?]+)', paragraph)
        
        for i in range(0, len(parts), 2):
            sentence_part = parts[i] if i < len(parts) else ''
            punctuation = parts[i+1] if i+1 < len(parts) else ''
            
            full_sentence = sentence_part + punctuation
            
            if len(current_sentence + full_sentence) <= max_length:
                current_sentence += full_sentence
            else:
                if current_sentence:
                    sentences.append(current_sentence.strip())
                current_sentence = full_sentence
        
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences

# Async function to initialize vector store with course content
async def initialize_with_documentation(vector_store):
    """
    Initialize the vector store with content from the Docusaurus site
    """
    processor = DocumentationProcessor()
    content_items = await processor.extract_content_from_docs()
    
    # Process and add each content item to the vector store
    for item in content_items:
        # Create embedding for the content
        text = item['title'] + " " + item['body']
        embedding = vector_store.encoder.encode(text).tolist()
        
        # Create a unique ID for this content item
        import uuid
        content_id = str(uuid.uuid4())
        
        # Create payload with metadata
        payload = {
            "title": item['title'],
            "content": item['body'],
            "module": item['module'],
            "chapter": item['chapter'],
            "source_file": item['source_file']
        }
        
        # Upload to the vector store
        from qdrant_client.http import models
        point = models.PointStruct(
            id=content_id,
            vector=embedding,
            payload=payload
        )
        
        # Store in vector DB (in batches to avoid overloading)
        vector_store.client.upload_points(
            collection_name=vector_store.collection_name,
            points=[point]
        )
        
        # Also store in cache
        from src.models import BookContent
        from datetime import datetime
        
        book_content = BookContent(
            id=content_id,
            title=item['title'],
            body=item['body'],
            module_id=item['module'],
            chapter_id=item['chapter']
        )
        vector_store.content_cache[content_id] = book_content
    
    print(f"Indexed {len(content_items)} content items from documentation")