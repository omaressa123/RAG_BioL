
import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, List, Any, Tuple
import os

class ChromaStore:
    def __init__(self, collection_name: str = "biolens", persist_directory: str = None):
        """
        Initialize ChromaDB store with enhanced capabilities
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist the database
        """
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()
        
        self.collection_name = collection_name
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
        except:
            self.collection = self.client.create_collection(collection_name)
    
    def store_chunks(self, chunks: List[str], metadatas: List[Dict[str, Any]]) -> bool:
        """
        Store chunks with metadata in ChromaDB
        
        Args:
            chunks: List of text chunks
            metadatas: List of metadata dictionaries
            
        Returns:
            Success status
        """
        try:
            # Generate embeddings
            embeddings = self.model.encode(chunks).tolist()
            
            # Generate unique IDs
            ids = [f"{self.collection_name}_{i}_{hash(chunks[i]) % 1000000}" for i in range(len(chunks))]
            
            # Add to collection
            self.collection.add(
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            return True
            
        except Exception as e:
            print(f"Error storing chunks: {str(e)}")
            return False
    
    def semantic_search(self, query: str, n_results: int = 5, 
                       chunk_type_filter: str = None) -> Dict[str, Any]:
        """
        Perform semantic search with confidence scoring
        
        Args:
            query: Search query
            n_results: Number of results to return
            chunk_type_filter: Filter by chunk type (concept, question, application)
            
        Returns:
            Dictionary with results and confidence scores
        """
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query]).tolist()
            
            # Build where clause for filtering
            where_clause = {}
            if chunk_type_filter:
                where_clause["chunk_type"] = chunk_type_filter
            
            # Perform search
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Calculate confidence scores
            enhanced_results = self._calculate_confidence_scores(results, query)
            
            return enhanced_results
            
        except Exception as e:
            print(f"Error in semantic search: {str(e)}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]], "confidence": [[]]}
    
    def _calculate_confidence_scores(self, results: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Calculate confidence scores for search results
        
        Args:
            results: Raw ChromaDB results
            query: Original query
            
        Returns:
            Enhanced results with confidence scores
        """
        if not results["documents"][0]:
            return results
        
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        
        confidence_scores = []
        
        for i, (doc, distance, metadata) in enumerate(zip(documents, distances, metadatas)):
            # Convert distance to similarity score (0-1)
            similarity = 1 / (1 + distance)
            
            # Boost confidence based on chunk type relevance
            type_boost = self._get_type_boost(metadata.get("chunk_type", "concept"))
            
            # Boost confidence based on keyword overlap
            keyword_boost = self._calculate_keyword_boost(query, doc, metadata.get("keywords", []))
            
            # Calculate final confidence score
            confidence = min(0.95, similarity * type_boost * keyword_boost)
            confidence_scores.append(round(confidence, 3))
        
        results["confidence"] = [confidence_scores]
        return results
    
    def _get_type_boost(self, chunk_type: str) -> float:
        """
        Get confidence boost based on chunk type
        
        Args:
            chunk_type: Type of chunk
            
        Returns:
            Boost multiplier
        """
        boosts = {
            "question": 1.2,      # Questions often more relevant
            "application": 1.1,   # Applications also quite relevant
            "concept": 1.0        # Baseline
        }
        return boosts.get(chunk_type, 1.0)
    
    def _calculate_keyword_boost(self, query: str, document: str, keywords: List[str]) -> float:
        """
        Calculate confidence boost based on keyword overlap
        
        Args:
            query: Search query
            document: Retrieved document
            keywords: Document keywords
            
        Returns:
            Boost multiplier
        """
        query_lower = query.lower()
        doc_lower = document.lower()
        
        # Count keyword matches
        keyword_matches = sum(1 for keyword in keywords if keyword in query_lower)
        
        # Count direct term matches
        query_terms = set(query_lower.split())
        doc_terms = set(doc_lower.split())
        term_overlap = len(query_terms & doc_terms) / max(len(query_terms), 1)
        
        # Calculate boost
        keyword_boost = 1.0 + (keyword_matches * 0.1) + (term_overlap * 0.2)
        
        return min(1.5, keyword_boost)  # Cap at 1.5x boost
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection
        
        Returns:
            Collection statistics
        """
        try:
            count = self.collection.count()
            
            # Get sample of metadata to analyze distribution
            sample_results = self.collection.get(limit=100, include=["metadatas"])
            
            chunk_types = {}
            sources = {}
            
            for metadata in sample_results.get("metadatas", []):
                # Count chunk types
                chunk_type = metadata.get("chunk_type", "unknown")
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                
                # Count sources
                source = metadata.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1
            
            return {
                "total_chunks": count,
                "chunk_type_distribution": chunk_types,
                "source_distribution": sources,
                "collection_name": self.collection_name
            }
            
        except Exception as e:
            print(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}
    
    def delete_collection(self) -> bool:
        """
        Delete the current collection
        
        Returns:
            Success status
        """
        try:
            self.client.delete_collection(self.collection_name)
            return True
        except Exception as e:
            print(f"Error deleting collection: {str(e)}")
            return False

# Global instance for backward compatibility
_store = None

def get_store():
    """Get or create global store instance"""
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store

def store_chunks(chunks, metadatas):
    """Backward compatibility function"""
    return get_store().store_chunks(chunks, metadatas)

def search(query, n_results=3):
    """Backward compatibility function"""
    return get_store().semantic_search(query, n_results)
