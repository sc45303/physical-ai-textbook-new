from typing import List, Optional
from src.vector_store import VectorStore
from src.models import ChatbotResponse, SearchResult
import logging
import asyncio
import openai
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class RAGService:
    """
    Service for Retrieval-Augmented Generation with course content
    """
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        
        # Initialize OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            openai.api_key = openai_api_key
            self.use_openai = True
        else:
            logger.warning("OPENAI_API_KEY not found. Using local LLM as fallback.")
            self.use_openai = False
            # Initialize local model if available
            self._initialize_local_model()
    
    def _initialize_local_model(self):
        """
        Initialize a local language model as a fallback
        """
        # For now, we'll use a simple prompt-based approach without neural models
        # In a full implementation, this would load a local transformer model
        pass

    async def process_question(self, question: str, module_context: Optional[str] = None, 
                              chapter_context: Optional[str] = None, 
                              selected_text: Optional[str] = None) -> ChatbotResponse:
        """
        Process a user question using RAG approach
        """
        try:
            # Step 1: Retrieve relevant content from vector store
            retrieved_content = await self.retrieve_relevant_content(
                question, module_context, chapter_context, limit=5
            )
            
            if not retrieved_content:
                return ChatbotResponse(
                    answer="I couldn't find relevant content in the course materials to answer your question.",
                    sources=[],
                    confidence=0.0,
                    grounded_in_book=False
                )
            
            # Step 2: Prepare context for the language model
            context = self.format_context_for_llm(retrieved_content, question)
            
            # Step 3: Generate answer using language model
            answer = await self.generate_answer_with_llm(context, question)
            
            # Step 4: Create response
            sources = [item.id for item in retrieved_content]
            
            return ChatbotResponse(
                answer=answer,
                sources=sources,
                confidence=0.95,  # For now, assuming high confidence
                grounded_in_book=True
            )
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            raise

    async def retrieve_relevant_content(self, query: str, module_filter: Optional[str] = None,
                                      chapter_filter: Optional[str] = None, limit: int = 5) -> List:
        """
        Retrieve relevant content from the vector store
        """
        try:
            # Perform vector search to find relevant content
            content_ids_with_scores = await self.vector_store.search(query, limit * 2)  # Get extra results
            
            # Get actual content documents
            content_items = await self.vector_store.get_content_batch([cid for cid, _ in content_ids_with_scores])
            
            # Apply filters if provided
            filtered_items = []
            for item in content_items:
                if module_filter and not self.matches_module(item.module_id, module_filter):
                    continue
                if chapter_filter and not self.matches_chapter(item.chapter_id, chapter_filter):
                    continue
                filtered_items.append(item)
            
            # Return top results after filtering
            return filtered_items[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving content: {str(e)}")
            return []

    def matches_module(self, item_module: str, filter_module: str) -> bool:
        """
        Check if the item's module matches the filter
        """
        # Normalize both strings for comparison
        item_norm = item_module.lower().replace("_", "").replace("-", "").replace(" ", "")
        filter_norm = filter_module.lower().replace("_", "").replace("-", "").replace(" ", "")
        
        # Check if filter is part of item or vice versa
        return filter_norm in item_norm or item_norm in filter_norm

    def matches_chapter(self, item_chapter: str, filter_chapter: str) -> bool:
        """
        Check if the item's chapter matches the filter
        """
        # Normalize both strings for comparison
        item_norm = item_chapter.lower().replace("_", "").replace("-", "").replace(" ", "")
        filter_norm = filter_chapter.lower().replace("_", "").replace("-", "").replace(" ", "")
        
        # Check if filter is part of item or vice versa
        return filter_norm in item_norm or item_norm in filter_norm

    def format_context_for_llm(self, retrieved_content: List, question: str) -> str:
        """
        Format the retrieved content and question for the LLM
        """
        context_parts = [f"The following are excerpts from the Physical AI & Humanoid Robotics Course materials that may help answer the question: '{question}'\n"]
        
        for i, item in enumerate(retrieved_content):
            context_parts.append(f"\nExcerpt {i+1} (Module: {item.module_id}, Chapter: {item.chapter_id}):")
            context_parts.append(f"Title: {item.title}")
            context_parts.append(f"Content: {item.body[:500]}...")  # Truncate long content
            context_parts.append("---")
        
        context_parts.append(f"\nQuestion: {question}")
        context_parts.append("Answer based ONLY on the course materials provided above, and cite which module/chapter the information comes from:")
        
        return "\n".join(context_parts)

    async def generate_answer_with_llm(self, context: str, question: str) -> str:
        """
        Generate an answer using a language model
        """
        if self.use_openai:
            return await self._generate_with_openai_api(context, question)
        else:
            return self._generate_with_prompt_engineering(context, question)

    async def _generate_with_openai_api(self, context: str, question: str) -> str:
        """
        Generate answer using OpenAI API
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Or "gpt-4" for better quality
                messages=[
                    {"role": "system", "content": "You are an assistant for the Physical AI & Humanoid Robotics Course. Answer questions based only on the provided course materials. If you can't find relevant information in the provided context, say so."},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,  # Lower temperature for more consistent answers
                max_tokens=500
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            # Fall back to local method
            return self._generate_with_prompt_engineering(context, question)

    def _generate_with_prompt_engineering(self, context: str, question: str) -> str:
        """
        Generate answer using prompt engineering with local methods
        """
        # In a full implementation, this would use a local transformer model
        # For now, we'll extract the most relevant sentences from the context
        
        # Find sentences that are most likely to contain the answer
        import re
        
        # Simple keyword matching approach
        question_keywords = set(re.findall(r'\b\w{4,}\b', question.lower()))
        
        context_sentences = re.split(r'[.!?]+', context)
        
        # Score sentences based on keyword overlap
        scored_sentences = []
        for sentence in context_sentences:
            sentence_words = set(re.findall(r'\b\w{4,}\b', sentence.lower()))
            overlap = len(question_keywords.intersection(sentence_words))
            scored_sentences.append((sentence.strip(), overlap))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Construct answer from relevant sentences
        top_sentences = [sent for sent, score in scored_sentences if score > 0][:3]
        answer = ". ".join(top_sentences).strip()
        
        if not answer:
            answer = "Based on my analysis of the course materials, I couldn't find specific information to answer your question."
        
        # Add disclaimer since we're not using a real LLM
        answer += " [Note: This answer was generated using basic keyword matching against course materials]"
        
        return answer

    async def search_content(self, query: str, module_filter: Optional[str] = None,
                            limit: int = 10) -> List[SearchResult]:
        """
        Search for content in the course materials
        """
        try:
            # Retrieve relevant content
            content_items = await self.retrieve_relevant_content(query, module_filter, None, limit)
            
            # Convert to search results
            search_results = []
            for item in content_items:
                search_result = SearchResult(
                    id=item.id,
                    title=item.title,
                    content=item.body[:300] + "...",  # Truncate for display
                    module=item.module_id,
                    chapter=item.chapter_id,
                    relevance=0.9  # Placeholder relevance score
                )
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in search_content: {str(e)}")
            return []

    async def validate_answer_grounding(self, answer: str, sources: List[str]) -> bool:
        """
        Validate that the answer is grounded in the provided sources
        """
        # In a full implementation, this would use an NLI (Natural Language Inference) model
        # For now, we'll just check if key concepts from sources appear in the answer
        try:
            source_content = []
            for source_id in sources:
                content = await self.vector_store.get_content_by_id(source_id)
                if content:
                    source_content.append(content.body.lower())
            
            if not source_content:
                return False
                
            answer_lower = answer.lower()
            source_text = " ".join(source_content)
            
            # Simple heuristic: check if at least some content from sources appears in the answer
            source_words = set(source_text.split()[:100])  # Take first 100 words to avoid long processing
            answer_words = set(answer_lower.split())
            
            # Calculate overlap
            intersection = source_words.intersection(answer_words)
            if len(intersection) > 0:
                return True
            else:
                logger.warning("Answer does not appear to be grounded in provided sources")
                return False
                
        except Exception as e:
            logger.error(f"Error validating answer grounding: {str(e)}")
            return False