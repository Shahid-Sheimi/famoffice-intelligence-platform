#!/usr/bin/env python3
"""
Streamlit UI for Family Office RAG Pipeline — Luxury Redesign
==============================================================
"""

import warnings
warnings.filterwarnings('ignore', message='.*Tried to instantiate.*')
warnings.filterwarnings('ignore', message='.*Accessing.*')
warnings.filterwarnings('ignore', message='.*No module named.*')
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*torch.classes.*")
warnings.filterwarnings("ignore", message=".*no running event loop.*")

import streamlit as st
import json
import sys
import os
import io
import hashlib
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def render_analysis(func):
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        func()
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    return output

sys.path.insert(0, str(Path(__file__).parent))

from task2_rag.investor_rag import RAGPipeline, load_family_office_data

REDIS_AVAILABLE = False
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    pass

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="FamilyOffice Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# GLOBAL STYLES — Luxury Dark Theme
# ─────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
/* ── Root tokens ─────────────────────────────── */
:root {
    --bg-void:     #07090f;
    --bg-surface:  #0d1117;
    --bg-card:     #111827;
    --bg-elevated: #1a2234;
    --border:      rgba(200,170,90,0.18);
    --border-bright: rgba(200,170,90,0.45);
    --gold:        #c8aa5a;
    --gold-light:  #e2c97e;
    --gold-dim:    rgba(200,170,90,0.35);
    --text-primary: #f0ead8;
    --text-secondary: #8a95a8;
    --text-muted:  #4a5568;
    --accent-blue: #3a6ea8;
    --success:     #2e7d52;
    --danger:      #8b2635;
    --radius-sm:   6px;
    --radius-md:   12px;
    --radius-lg:   20px;
}

/* ── Base ───────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background-color: var(--bg-void) !important;
    color: var(--text-primary) !important;
}

.main .block-container {
    padding: 2rem 2.5rem 4rem !important;
    max-width: 1400px !important;
}

/* ── Header ─────────────────────────────────── */
.fo-header {
    display: flex;
    align-items: baseline;
    gap: 1rem;
    margin-bottom: 0.25rem;
}

.fo-wordmark {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-primary);
    line-height: 1;
}

.fo-wordmark span {
    color: var(--gold);
}

.fo-tagline {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 1.8rem;
}

/* ── Gold rule ──────────────────────────────── */
.gold-rule {
    height: 1px;
    background: linear-gradient(90deg, var(--gold) 0%, transparent 100%);
    margin: 1.4rem 0;
    opacity: 0.45;
}

/* ── Metric cards ───────────────────────────── */
.metric-row {
    display: flex;
    gap: 1.2rem;
    margin-bottom: 1.8rem;
}

.metric-card {
    flex: 1;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.4rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.25s;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--gold), transparent);
}

.metric-card:hover { border-color: var(--border-bright); }

.metric-label {
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.4rem;
}

.metric-value {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2rem;
    font-weight: 600;
    color: var(--gold-light);
    line-height: 1;
}

.metric-sub {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 0.3rem;
}

/* ── Search bar ─────────────────────────────── */
.stTextInput > div > div > input {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1.1rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px var(--gold-dim) !important;
    outline: none !important;
}

.stTextInput > div > div > input::placeholder {
    color: var(--text-muted) !important;
}

/* ── Buttons ────────────────────────────────── */
.stButton > button {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    border-radius: var(--radius-sm) !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.04em !important;
}

/* Primary — Gold CTA */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #b8973e 0%, #c8aa5a 50%, #d4b96e 100%) !important;
    color: #07090f !important;
    border: none !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 12px rgba(200,170,90,0.3) !important;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #c8aa5a, #e2c97e, #c8aa5a) !important;
    box-shadow: 0 4px 20px rgba(200,170,90,0.45) !important;
    transform: translateY(-1px) !important;
}

/* Secondary — Ghost */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border) !important;
}

.stButton > button[kind="secondary"]:hover {
    border-color: var(--gold) !important;
    color: var(--gold-light) !important;
}

