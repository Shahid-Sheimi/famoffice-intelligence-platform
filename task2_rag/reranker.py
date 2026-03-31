#!/usr/bin/env python3
"""
Re-Ranker Module for RAG Pipeline
================================
Simple reranking based on keyword matching and confidence scoring.
Can be extended to use cross-encoders for better semantic matching.
"""

import logging
from typing import List, Dict, Any, Tuple
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def keyword_rerank(query: str, documents: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Re-rank documents based on keyword matching with query.
    More strict matching - requires query terms to appear in relevant fields.
    
    Args:
        query: Original search query
        documents: List of document dicts from initial retrieval
        top_k: Number of results to return
        
    Returns:
        Re-ranked list of documents with relevance scores
    """
    logger.info(f"[KEYWORD_RERANK] Starting with query: '{query}', documents: {len(documents)}, top_k: {top_k}")
    query_terms = query.lower().split()
    # Filter to meaningful terms (length > 2)
    query_terms = [t for t in query_terms if len(t) > 2]
    
    # Extract key query intent words
    focus_terms = [t for t in query_terms if t in ['technology', 'ai', 'venture', 'capital', 
        'healthcare', 'finance', 'biotech', 'crypto', 'blockchain', 'software', 'energy',
        'realestate', 'property', 'private', 'equity', 'growth', 'early', 'stage', 'Series',
        'seed', 'fund', 'investment', 'family', 'office', 'sovereign', 'wealth', 'fund']]
    location_terms = [t for t in query_terms if t in ['asia', 'europe', 'usa', 'us', 'uk', 'china', 
        'india', 'singapore', 'japan', 'dubai', 'middle', 'east', 'america', 'north', 'south']]
    
    reranked = []
    for doc in documents:
        # Get all relevant text from document
        title = doc.get('title', '').lower()
        metadata = doc.get('metadata', {})
        focus = metadata.get('investment_focus', '').lower()
        stage = metadata.get('stage', '').lower()
        location = metadata.get('location', '').lower()
        aum = metadata.get('aum_estimate', '').lower()
        
        # Combine all relevant text
        combined = f"{title} {focus} {stage} {location} {aum}"
        
        # Check for mandatory focus term matches (if any focus terms in query)
        focus_score = 0
        if focus_terms:
            focus_matches = sum(1 for term in focus_terms if term in combined)
            focus_score = focus_matches / len(focus_terms)
            # If no focus matches, heavily penalize (but don't exclude yet)
            if focus_matches == 0:
                focus_score = -0.5
        
        # Check for location matches (if any location terms in query)
        location_score = 0
        if location_terms:
            location_matches = sum(1 for term in location_terms if term in location)
            location_score = location_matches / len(location_terms)
            # If location specified but no match, heavily penalize
            if location_matches == 0 and any(term in combined for term in location_terms):
                location_score = -0.3
        
        # Overall keyword match score
        keyword_matches = sum(1 for term in query_terms if term in combined)
        keyword_score = keyword_matches / max(len(query_terms), 1)
        
        # Get confidence score (boost high confidence)
        confidence = metadata.get('confidence_score', 'Medium')
        confidence_map = {'High': 1.0, 'Medium': 0.5, 'Low': 0.25, 'N/A': 0.0}
        confidence_score = confidence_map.get(confidence, 0.0)
        
        # Combined score - weight keyword matching heavily
        # Prioritize exact matches on focus terms
        final_score = (keyword_score * 0.5) + (focus_score * 0.3) + (confidence_score * 0.2)
        
        reranked.append({
            **doc,
            'rerank_score': final_score,
            'keyword_matches': keyword_matches,
            'focus_score': focus_score
        })
    
    # Sort by rerank score descending
    reranked.sort(key=lambda x: x['rerank_score'], reverse=True)
    
    # Only return results with positive scores (relevant to query)
    relevant_results = [r for r in reranked if r['rerank_score'] > 0]
    
    logger.info(f"[KEYWORD_RERANK] Returning {len(relevant_results[:top_k])} results from {len(reranked)} candidates")
    return relevant_results[:top_k]


def semantic_rerank(query: str, documents: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Re-rank documents using semantic similarity.
    Falls back to keyword if sentence-transformers not available.
    
    Args:
        query: Original search query  
        documents: List of document dicts from initial retrieval
        top_k: Number of results to return
        
    Returns:
        Re-ranked list of documents with relevance scores
    """
    logger.info(f"[SEMANTIC_RERANK] Starting with query: '{query}', documents: {len(documents)}, top_k: {top_k}")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # Get texts to rerank
        texts = [query] * len(documents)
        doc_texts = [
            f"{d.get('title', '')} {d.get('metadata', {}).get('investment_focus', '')}"
            for d in documents
        ]
        
        # Get cross-encoder scores
        scores = model.predict(texts, doc_texts)
        
        # Combine with original rerank_score if exists
        reranked = []
        for i, doc in enumerate(documents):
            original_score = doc.get('rerank_score', 0.0)
            semantic_score = float(scores[i])
            # Blend scores: 50% original, 50% semantic
            final_score = (original_score * 0.5) + (semantic_score * 0.5)
            
            reranked.append({
                **doc,
                'rerank_score': final_score,
                'semantic_score': semantic_score
            })
        
        reranked.sort(key=lambda x: x['rerank_score'], reverse=True)
        return reranked[:top_k]
        
    except (ImportError, Exception) as e:
        logger.warning(f"[SEMANTIC_RERANK] Semantic reranking unavailable ({e}), falling back to keyword reranking")
        return keyword_rerank(query, documents, top_k)
    
    logger.info(f"[SEMANTIC_RERANK] Returning {len(reranked[:top_k])} results")


def apply_reranking(
    query: str, 
    documents: List[Dict[str, Any]], 
    method: str = 'keyword',
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Apply reranking to document results.
    
    Args:
        query: Search query
        documents: Initial retrieved documents
        method: 'keyword', 'semantic', or 'hybrid'
        top_k: Number of results to return
        
    Returns:
        Re-ranked documents
    """
    logger.info(f"[APPLY_RERANK] Starting with method: '{method}', query: '{query}', documents: {len(documents)}")
    if not documents:
        logger.warning("[APPLY_RERANK] No documents provided, returning empty list")
        return []
    
    if method == 'semantic':
        logger.info("[APPLY_RERANK] Using semantic method")
        return semantic_rerank(query, documents, top_k)
    elif method == 'hybrid':
        logger.info("[APPLY_RERANK] Using hybrid method (keyword + semantic)")
        # First keyword rerank, then semantic refine
        kw_reranked = keyword_rerank(query, documents, top_k * 2)
        return semantic_rerank(query, kw_reranked, top_k)
    else:
        logger.info("[APPLY_RERANK] Using keyword method")
        return keyword_rerank(query, documents, top_k)


if __name__ == "__main__":
    # Test reranker
    test_docs = [
        {"title": "Sequoia Capital", "metadata": {"investment_focus": "technology venture", "confidence_score": "High"}},
        {"title": "Andreessen Horowitz", "metadata": {"investment_focus": "software AI", "confidence_score": "High"}},
        {"title": "Goldman Sachs", "metadata": {"investment_focus": "financial services", "confidence_score": "Medium"}},
    ]
    
    results = apply_reranking("AI technology venture", test_docs, method='keyword')
    
    print("Re-Ranking Test:")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']} - Score: {r.get('rerank_score', 0):.2f}")