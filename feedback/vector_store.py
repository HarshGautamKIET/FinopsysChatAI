"""
Vector Store for Feedback Management
Integrates with FAISS for storing and retrieving feedback embeddings
"""
import uuid
import json
import logging
import os
import sys
import pickle
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file))
sys.path.insert(0, project_root)

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available. Install with: pip install faiss-cpu")

try:
    import google.generativeai as genai
    GEMINI_EMBEDDING_AVAILABLE = True
except ImportError:
    GEMINI_EMBEDDING_AVAILABLE = False
    logging.warning("Google Generative AI not available for embeddings")

from config import Config

logger = logging.getLogger(__name__)

class FeedbackVectorStore:
    """Vector store for feedback storage and retrieval using FAISS"""
    
    def __init__(self):
        self.config = Config()
        self.index = None
        self.feedback_data = []
        self.embedding_dimension = 768  # Gemini embedding dimension
        self.similarity_threshold = self.config.get('FEEDBACK_SIMILARITY_THRESHOLD', 0.85)
        self.max_results = self.config.get('FEEDBACK_MAX_RESULTS', 5)
        
        # File paths
        self.index_path = self.config.get('FAISS_INDEX_PATH', './feedback_data/faiss_index')
        self.data_path = self.config.get('FEEDBACK_DATA_PATH', './feedback_data/feedback.json')
        
        if FAISS_AVAILABLE:
            self._initialize_faiss()
        else:
            logger.error("FAISS not available. Feedback system will not work.")
    
    def _initialize_faiss(self):
        """Initialize FAISS index and load existing data"""
        try:
            # Create data directory if it doesn't exist
            data_dir = Path(self.data_path).parent
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Try to load existing index and data
            if os.path.exists(self.index_path) and os.path.exists(self.data_path):
                try:
                    # Load FAISS index
                    self.index = faiss.read_index(self.index_path)
                    
                    # Load feedback data
                    with open(self.data_path, 'r') as f:
                        self.feedback_data = json.load(f)
                    
                    logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
                except Exception as e:
                    logger.warning(f"Failed to load existing data: {e}. Creating new index.")
                    self._create_new_index()
            else:
                self._create_new_index()
                
        except Exception as e:
            logger.error(f"Failed to initialize FAISS: {str(e)}")
            self.index = None
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        try:
            # Create new FAISS index (L2 distance)
            self.index = faiss.IndexFlatL2(self.embedding_dimension)
            self.feedback_data = []
            
            # Save empty index
            self._save_index()
            
            logger.info("Created new FAISS index")
        except Exception as e:
            logger.error(f"Failed to create FAISS index: {e}")
            self.index = None
    
    def _save_index(self):
        """Save FAISS index and feedback data to disk"""
        try:
            if self.index is not None:
                # Ensure directory exists
                index_dir = Path(self.index_path).parent
                index_dir.mkdir(parents=True, exist_ok=True)
                
                # Save FAISS index
                faiss.write_index(self.index, self.index_path)
                
                # Save feedback data
                with open(self.data_path, 'w') as f:
                    json.dump(self.feedback_data, f, indent=2, default=str)
                
                logger.debug("Saved FAISS index and feedback data")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Gemini API"""
        if not GEMINI_EMBEDDING_AVAILABLE:
            logger.error("Gemini embedding not available")
            return []
        
        try:
            # Configure Gemini
            if self.config.GEMINI_API_KEY:
                genai.configure(api_key=self.config.GEMINI_API_KEY)
                
                # Use Gemini's embedding model
                response = genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="semantic_similarity"
                )
                
                return response['embedding']
            else:
                logger.error("Gemini API key not configured")
                return []
                
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            return []
    
    def store_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """Store feedback with embedding in FAISS index"""
        if not self.index:
            logger.error("FAISS index not initialized")
            return False
        
        try:
            # Generate embedding from prompt + response
            text_for_embedding = f"{feedback_data['original_prompt']} {feedback_data['original_response']}"
            embedding = self.generate_embedding(text_for_embedding)
            
            if not embedding:
                logger.error("Failed to generate embedding for feedback")
                return False
            
            # Create feedback entry
            feedback_id = str(uuid.uuid4())
            feedback_entry = {
                "id": feedback_id,
                "original_prompt": feedback_data['original_prompt'],
                "original_response": feedback_data['original_response'],
                "developer_feedback": feedback_data['developer_feedback'],
                "vendor_id": feedback_data.get('vendor_id'),
                "case_id": feedback_data.get('case_id'),
                "sql_query": feedback_data.get('sql_query'),
                "query_type": feedback_data.get('query_type'),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Add to FAISS index
            embedding_array = np.array([embedding], dtype=np.float32)
            self.index.add(embedding_array)
            
            # Add to feedback data
            self.feedback_data.append(feedback_entry)
            
            # Save to disk
            self._save_index()
            
            logger.info(f"Stored feedback with ID: {feedback_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store feedback: {str(e)}")
            return False
    
    def search_similar_feedback(self, prompt: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar feedback based on prompt similarity"""
        if not self.index or self.index.ntotal == 0:
            logger.warning("FAISS index not initialized or empty")
            return []
        
        try:
            # Generate embedding for the current prompt
            embedding = self.generate_embedding(prompt)
            
            if not embedding:
                logger.error("Failed to generate embedding for search")
                return []
            
            # Search for similar vectors
            query_vector = np.array([embedding], dtype=np.float32)
            
            # Get more results than needed and filter by threshold later
            search_limit = min(limit * 2, self.index.ntotal)
            distances, indices = self.index.search(query_vector, search_limit)
            
            # Convert distances to similarity scores (higher = more similar)
            # FAISS returns L2 distances, convert to similarity
            similarities = 1 / (1 + distances[0])
            
            # Filter by similarity threshold and limit results
            similar_feedback = []
            for i, (similarity, idx) in enumerate(zip(similarities, indices[0])):
                if similarity >= self.similarity_threshold and len(similar_feedback) < limit:
                    if 0 <= idx < len(self.feedback_data):
                        feedback_item = self.feedback_data[idx].copy()
                        feedback_item["similarity_score"] = float(similarity)
                        similar_feedback.append(feedback_item)
            
            logger.info(f"Found {len(similar_feedback)} similar feedback items")
            return similar_feedback
            
        except Exception as e:
            logger.error(f"Failed to search feedback: {str(e)}")
            return []
    
    def get_all_feedback(self, vendor_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all feedback items, optionally filtered by vendor"""
        try:
            if vendor_id:
                # Filter by vendor_id
                filtered_feedback = [
                    f for f in self.feedback_data 
                    if f.get("vendor_id") == vendor_id
                ]
            else:
                filtered_feedback = self.feedback_data.copy()
            
            # Sort by creation date (newest first)
            filtered_feedback.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            logger.info(f"Retrieved {len(filtered_feedback)} feedback items")
            return filtered_feedback
            
        except Exception as e:
            logger.error(f"Failed to get feedback: {str(e)}")
            return []
    
    def update_feedback(self, feedback_id: str, updated_feedback: Dict[str, Any]) -> bool:
        """Update existing feedback item"""
        try:
            # Find the feedback item
            feedback_index = None
            for i, feedback in enumerate(self.feedback_data):
                if feedback["id"] == feedback_id:
                    feedback_index = i
                    break
            
            if feedback_index is None:
                logger.error(f"Feedback with ID {feedback_id} not found")
                return False
            
            # Update the feedback data
            self.feedback_data[feedback_index].update(updated_feedback)
            self.feedback_data[feedback_index]["updated_at"] = datetime.now().isoformat()
            
            # If prompt or response changed, we need to regenerate embedding
            if 'original_prompt' in updated_feedback or 'original_response' in updated_feedback:
                # Remove old vector from index and add new one
                # For simplicity, we'll rebuild the entire index
                self._rebuild_index()
            else:
                # Just save the data
                self._save_index()
            
            logger.info(f"Updated feedback with ID: {feedback_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update feedback: {str(e)}")
            return False
    
    def delete_feedback(self, feedback_id: str) -> bool:
        """Delete feedback item"""
        try:
            # Find and remove the feedback item
            original_count = len(self.feedback_data)
            self.feedback_data = [f for f in self.feedback_data if f["id"] != feedback_id]
            
            if len(self.feedback_data) == original_count:
                logger.error(f"Feedback with ID {feedback_id} not found")
                return False
            
            # Rebuild index without the deleted item
            self._rebuild_index()
            
            logger.info(f"Deleted feedback with ID: {feedback_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete feedback: {str(e)}")
            return False
    
    def _rebuild_index(self):
        """Rebuild FAISS index from current feedback data"""
        try:
            if not self.feedback_data:
                self._create_new_index()
                return
            
            # Create new index
            new_index = faiss.IndexFlatL2(self.embedding_dimension)
            
            # Add all embeddings
            embeddings = []
            for feedback in self.feedback_data:
                text_for_embedding = f"{feedback['original_prompt']} {feedback['original_response']}"
                embedding = self.generate_embedding(text_for_embedding)
                if embedding:
                    embeddings.append(embedding)
                else:
                    logger.warning(f"Failed to generate embedding for feedback {feedback['id']}")
            
            if embeddings:
                embeddings_array = np.array(embeddings, dtype=np.float32)
                new_index.add(embeddings_array)
            
            self.index = new_index
            self._save_index()
            
            logger.info("Rebuilt FAISS index")
            
        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored feedback"""
        try:
            stats = {
                "total_feedback": len(self.feedback_data),
                "total_vectors": self.index.ntotal if self.index else 0,
                "helpful_feedback": len([f for f in self.feedback_data if f.get("developer_feedback", {}).get("is_helpful", False)]),
                "unhelpful_feedback": len([f for f in self.feedback_data if not f.get("developer_feedback", {}).get("is_helpful", True)]),
                "unique_vendors": len(set(f.get("vendor_id") for f in self.feedback_data if f.get("vendor_id"))),
                "categories": {}
            }
            
            # Count by category
            for feedback in self.feedback_data:
                category = feedback.get("developer_feedback", {}).get("category", "uncategorized")
                stats["categories"][category] = stats["categories"].get(category, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {"error": str(e)}
    
    def generate_feedback_summary_for_prompt(self, similar_feedback: List[Dict[str, Any]]) -> str:
        """Generate a summary of relevant feedback for prompt injection"""
        if not similar_feedback:
            return ""
        
        feedback_parts = []
        
        for feedback in similar_feedback:
            dev_feedback = feedback.get("developer_feedback", {})
            
            if not dev_feedback.get("is_helpful", True):
                # Include correction if available
                correction = dev_feedback.get("correction")
                improvement = dev_feedback.get("improvement_suggestion")
                category = dev_feedback.get("category", "general")
                
                feedback_text = f"For {category} queries: "
                if correction:
                    feedback_text += correction
                if improvement:
                    feedback_text += f" {improvement}"
                
                feedback_parts.append(feedback_text)
        
        if feedback_parts:
            return f"Reference Feedback:\n\"\"\"\n{' '.join(feedback_parts[:3])}\n\"\"\""  # Limit to top 3
        
        return ""
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the vector store connection"""
        if not self.index:
            return {
                "status": "error",
                "message": "FAISS index not initialized",
                "faiss_available": FAISS_AVAILABLE,
                "gemini_available": GEMINI_EMBEDDING_AVAILABLE
            }
        
        try:
            index_exists = os.path.exists(self.index_path)
            data_exists = os.path.exists(self.data_path)
            
            return {
                "status": "healthy",
                "faiss_available": True,
                "gemini_available": GEMINI_EMBEDDING_AVAILABLE,
                "index_exists": index_exists,
                "data_exists": data_exists,
                "total_vectors": self.index.ntotal,
                "similarity_threshold": self.similarity_threshold
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "faiss_available": FAISS_AVAILABLE,
                "gemini_available": GEMINI_EMBEDDING_AVAILABLE
            }


# Global instance
feedback_store = FeedbackVectorStore()