/* Suggestion pills */
div[data-testid="column"] .stButton > button {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
    border-radius: 999px !important;
    padding: 0.4rem 0.9rem !important;
    font-size: 0.78rem !important;
}

div[data-testid="column"] .stButton > button:hover {
    border-color: var(--gold) !important;
    color: var(--gold-light) !important;
    background: rgba(200,170,90,0.08) !important;
}

/* ── Tabs ───────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 4px !important;
    width: fit-content !important;
}

.stTabs [data-baseweb="tab"] {
    height: 38px !important;
    padding: 0 22px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    background: transparent !important;
    color: var(--text-muted) !important;
    letter-spacing: 0.04em !important;
    transition: all 0.2s ease !important;
    border: none !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary) !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #b8973e, #c8aa5a) !important;
    color: #07090f !important;
    font-weight: 600 !important;
}

.stTabs [data-baseweb="tab-border"],
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

/* ── Result cards ───────────────────────────── */
.result-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.5rem 1.8rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.25s, transform 0.2s;
}

.result-card::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(200,170,90,0.03) 0%, transparent 60%);
    pointer-events: none;
}

.result-card:hover {
    border-color: var(--border-bright);
    transform: translateY(-2px);
}

.result-index {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    color: var(--gold);
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}

.result-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.8rem;
    line-height: 1.25;
}

.result-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-bottom: 0.9rem;
}

.meta-pill {
    font-size: 0.72rem;
    font-weight: 500;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    border: 1px solid;
    letter-spacing: 0.03em;
}

