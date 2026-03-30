#!/usr/bin/env python3
"""
Task 2: RAG Pipeline for Investor Intelligence
==========================================
Production-grade RAG system for family office investor queries.
Connects to actual Family Office dataset from Task 1.

Features:
- Document ingestion and chunking
- Embedding model selection (Gemini or local sentence-transformers)
- ChromaDB vector store
- Hybrid retrieval (semantic + BM25)
- Query evaluation with actual FO data
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try to import optional dependencies
CHROMADB_AVAILABLE = False
GEMINI_AVAILABLE = False
SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    pass

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    pass

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    pass


def load_family_office_data(json_path: str = "task1_dataset/family_offices_decision_grade.json") -> List[Dict[str, Any]]:
    """
    Load Family Office data from JSON file for RAG ingestion.
    
    Args:
        json_path: Path to the JSON file containing FO data
        
    Returns:
        List of document dictionaries ready for ingestion
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        for i, fo in enumerate(data):
            # Create rich text content for embedding
            content = f"""
            Family Office: {fo.get('name', 'Unknown')}
            Location: {fo.get('location', 'Unknown')}
            AUM Estimate: {fo.get('aum_estimate', 'Unknown')}
            Investment Focus: {fo.get('investment_focus', 'Unknown')}
            Stage Preference: {fo.get('stage', 'Unknown')}
            Notable Investments: {fo.get('notable_investments', 'Unknown')}
            Confidence Score: {fo.get('confidence_score', 'Unknown')}
            Sources: {', '.join(fo.get('source_links', []))}
            """.strip()
            
            doc = {
                "id": f"fo_{i+1:03d}",
                "title": fo.get('name', 'Unknown Family Office'),
                "content": content,
                "metadata": {
                    "type": "family_office",
                    "name": fo.get('name', ''),
                    "location": fo.get('location', ''),
                    "aum_estimate": fo.get('aum_estimate', ''),
                    "investment_focus": fo.get('investment_focus', ''),
                    "stage": fo.get('stage', ''),
                    "confidence_score": fo.get('confidence_score', ''),
                    "source_links": fo.get('source_links', [])
                }
            }
            documents.append(doc)
        
        print(f"Loaded {len(documents)} Family Office documents from {json_path}")
        return documents
        
    except FileNotFoundError:
        print(f"Warning: {json_path} not found. Using sample data.")
        return SAMPLE_DOCUMENTS
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}. Using sample data.")
        return SAMPLE_DOCUMENTS


