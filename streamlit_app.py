#!/usr/bin/env python3
"""
Streamlit UI for Family Office RAG Pipeline
=============================================
Web interface for querying Family Office investor intelligence.
Features:
- Chat history with delete capability
- Redis caching for redundant queries
- Clickable suggested queries
"""

import streamlit as st
import json
import sys
import os
import hashlib
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from task2_rag.investor_rag import RAGPipeline, load_family_office_data

# Try to import Redis for caching
REDIS_AVAILABLE = False
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    pass

# Page config
st.set_page_config(
    page_title="Family Office Intelligence",
    page_icon="🏦",
    layout="wide"
)

# Redis connection
@st.cache_resource
def get_redis_client():
    if not REDIS_AVAILABLE:
        return None
    try:
        client = redis.Redis(host='localhost', port=6379, db=0)
        client.ping()
        return client
    except:
        return None

redis_client = get_redis_client()

# Cache query results in Redis
def cache_get(query: str):
    """Get cached result for query"""
    if redis_client is None:
        return None
    key = f"fo_rag:{hashlib.md5(query.encode()).hexdigest()}"
    try:
        cached = redis_client.get(key)
        if cached:
            return json.loads(cached)
    except:
        pass
    return None

def cache_set(query: str, results: dict, ttl: int = 3600):
    """Cache query result"""
    if redis_client is None:
        return
    key = f"fo_rag:{hashlib.md5(query.encode()).hexdigest()}"
    try:
        redis_client.setex(key, ttl, json.dumps(results))
    except:
        pass

# Initialize pipeline
@st.cache_resource
def get_pipeline():
    return RAGPipeline(use_local=True)

pipeline = get_pipeline()

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Title
st.title("🏦 Family Office Investor Intelligence")
st.markdown("*Decision-grade data with semantic search*")

# Layout: Main content + Sidebar
col_main, col_side = st.columns([3, 1])

with col_side:
    st.header("📜 Chat History")
    
    # Show history
    if st.session_state.chat_history:
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            with st.container():
                # Truncate query for display
                display_query = chat['query'][:40] + "..." if len(chat['query']) > 40 else chat['query']
                col_btn, col_del = st.columns([4, 1])
                with col_btn:
                    if st.button(f"📋 {display_query}", key=f"chat_{i}", help=chat['query']):
                        # Re-run the query
                        st.session_state.active_query = chat['query']
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{i}"):
                        del st.session_state.chat_history[i]
                        st.rerun()
    else:
        st.caption("No queries yet")
    
    if st.button("Clear All History", type="secondary"):
        st.session_state.chat_history = []
        st.rerun()
    
    st.divider()
    
    # Filters
    st.header("🔧 Filters")
    aum_filter = st.multiselect(
        "AUM Range",
        options=["$10B+", "$5B-$10B", "$1B-$5B", "$500M-$1B"],
        default=["$10B+", "$5B-$10B", "$1B-$5B", "$500M-$1B"]
    )
    
    confidence_filter = st.multiselect(
        "Confidence",
        options=["High", "Medium", "Low"],
        default=["High", "Medium", "Low"]
    )

with col_main:
    # Stats
    data = load_family_office_data("task1_dataset/family_offices_decision_grade.json")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Family Offices", len(data))
    col2.metric("High Confidence", sum(1 for d in data if d.get("confidence_score") == "High"))
    col3.metric("Cached Queries", len(st.session_state.chat_history))
    
    st.divider()
    
    # Query input
    st.header("🔍 Search")
    
    # Check for active query from history click
    active_query = getattr(st.session_state, 'active_query', None)
    if active_query:
        query = active_query
        st.session_state.active_query = None  # Clear after use
    else:
        query = ""
    
    query = st.text_input(
        "Enter your query:",
        value=query,
        placeholder="e.g., 'venture capital AI technology' or 'sovereign wealth fund asia'",
        label_visibility="collapsed"
    )
    
    col_search, col_cache = st.columns([1, 1])
    with col_search:
        search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
    with col_cache:
        cache_status = "🟢 Redis Cache Active" if redis_client else "🔴 No Redis"
        st.caption(cache_status)
    
    # Process query
    if (search_clicked or query) and query:
        # Check cache first
        cached_result = cache_get(query)
        
        if cached_result:
            st.info("📦 Loaded from cache")
            results = cached_result
        else:
            with st.spinner("Searching..."):
                results = pipeline.answer_query(query, top_k=10)
            # Cache the result
            cache_set(query, results)
        
        # Add to history
        history_entry = {
            'query': query,
            'timestamp': datetime.now().strftime("%H:%M"),
            'num_results': results['num_results']
        }
        
        # Avoid duplicates
        if not any(h['query'] == query for h in st.session_state.chat_history):
            st.session_state.chat_history.insert(0, history_entry)
        
        st.subheader(f"Found {results['num_results']} results for: *{query}*")
        
        # Display results with filters
        for i, doc in enumerate(results["results"], 1):
            # Apply filters
            confidence = doc["metadata"].get("confidence_score", "N/A")
            if confidence_filter and confidence not in confidence_filter:
                continue
            
            aum = doc["metadata"].get("aum_estimate", "N/A")
            if aum_filter and aum not in aum_filter:
                continue
            
            with st.container():
                st.markdown(f"### {i}. {doc['title']}")
                
                col_a, col_b, col_c = st.columns(3)
                col_a.write(f"📍 **{doc['metadata'].get('location', 'N/A')}**")
                col_b.write(f"💰 **{aum}**")
                col_c.write(f"✅ {confidence}")
                
                st.write(f"**Focus:** {doc['metadata'].get('investment_focus', 'N/A')}")
                st.write(f"**Stage:** {doc['metadata'].get('stage', 'N/A')}")
                st.write(f"**Notable:** {doc['metadata'].get('notable_investments', 'N/A')}")
                
                # Sources
                sources = doc['metadata'].get('source_links', [])
                if sources:
                    st.markdown("**Sources:** " + " | ".join([f"[Link]({s})" for s in sources[:3]]))
                
                st.divider()
    
    # Sample queries
    st.header("💡 Suggested Queries")
    sample_queries = [
        ("AI & ML Venture Capital", "venture capital ai machine learning"),
        ("Sovereign Wealth Tech", "sovereign wealth fund technology"),
        ("US Buyout Funds", "private equity buyout united states"),
        ("Fintech Growth", "fintech investment growth stage"),
        ("Healthcare VC", "healthcare venture capital"),
        ("Real Estate Family Offices", "family office real estate"),
        ("Credit Hedge Funds", "hedge fund credit strategies"),
        ("European Tech", "european technology investment"),
    ]
    
    cols = st.columns(4)
    for i, (label, sq) in enumerate(sample_queries):
        with cols[i % 4]:
            if st.button(label, key=f"suggest_{i}", use_container_width=True):
                # Directly search when clicking suggested query
                st.session_state.active_query = sq
                st.rerun()

# Footer
st.divider()
st.caption("🏦 RAG + ChromaDB + Redis Cache | 48 Family Offices | Chat History: Delete or Re-run")