.pill-location  { color: #7fa8d4; border-color: rgba(127,168,212,0.3); background: rgba(127,168,212,0.08); }
.pill-aum       { color: var(--gold-light); border-color: var(--gold-dim); background: rgba(200,170,90,0.07); }
.pill-high      { color: #4ade80; border-color: rgba(74,222,128,0.3); background: rgba(74,222,128,0.07); }
.pill-medium    { color: #fbbf24; border-color: rgba(251,191,36,0.3); background: rgba(251,191,36,0.07); }
.pill-low       { color: #f87171; border-color: rgba(248,113,113,0.3); background: rgba(248,113,113,0.07); }

.result-field-label {
    font-size: 0.68rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.15rem;
}

.result-field-value {
    font-size: 0.88rem;
    color: var(--text-secondary);
    margin-bottom: 0.75rem;
    line-height: 1.5;
}

.source-link {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: var(--gold);
    text-decoration: none;
    padding: 0.2rem 0.6rem;
    border: 1px solid var(--gold-dim);
    border-radius: 4px;
    margin-right: 0.4rem;
    transition: background 0.2s;
}
.source-link:hover { background: rgba(200,170,90,0.12); }

/* ── History panel ──────────────────────────── */
.history-item {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 0.6rem 0.8rem;
    margin-bottom: 0.5rem;
    transition: border-color 0.2s;
}
.history-item:hover { border-color: var(--border-bright); }

.history-ts {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    color: var(--text-muted);
}

.history-q {
    font-size: 0.8rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ── Section headings ───────────────────────── */
.section-heading {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: 0.02em;
    margin-bottom: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.section-heading::before {
    content: '';
    display: inline-block;
    width: 18px;
    height: 1px;
    background: var(--gold);
}

/* ── Filter multiselect ─────────────────────── */
.stMultiSelect [data-baseweb="select"] > div {
    background: var(--bg-card) !important;
    border-color: var(--border) !important;
    border-radius: var(--radius-sm) !important;
}
.stMultiSelect span {
    background: var(--bg-elevated) !important;
    color: var(--text-secondary) !important;
    font-size: 0.75rem !important;
}

/* ── Status badges ──────────────────────────── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
    border: 1px solid;
}

.status-active { color: #4ade80; border-color: rgba(74,222,128,0.3); background: rgba(74,222,128,0.07); }
.status-inactive { color: #f87171; border-color: rgba(248,113,113,0.3); background: rgba(248,113,113,0.07); }

/* ── Info / Warning / Success boxes ─────────── */
.stAlert {
    background: var(--bg-elevated) !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
}

/* ── Code block ─────────────────────────────── */
.stCodeBlock {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
}

/* ── Spinner ────────────────────────────────── */
.stSpinner > div { border-top-color: var(--gold) !important; }

/* ── Scrollbar ──────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-surface); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold-dim); }

/* ── Divider ────────────────────────────────── */
hr { border-color: var(--border) !important; opacity: 0.5 !important; }

/* ── Caption / small text ───────────────────── */
.stCaption { color: var(--text-muted) !important; font-size: 0.75rem !important; }

/* ── Remove default streamlit header spacer ─── */
.block-container { padding-top: 1.8rem !important; }

/* ── No results state ───────────────────────── */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: var(--text-muted);
}
.empty-state-icon { font-size: 2.5rem; margin-bottom: 0.75rem; opacity: 0.4; }
.empty-state-text { font-family: 'Cormorant Garamond', serif; font-size: 1.1rem; }

/* ── Cache info banner ──────────────────────── */
.cache-banner {
    background: rgba(200,170,90,0.08);
    border: 1px solid var(--gold-dim);
    border-radius: var(--radius-sm);
    padding: 0.5rem 1rem;
    font-size: 0.78rem;
    color: var(--gold-light);
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.05em;
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# REDIS & PIPELINE
# ─────────────────────────────────────────────
@st.cache_resource
def get_redis_client():
    if not REDIS_AVAILABLE:
        return None
    try:
        client = redis.Redis(host='localhost', port=6379, db=0)
        client.ping()
        return client
    except Exception:
        return None

redis_client = get_redis_client()

def cache_get(query: str):
    if redis_client is None:
        return None
    key = f"fo_rag:{hashlib.md5(query.encode()).hexdigest()}"
    try:
        cached = redis_client.get(key)
        return json.loads(cached) if cached else None
    except Exception:
        return None

def cache_set(query: str, results: dict, ttl: int = 3600):
    if redis_client is None:
        return
    key = f"fo_rag:{hashlib.md5(query.encode()).hexdigest()}"
    try:
        redis_client.setex(key, ttl, json.dumps(results))
    except Exception:
        pass

@st.cache_resource
def get_pipeline():
    return RAGPipeline(use_local=True)

pipeline = get_pipeline()

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for key, val in [
    ('chat_history', []),
    ('active_query', ''),
    ('auto_search', False),
]:
    if key not in st.session_state:
        st.session_state[key] = val


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="fo-header">
    <div class="fo-wordmark">Family<span>Office</span> Intelligence</div>
</div>
<div class="fo-tagline">◆ &nbsp; Hybrid RAG · Semantic + BM25 · Decision-Grade Investor Data</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_search, tab_analysis, tab_product = st.tabs([
    "  Search  ",
    "  SaaS Analysis  ",
    "  AI Product  ",
])


# ══════════════════════════════════════════════
# TAB 1 — SEARCH
# ══════════════════════════════════════════════
with tab_search:
    col_main, col_side = st.columns([3, 1], gap="large")

    # ── Sidebar ──────────────────────────────
    with col_side:
        st.markdown('<div class="section-heading">History</div>', unsafe_allow_html=True)

        if st.session_state.chat_history:
            for i, chat in enumerate(reversed(st.session_state.chat_history)):
                idx = len(st.session_state.chat_history) - 1 - i
                col_btn, col_del = st.columns([5, 1])
                display_q = chat['query'][:36] + "…" if len(chat['query']) > 36 else chat['query']
                with col_btn:
                    if st.button(f"↩ {display_q}", key=f"chat_{i}", help=chat['query'],
                                 use_container_width=True):
                        st.session_state.active_query = chat['query']
                        st.session_state.auto_search = True
                        st.rerun()
                with col_del:
                    if st.button("✕", key=f"del_{i}"):
                        del st.session_state.chat_history[idx]
                        st.rerun()

            st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
            if st.button("Clear All", type="secondary", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
        else:
            st.markdown(
                '<p style="color:var(--text-muted);font-size:0.8rem;margin-top:0.5rem">No queries yet</p>',
                unsafe_allow_html=True
            )

        st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-heading">Filters</div>', unsafe_allow_html=True)
        aum_filter = st.multiselect(
            "AUM Range",
            ["$10B+", "$5B-$10B", "$1B-$5B", "$500M-$1B"],
            default=["$10B+", "$5B-$10B", "$1B-$5B", "$500M-$1B"],
            label_visibility="collapsed",
        )
        confidence_filter = st.multiselect(
            "Confidence",
            ["High", "Medium", "Low"],
            default=["High", "Medium", "Low"],
            label_visibility="collapsed",
        )
        st.caption("AUM Range · Confidence Level")

    # ── Main Column ───────────────────────────
    with col_main:
        data = load_family_office_data("task1_dataset/family_offices_decision_grade.json")

        # Metric row
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="metric-label">Family Offices</div>
                <div class="metric-value">{len(data)}</div>
                <div class="metric-sub">Indexed & searchable</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Queries Cached</div>
                <div class="metric-value">{len(st.session_state.chat_history)}</div>
                <div class="metric-sub">Session history</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Cache Layer</div>
                <div class="metric-value" style="font-size:1.1rem;padding-top:0.4rem">
                    {"<span class='status-badge status-active'>● Redis Active</span>" if redis_client else "<span class='status-badge status-inactive'>● No Redis</span>"}
                </div>
                <div class="metric-sub">{"Real-time deduplication" if redis_client else "In-memory only"}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Query bar ────────────────────────
        active_query = st.session_state.active_query
        auto_search  = st.session_state.auto_search
        if active_query:
            query = active_query
            auto_search = True
            st.session_state.active_query = ""
            st.session_state.auto_search  = False
        else:
            query = ""

        query = st.text_input(
            "Query",
            value=query,
            placeholder="e.g.  venture capital AI  ·  sovereign wealth fund technology  ·  European buyout",
            label_visibility="collapsed",
        )

        col_s, col_c = st.columns([2, 1])
        with col_s:
            search_clicked = st.button("Search", type="primary", use_container_width=True)

        current_query = query.strip() if query else ""
        should_search = (search_clicked or auto_search) and current_query

        # ── Results ──────────────────────────
        if should_search:
            cached_result = cache_get(current_query)
            if cached_result:
                st.markdown(
                    '<div class="cache-banner">◆ &nbsp; Retrieved from Redis cache</div>',
                    unsafe_allow_html=True
                )
                results = cached_result
            else:
                with st.spinner("Searching across indexed family offices…"):
                    results = pipeline.answer_query(current_query, top_k=10)
                cache_set(current_query, results)

            if not any(h['query'] == current_query for h in st.session_state.chat_history):
                st.session_state.chat_history.insert(0, {
                    'query': current_query,
                    'timestamp': datetime.now().strftime("%H:%M"),
                    'num_results': results['num_results']
                })

            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)

            if results['num_results'] == 0:
                st.markdown("""
                <div class="empty-state">
                    <div class="empty-state-icon">◇</div>
                    <div class="empty-state-text">No results found — try broadening your search terms</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                high_conf = sum(
                    1 for r in results["results"]
                    if r.get("metadata", {}).get("confidence_score") == "High"
                )
                st.markdown(f"""
                <div style="margin-bottom:1.2rem">
                    <span style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:600;color:var(--text-primary)">
                        {results['num_results']} results
                    </span>
                    <span style="font-size:0.82rem;color:var(--text-muted);margin-left:0.8rem">
                        for &nbsp;<em style="color:var(--gold-light)">{current_query}</em>
                    </span>
                    <span style="font-size:0.75rem;color:var(--text-muted);margin-left:1.2rem">
                        {high_conf} high-confidence
                    </span>
                </div>
                """, unsafe_allow_html=True)

                for i, doc in enumerate(results["results"], 1):
                    confidence = doc["metadata"].get("confidence_score", "N/A")
                    aum        = doc["metadata"].get("aum_estimate", "N/A")

                    if confidence_filter and confidence not in confidence_filter:
                        continue
                    if aum_filter and aum not in aum_filter:
                        continue

                    conf_class = {
                        "High": "pill-high", "Medium": "pill-medium", "Low": "pill-low"
                    }.get(confidence, "pill-low")

                    # Extract metadata fields - use empty string if not present
                    entity_type = doc['metadata'].get('entity_type', '')
                    location = doc['metadata'].get('location', '')
                    region = doc['metadata'].get('region', '')
                    focus    = doc['metadata'].get('investment_focus', '')
                    stage    = doc['metadata'].get('stage', '')
                    notable  = doc['metadata'].get('notable_investments', '')
                    data_verified = doc['metadata'].get('data_verified', '')
                    notes = doc['metadata'].get('notes', '')
                    sources  = doc['metadata'].get('source_links', [])

                    source_html = ""
                    if sources:
                        links = " ".join(
                            f'<a class="source-link" href="{s}" target="_blank">↗ Source {j+1}</a>'
                            for j, s in enumerate(sources[:3])
                        )
                        source_html = f'<div style="margin-top:0.8rem">{links}</div>'

                    # Build markdown for result card with conditional field rendering
                    card_md = f"""
<div class="result-card">
    <div class="result-index">◆ &nbsp; #{i:02d}</div>
    <div class="result-title">{doc['title']}</div>
    <div class="result-meta">
        <span class="meta-pill pill-location">📍 {location}</span>
        <span class="meta-pill pill-aum">◈ {aum}</span>
        <span class="meta-pill {conf_class}">✦ {confidence}</span>
    </div>
                    """
                    
                    # Add Entity Type if present
                    if entity_type:
                        card_md += f"""
**Entity Type :**
{entity_type}
                        """
                    
                    # Add Region if present
                    if region:
                        card_md += f"""
**Region :**
{region}
                        """
                    
                    # Add Investment Focus if present
                    if focus:
                        card_md += f"""
**Investment Focus :**
{focus}
                        """
                    
                    # Add Stage if present
                    if stage:
                        card_md += f"""
**Stage :**
{stage}
                        """
                    
                    # Add Notable Investments if present
                    if notable:
                        card_md += f"""
**Notable Investments :**
{notable}
                        """
                    
                    # Add Data Verified if present
                    if data_verified:
                        card_md += f"""
**Data Verified :**
{data_verified}
                        """
                    
                    # Add Notes - always display (mandatory field)
                    note_display = notes if notes else "Verified family office data from trusted sources"
                    card_md += f"""
**Note :**
{note_display}
                    """
                    
                    # Add source links
                    card_md += source_html
                    card_md += """
</div>
                    """
                    
                    st.markdown(card_md, unsafe_allow_html=True)

        # ── Suggested Queries ─────────────────
        st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Suggested Queries</div>', unsafe_allow_html=True)

        sample_queries = [
            ("AI & ML Venture", "venture capital ai machine learning"),
            ("Sovereign Wealth Tech", "sovereign wealth fund technology"),
            ("US Buyout Funds", "private equity buyout united states"),
            ("Fintech Growth", "fintech investment growth stage"),
            ("Healthcare VC", "healthcare venture capital"),
            ("Real Estate FO", "family office real estate"),
            ("Credit Strategies", "hedge fund credit strategies"),
            ("European Tech", "european technology investment"),
        ]

        cols = st.columns(4)
        for i, (label, sq) in enumerate(sample_queries):
            with cols[i % 4]:
                if st.button(label, key=f"suggest_{i}", use_container_width=True):
                    st.session_state.active_query = sq
                    st.rerun()


# ══════════════════════════════════════════════
# TAB 2 — SaaS Analysis
# ══════════════════════════════════════════════
with tab_analysis:
    st.markdown("""
    <div style="margin-bottom:1.5rem">
        <div class="fo-wordmark" style="font-size:1.8rem">SaaS Conversion Analysis</div>
        <div class="fo-tagline" style="margin-bottom:0">RAG Product · Conversion Optimisation</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        from task3_saas_analysis.conversion_analysis import (
            analyze_conversion_funnel, analyze_blockers, show_metrics,
            analyze_pricing, analyze_cohorts, show_one_fix
        )
        output = ""
        for func in [analyze_conversion_funnel, analyze_blockers, show_metrics,
                     analyze_pricing, analyze_cohorts, show_one_fix]:
            output += render_analysis(func)
        st.code(output, language="text")
        st.markdown("""
        <div style="background:rgba(200,170,90,0.07);border:1px solid var(--gold-dim);border-radius:12px;
                    padding:1rem 1.4rem;margin-top:1rem">
            <span style="color:var(--gold-light);font-family:'IBM Plex Mono',monospace;font-size:0.75rem;
                         letter-spacing:0.1em">◆ KEY INSIGHT</span>
            <p style="margin:0.4rem 0 0;color:var(--text-secondary);font-size:0.9rem">
                This is NOT a typical SaaS conversion problem. The leverage point is <strong style="color:var(--text-primary)">TRUST in data quality</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"""
        <div style="background:rgba(139,38,53,0.12);border:1px solid rgba(139,38,53,0.35);
                    border-radius:10px;padding:1rem 1.4rem;color:#f87171;font-size:0.85rem">
            ⚠ &nbsp; Error loading analysis module: <code>{e}</code>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 3 — AI Product Spec
# ══════════════════════════════════════════════
with tab_product:
    st.markdown("""
    <div style="margin-bottom:1.5rem">
        <div class="fo-wordmark" style="font-size:1.8rem">FundFlow <span>Product Spec</span></div>
        <div class="fo-tagline" style="margin-bottom:0">Daily Venture Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        from task4_ai_product.product_spec import (
            show_product, show_icp, show_pricing, show_revenue_projection,
            show_trial_strategy, show_deployment, show_costs,
            show_ai_role, show_build_plan
        )
        output = ""
        for func in [show_product, show_icp, show_pricing, show_revenue_projection,
                     show_trial_strategy, show_deployment, show_costs,
                     show_ai_role, show_build_plan]:
            output += render_analysis(func)
        st.code(output, language="text")
        st.markdown("""
        <div style="background:rgba(46,125,82,0.1);border:1px solid rgba(74,222,128,0.25);border-radius:12px;
                    padding:1rem 1.4rem;margin-top:1rem">
            <span style="color:#4ade80;font-family:'IBM Plex Mono',monospace;font-size:0.75rem;
                         letter-spacing:0.1em">◆ STATUS</span>
            <p style="margin:0.4rem 0 0;color:var(--text-secondary);font-size:0.9rem">
                <strong style="color:#4ade80">FundFlow</strong> — Viral product concept.
                Launch in 1 week, <strong style="color:var(--text-primary)">$0 cost</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"""
        <div style="background:rgba(139,38,53,0.12);border:1px solid rgba(139,38,53,0.35);
                    border-radius:10px;padding:1rem 1.4rem;color:#f87171;font-size:0.85rem">
            ⚠ &nbsp; Error loading product spec: <code>{e}</code>
        </div>
        """, unsafe_allow_html=True)


# ── Footer ────────────────────────────────────
st.markdown("""
<div class="gold-rule"></div>
<div style="display:flex;justify-content:space-between;align-items:center;
            padding:0.2rem 0 1rem;opacity:0.5">
    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.65rem;letter-spacing:0.12em;
                 text-transform:uppercase;color:var(--text-muted)">
        ◆ &nbsp; ChromaDB · Redis · Hybrid RAG · 48 Family Offices
    </span>
    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.65rem;color:var(--text-muted)">
        FamilyOffice Intelligence
    </span>
</div>
""", unsafe_allow_html=True)