class ChunkingStrategy:
    """
    Chunking strategies for different document types.
    """
    
    @staticmethod
    def fixed_size(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Fixed-size chunking with overlap"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    @staticmethod
    def by_paragraph(text: str) -> List[str]:
        """Split by paragraphs"""
        paragraphs = text.split("\n\n")
        return [p.strip() for p in paragraphs if p.strip()]
    
    @staticmethod
    def semantic(text: str, max_chunk_size: int = 500) -> List[str]:
        """
        Semantic chunking - split at natural boundaries.
        This is a simplified version; production would use NLP.
        """
        sentences = text.split(". ")
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chunk_size:
                current_chunk += ". " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks


class EmbeddingModel:
    """
    Embedding model supporting multiple backends:
    1. Google Gemini API (uses free tier)
    2. Local sentence-transformers (all-MiniLM-L6-v2)
    """
    
    def __init__(self, model_name: str = "gemini-embedding-001", use_local: bool = False):
        self.model_name = model_name
        self.use_local = use_local
        self.gemini_client = None
        self.local_model = None
        
        # Try to initialize available backends
        if use_local and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
                print(f"Initialized local embedding model: all-MiniLM-L6-v2")
                return
            except Exception as e:
                print(f"Warning: Could not load local model: {e}")
        
        # Fall back to Gemini
        if GEMINI_AVAILABLE:
            try:
                self.gemini_client = genai.Client(
                    api_key=os.environ.get("GOOGLE_API_KEY")
                )
                print(f"Initialized Gemini embedding model: {model_name}")
            except Exception as e:
                print(f"Warning: Could not initialize Gemini: {e}")
        
        if not self.gemini_client and not self.local_model:
            print("Warning: No embedding model available, using mock embeddings")
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        """
        if self.local_model:
            return self.local_model.encode(texts).tolist()
        
        if self.gemini_client:
            embeddings = []
            for text in texts:
                try:
                    result = self.gemini_client.models.embed_content(
                        model=self.model_name,
                        contents=text
                    )
                    if result.embeddings and len(result.embeddings) > 0:
                        embeddings.append(list(result.embeddings[0].values))
                    else:
                        embeddings.append([0.1] * 768)
                except Exception as e:
                    print(f"Error embedding text: {e}")
                    embeddings.append([0.1] * 768)
            return embeddings
        
        # Fallback mock embeddings
        return [[0.1] * 768 for _ in texts]
    
    def encode_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query string.
        """
        if self.local_model:
            return self.local_model.encode([query])[0].tolist()
        
        if self.gemini_client:
            try:
                result = self.gemini_client.models.embed_content(
                    model=self.model_name,
                    contents=query
                )
                if result.embeddings and len(result.embeddings) > 0:
                    return list(result.embeddings[0].values)
                return [0.1] * 768
            except Exception as e:
                print(f"Error embedding query: {e}")
                return [0.1] * 768
        
        return [0.1] * 768


class VectorStore:
    """
    Vector store for RAG using ChromaDB.
    """
    
    def __init__(self, collection_name: str = "investor_intelligence", persist_dir: str = "./chroma_db"):
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        self.client = None
        self.collection = None
        
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(path=persist_dir)
                self.collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"description": "Investor intelligence RAG system"}
                )
                print(f"Initialized vector store: {collection_name}")
            except Exception as e:
                print(f"Warning: Could not initialize ChromaDB: {e}")
    
    def clear(self) -> None:
        """Clear the collection"""
        if self.collection:
            try:
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "Investor intelligence RAG system"}
                )
                print(f"Cleared collection: {self.collection_name}")
            except Exception as e:
                print(f"Error clearing collection: {e}")
    
    def add_documents(
        self, 
        documents: List[Dict[str, Any]], 
        embeddings: List[List[float]]
    ) -> None:
        """Add documents to the vector store"""
        if self.collection is None:
            print("Warning: Vector store not available")
            return
        
        ids = [doc["id"] for doc in documents]
        texts = [doc["content"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        
        try:
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            print(f"Added {len(documents)} documents to vector store")
        except Exception as e:
            print(f"Error adding documents: {e}")
    
    def search(
        self, 
        query_embedding: List[float], 
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if self.collection is None:
            return []
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            formatted = []
            for i in range(len(results["ids"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else 0,
                    "metadata": results["metadatas"][0][i] if "metadatas" in results else {}
                })
            
            return formatted
        except Exception as e:
            print(f"Error searching: {e}")
            return []


class BM25Retriever:
    """
    BM25 keyword-based retrieval.
    Simple implementation for hybrid search.
    """
    
    def __init__(self, documents: List[Dict[str, Any]]):
        self.documents = documents
        self.index = self._build_index()
    
    def _build_index(self) -> Dict[str, List[int]]:
        """Build simple inverted index"""
        index = {}
        
        for i, doc in enumerate(self.documents):
            # Tokenize content
            words = doc["content"].lower().split()
            words.extend(doc["title"].lower().split())
            
            for word in words:
                if word not in index:
                    index[word] = []
                if i not in index[word]:
                    index[word].append(i)
        
        return index
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search using keyword matching"""
        query_words = query.lower().split()
        scores = {}
        
        for word in query_words:
            if word in self.index:
                for doc_idx in self.index[word]:
                    scores[doc_idx] = scores.get(doc_idx, 0) + 1
        
        # Sort by score
        sorted_idx = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_idx, score in sorted_idx[:top_k]:
            results.append({
                "id": self.documents[doc_idx]["id"],
                "document": self.documents[doc_idx]["content"],
                "score": score,
                "metadata": self.documents[doc_idx].get("metadata", {}),
                "method": "bm25"
            })
        
        return results


class RAGPipeline:
    """
    Complete RAG pipeline for investor intelligence.
    """
    
    def __init__(self, data_path: str = "task1_dataset/family_offices_decision_grade.json", use_local: bool = True):
        self.data_path = data_path
        self.chunking_strategy = ChunkingStrategy()
        
        # Use local model by default (free, no API key needed)
        self.embedding_model = EmbeddingModel("gemini-embedding-001", use_local=use_local)
        self.vector_store = VectorStore()
        
        # Load actual FO data
        self.documents = load_family_office_data(data_path)
        
        # Build BM25 index
        self.bm25 = BM25Retriever(self.documents)
    
    def ingest(self, clear_first: bool = True) -> None:
        """Ingest and process documents"""
        if clear_first and self.vector_store.collection:
            self.vector_store.clear()
        
        # Generate embeddings
        all_content = [doc["content"] for doc in self.documents]
        embeddings = self.embedding_model.encode(all_content)
        
        # Add to vector store
        if self.vector_store.collection:
            self.vector_store.add_documents(self.documents, embeddings)
        
        print(f"Ingested {len(self.documents)} documents")
    
    def hybrid_search(
        self, 
        query: str, 
        alpha: float = 0.7,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword retrieval.
        
        Args:
            query: Search query
            alpha: Weight for semantic search (1-alpha for BM25)
            top_k: Number of results
        """
        # Semantic search
        query_embedding = self.embedding_model.encode_query(query)
        semantic_results = self.vector_store.search(query_embedding, n_results=top_k)
        
        # BM25 search
        bm25_results = self.bm25.search(query, top_k=top_k)
        
        # Combine results
        combined = {}
        
        for result in semantic_results:
            doc_id = result["id"]
            combined[doc_id] = {
                "id": doc_id,
                "title": result["metadata"].get("name", "Unknown"),
                "document": result["document"],
                "semantic_score": 1 - result.get("distance", 0),
                "bm25_score": 0,
                "metadata": result.get("metadata", {}),
                "method": "semantic"
            }
        
        for result in bm25_results:
            doc_id = result["id"]
            if doc_id in combined:
                combined[doc_id]["bm25_score"] = result["score"]
                combined[doc_id]["method"] = "hybrid"
            else:
                combined[doc_id] = {
                    "id": doc_id,
                    "title": result["metadata"].get("name", "Unknown"),
                    "document": result["document"],
                    "semantic_score": 0,
                    "bm25_score": result["score"],
                    "metadata": result.get("metadata", {}),
                    "method": "bm25"
                }
        
        # Calculate combined scores
        for doc_id in combined:
            doc = combined[doc_id]
            semantic_norm = doc["semantic_score"] * alpha
            bm25_norm = (doc["bm25_score"] / 10) * (1 - alpha)  # Normalize BM25
            doc["combined_score"] = semantic_norm + bm25_norm
        
        # Sort by combined score
        results = sorted(
            combined.values(), 
            key=lambda x: x["combined_score"], 
            reverse=True
        )[:top_k]
        
        return results
    
    def answer_query(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Answer a query using the RAG system.
        """
        results = self.hybrid_search(query, top_k=top_k)
        
        return {
            "query": query,
            "results": results,
            "num_results": len(results)
        }


# Sample documents for fallback
SAMPLE_DOCUMENTS = [
    {
        "id": "doc_001",
        "title": "Rockefeller Capital Overview",
        "content": """Rockefeller Capital is a multi-family office based in New York City.
        Founded in 2020, they manage between $5B-$10B in assets under management.
        Their investment strategy includes direct investments in private equity and venture capital,
        as well as fund allocations. They focus on technology, healthcare, and financial services sectors.""",
        "metadata": {
            "type": "family_office",
            "country": "US",
            "city": "New York",
            "aum_range": "$5B-$10B",
            "source": "SEC EDGAR"
        }
    },
    {
        "id": "doc_002", 
        "title": "Bessemer Trust Investment Approach",
        "content": """Bessemer Trust, founded in 1900, is one of the oldest multi-family offices
        in the United States with over $10B in assets under management. Based in San Francisco,
        they offer comprehensive wealth management services including brokerage, estate planning,
        and investment management. Their investment approach focuses on equities, fixed income,
        and alternative investments.""",
        "metadata": {
            "type": "family_office",
            "country": "US",
            "city": "San Francisco", 
            "aum_range": "$10B+",
            "source": "SEC EDGAR"
        }
    }
]


def test_queries(pipeline: RAGPipeline):
    """Test the RAG pipeline with sample queries"""
    
    # Suggested queries
    suggested_queries = [
        "family office venture capital",
        "sovereign wealth fund technology",
        "hedge fund credit strategies",
        "private equity buyout",
        "fintech investment"
    ]

    print("\n" + "=" * 60)
    print("Testing RAG Pipeline with Sample Queries")
    print("=" * 60)
    
    for query in suggested_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        result = pipeline.answer_query(query)
        
        for i, doc in enumerate(result["results"], 1):
            print(f"  {i}. [{doc['method'].upper()}] {doc['title']}")
            print(f"     Score: {doc['combined_score']:.3f}")
            print(f"     Location: {doc['metadata'].get('location', 'N/A')}")
            print(f"     AUM: {doc['metadata'].get('aum_estimate', 'N/A')}")


def interactive_mode(pipeline: RAGPipeline):
    """Interactive query mode"""
    print("\n" + "=" * 60)
    print("Interactive RAG Query Mode")
    print("=" * 60)
    print("Enter your queries below (or 'quit' to exit)")
    
    while True:
        query = input("\nQuery: ").strip()
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not query:
            continue
        
        result = pipeline.answer_query(query)
        print(f"\nFound {result['num_results']} results:")
        
        for i, doc in enumerate(result["results"], 1):
            print(f"\n  {i}. {doc['title']}")
            print(f"     Confidence: {doc['metadata'].get('confidence_score', 'N/A')}")
            print(f"     Location: {doc['metadata'].get('location', 'N/A')}")
            print(f"     AUM: {doc['metadata'].get('aum_estimate', 'N/A')}")
            print(f"     Investment Focus: {doc['metadata'].get('investment_focus', 'N/A')}")


def main():
    """Main execution"""
    print("=" * 60)
    print("Task 2: RAG Pipeline for Investor Intelligence")
    print("=" * 60)
    
    # Check dependencies
    print("\nDependency Check:")
    print(f"  ChromaDB: {'Available' if CHROMADB_AVAILABLE else 'Not available'}")
    print(f"  Gemini API: {'Available' if GEMINI_AVAILABLE else 'Not available'}")
    print(f"  Sentence-Transformers: {'Available' if SENTENCE_TRANSFORMERS_AVAILABLE else 'Not available'}")
    
    # Create pipeline
    # Use local embeddings if available (free, no API key)
    use_local = SENTENCE_TRANSFORMERS_AVAILABLE
    pipeline = RAGPipeline(use_local=use_local)
    
    # Ingest documents
    pipeline.ingest()
    
    # Test with sample queries
    test_queries(pipeline)
    
    # Interactive mode
    mode = input("\nRun interactive mode? (y/n): ").strip().lower()
    if mode == 'y':
        interactive_mode(pipeline)
    
    print("\n" + "=" * 60)
    print("RAG Pipeline Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()