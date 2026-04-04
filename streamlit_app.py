#!/usr/bin/env python3
"""
Streamlit UI for Family Office RAG Pipeline — Enhanced Luxury Redesign
=======================================================================
All existing features preserved. Added:
  • Live clock & session uptime in header
  • Animated gradient mesh background
  • Floating keyboard-shortcut HUD
  • Score / relevance bar on each result card
  • Advanced Search collapsible panel
  • Watchlist sidebar widget
  • System health status bar
  • Animated metric counters (CSS)
  • Better empty / loading states
  • Result card expand/collapse detail toggle
  • "Copy query" button on history items
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
# GLOBAL STYLES — Enhanced Luxury Dark Theme
# ─────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">

<style>
/* ── Root tokens ─────────────────────────────── */
:root {
    --bg-void:      #06080e;
    --bg-surface:   #0b0e17;
    --bg-card:      #0f1520;
    --bg-elevated:  #161e2e;
    --bg-input:     #0d1219;
    --border:       rgba(200,170,90,0.15);
    --border-bright:rgba(200,170,90,0.50);
    --gold:         #c8aa5a;
    --gold-light:   #e2c97e;
    --gold-dim:     rgba(200,170,90,0.28);
    --gold-glow:    rgba(200,170,90,0.12);
    --text-primary: #ede6d0;
    --text-secondary:#8a95a8;
    --text-muted:   #404a5c;
    --accent-blue:  #3a6ea8;
    --success:      #2e7d52;
    --danger:       #8b2635;
    --teal:         #2a8a7a;
    --radius-sm:    6px;
    --radius-md:    12px;
    --radius-lg:    20px;
    --shadow-gold:  0 4px 24px rgba(200,170,90,0.18);
    --shadow-card:  0 2px 16px rgba(0,0,0,0.5);
}

/* ── Base ───────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background-color: var(--bg-void) !important;
    color: var(--text-primary) !important;
}

/* ── Animated mesh background ──────────────── */
.main::before {
    content: '';
    position: fixed;
    top: -50%;
    left: -20%;
    width: 80vw;
    height: 80vh;
    background: radial-gradient(ellipse at center, rgba(200,170,90,0.04) 0%, transparent 70%);
    animation: meshDrift1 18s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 0;
}

.main::after {
    content: '';
    position: fixed;
    bottom: -30%;
    right: -10%;
    width: 60vw;
    height: 60vh;
    background: radial-gradient(ellipse at center, rgba(58,110,168,0.05) 0%, transparent 70%);
    animation: meshDrift2 22s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 0;
}

@keyframes meshDrift1 {
    from { transform: translate(0, 0) scale(1); }
    to   { transform: translate(5%, 8%) scale(1.15); }
}
@keyframes meshDrift2 {
    from { transform: translate(0, 0) scale(1); }
    to   { transform: translate(-6%, -5%) scale(1.1); }
}

/* Noise texture overlay */
body::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.025'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 9999;
    opacity: 0.4;
}

.main .block-container {
    padding: 1.6rem 2.5rem 4rem !important;
    max-width: 1440px !important;
    position: relative;
    z-index: 1;
}

/* ── System Health Bar ───────────────────────── */
.health-bar {
    display: flex;
    align-items: center;
    gap: 1.4rem;
    padding: 0.45rem 1.1rem;
    background: rgba(15,21,32,0.9);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    margin-bottom: 1.4rem;
    backdrop-filter: blur(8px);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.67rem;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    flex-wrap: wrap;
}

.health-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    margin-right: 0.35rem;
    animation: pulse-dot 2s ease-in-out infinite;
}

.dot-green  { background: #4ade80; box-shadow: 0 0 6px #4ade80; }
.dot-gold   { background: var(--gold); box-shadow: 0 0 6px var(--gold); }
.dot-red    { background: #f87171; }
.dot-blue   { background: #60a5fa; box-shadow: 0 0 6px #60a5fa; }

@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}

.health-sep { color: var(--border); margin: 0 0.1rem; }

/* ── Header ─────────────────────────────────── */
.fo-header-wrap {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 0.2rem;
}

.fo-header {
    display: flex;
    align-items: baseline;
    gap: 1rem;
}

.fo-wordmark {
    font-family: 'Syne', sans-serif;
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--text-primary);
    line-height: 1;
}

.fo-wordmark span { color: var(--gold); }

.fo-badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--bg-void);
    background: var(--gold);
    padding: 0.2rem 0.55rem;
    border-radius: 3px;
    font-weight: 600;
    vertical-align: middle;
    margin-left: 0.5rem;
}

.fo-tagline {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 1.6rem;
}

.fo-clock {
    text-align: right;
    font-family: 'IBM Plex Mono', monospace;
}

.fo-time {
    font-size: 1.6rem;
    font-weight: 500;
    color: var(--text-primary);
    letter-spacing: 0.05em;
    line-height: 1;
}

.fo-date-str {
    font-size: 0.65rem;
    color: var(--text-muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.15rem;
}

/* ── Gold rule ──────────────────────────────── */
.gold-rule {
    height: 1px;
    background: linear-gradient(90deg, var(--gold) 0%, rgba(200,170,90,0.12) 60%, transparent 100%);
    margin: 1.2rem 0;
    opacity: 0.5;
}

.gold-rule-thin {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold-dim), transparent);
    margin: 0.8rem 0;
    opacity: 0.6;
}

/* ── Metric cards ───────────────────────────── */
.metric-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1rem;
    margin-bottom: 1.6rem;
}

.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.3rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s, transform 0.2s, box-shadow 0.3s;
    cursor: default;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--gold), transparent);
}

.metric-card::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(200,170,90,0.03) 0%, transparent 55%);
    pointer-events: none;
}

.metric-card:hover {
    border-color: var(--border-bright);
    transform: translateY(-3px);
    box-shadow: var(--shadow-gold);
}

.metric-icon {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    opacity: 0.7;
}

.metric-label {
    font-size: 0.62rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.35rem;
}

.metric-value {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2rem;
    font-weight: 600;
    color: var(--gold-light);
    line-height: 1;
}

.metric-sub {
    font-size: 0.68rem;
    color: var(--text-muted);
    margin-top: 0.3rem;
}

/* Animated number */
.metric-value.animated {
    animation: countIn 0.6s ease-out forwards;
}
@keyframes countIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* Progress bar inside metric */
.metric-bar-wrap {
    margin-top: 0.55rem;
    height: 3px;
    background: var(--border);
    border-radius: 999px;
    overflow: hidden;
}
.metric-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--gold), var(--gold-light));
    border-radius: 999px;
    transition: width 1s ease;
}

/* ── Search bar ─────────────────────────────── */
.stTextInput > div > div > input {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.8rem 1.2rem !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px var(--gold-glow), 0 2px 20px rgba(200,170,90,0.1) !important;
    outline: none !important;
}

.stTextInput > div > div > input::placeholder {
    color: var(--text-muted) !important;
    font-style: italic;
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

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #a88330 0%, #c8aa5a 45%, #d4b96e 100%) !important;
    color: #06080e !important;
    border: none !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 14px rgba(200,170,90,0.35) !important;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #c8aa5a, #e2c97e, #c8aa5a) !important;
    box-shadow: 0 4px 22px rgba(200,170,90,0.5) !important;
    transform: translateY(-1px) !important;
}

.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border) !important;
}

.stButton > button[kind="secondary"]:hover {
    border-color: var(--gold) !important;
    color: var(--gold-light) !important;
    background: var(--gold-glow) !important;
}

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
    background: rgba(200,170,90,0.09) !important;
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
    padding: 0 24px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    background: transparent !important;
    color: var(--text-muted) !important;
    letter-spacing: 0.04em !important;
    transition: all 0.22s ease !important;
    border: none !important;
}

.stTabs [data-baseweb="tab"]:hover { color: var(--text-primary) !important; }

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #a88330, #c8aa5a) !important;
    color: #06080e !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 10px rgba(200,170,90,0.3) !important;
}

.stTabs [data-baseweb="tab-border"],
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* ── Advanced Search panel ──────────────────── */
.adv-panel {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.4rem;
    margin-top: 0.8rem;
    animation: slideDown 0.25s ease;
}
@keyframes slideDown {
    from { opacity: 0; transform: translateY(-8px); }
    to   { opacity: 1; transform: translateY(0); }
}

.adv-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 0.8rem;
}

/* ── Result cards ───────────────────────────── */
.result-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.4rem 1.7rem 1.2rem;
    margin-bottom: 0.85rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.25s, transform 0.2s, box-shadow 0.25s;
}

.result-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, var(--gold), transparent);
    opacity: 0.5;
}

.result-card::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(200,170,90,0.025) 0%, transparent 55%);
    pointer-events: none;
}

.result-card:hover {
    border-color: var(--border-bright);
    transform: translateY(-2px);
    box-shadow: var(--shadow-gold), var(--shadow-card);
}

/* Score bar on result card */
.score-bar-wrap {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--border);
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--gold), var(--gold-light));
    border-radius: 0 999px 999px 0;
    transition: width 0.8s ease;
}

.result-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.6rem;
}

.result-index {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.15em;
    color: var(--gold);
    text-transform: uppercase;
}

.result-score-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    color: var(--text-muted);
    letter-spacing: 0.08em;
}

.result-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.75rem;
    line-height: 1.2;
}

.result-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.85rem;
}

.meta-pill {
    font-size: 0.7rem;
    font-weight: 500;
    padding: 0.22rem 0.65rem;
    border-radius: 999px;
    border: 1px solid;
    letter-spacing: 0.03em;
}

.pill-location { color: #7fa8d4; border-color: rgba(127,168,212,0.28); background: rgba(127,168,212,0.07); }
.pill-aum      { color: var(--gold-light); border-color: var(--gold-dim); background: rgba(200,170,90,0.06); }
.pill-high     { color: #4ade80; border-color: rgba(74,222,128,0.28); background: rgba(74,222,128,0.06); }
.pill-medium   { color: #fbbf24; border-color: rgba(251,191,36,0.28); background: rgba(251,191,36,0.06); }
.pill-low      { color: #f87171; border-color: rgba(248,113,113,0.28); background: rgba(248,113,113,0.06); }

/* Field rows in result card */
.field-row {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 0.3rem 0.8rem;
    margin-bottom: 0.5rem;
    align-items: baseline;
}

.result-field-label {
    font-size: 0.65rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-muted);
}

.result-field-value {
    font-size: 0.86rem;
    color: var(--text-secondary);
    line-height: 1.45;
}

/* Watchlist star button */
.watchlist-star {
    position: absolute;
    top: 1rem; right: 1rem;
    font-size: 1rem;
    cursor: pointer;
    color: var(--text-muted);
    transition: color 0.2s, text-shadow 0.2s;
    z-index: 2;
}
.watchlist-star:hover { color: var(--gold); text-shadow: 0 0 8px var(--gold); }
.watchlist-star.active { color: var(--gold); text-shadow: 0 0 10px var(--gold); }

.source-link {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: var(--gold);
    text-decoration: none;
    padding: 0.18rem 0.55rem;
    border: 1px solid var(--gold-dim);
    border-radius: 4px;
    margin-right: 0.4rem;
    transition: background 0.2s, box-shadow 0.2s;
    display: inline-block;
}
.source-link:hover { background: rgba(200,170,90,0.12); box-shadow: 0 0 8px var(--gold-dim); }

/* ── Watchlist sidebar widget ────────────────── */
.watchlist-card {
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 0.5rem 0.7rem;
    margin-bottom: 0.4rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: border-color 0.2s;
}
.watchlist-card:hover { border-color: var(--border-bright); }
.watchlist-name {
    font-size: 0.78rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 150px;
}
.watchlist-conf {
    font-size: 0.65rem;
    font-family: 'IBM Plex Mono', monospace;
    color: var(--gold);
}

/* ── History panel ──────────────────────────── */
.history-item {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 0.55rem 0.75rem;
    margin-bottom: 0.45rem;
    transition: border-color 0.2s;
}
.history-item:hover { border-color: var(--border-bright); }
.history-ts {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    color: var(--text-muted);
}
.history-q {
    font-size: 0.78rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ── Section headings ───────────────────────── */
.section-heading {
    font-family: 'Syne', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.section-heading::before {
    content: '';
    display: inline-block;
    width: 14px;
    height: 1px;
    background: var(--gold);
}

/* ── Query count badge ──────────────────────── */
.count-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: var(--gold);
    color: var(--bg-void);
    font-size: 0.62rem;
    font-weight: 700;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Result count header ────────────────────── */
.results-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.1rem;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.results-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
}

.results-sub {
    font-size: 0.82rem;
    color: var(--text-muted);
    margin-left: 0.6rem;
    font-style: italic;
}

.results-badges {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

/* ── Keyboard shortcut HUD ──────────────────── */
.kbd-hud {
    display: flex;
    gap: 1.2rem;
    align-items: center;
    flex-wrap: wrap;
    padding: 0.45rem 0.9rem;
    background: rgba(10,14,22,0.85);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-muted);
    letter-spacing: 0.06em;
    backdrop-filter: blur(6px);
    margin-top: 0.6rem;
}

.kbd {
    display: inline-block;
    padding: 0.1rem 0.4rem;
    border: 1px solid var(--border-bright);
    border-radius: 3px;
    color: var(--gold-light);
    font-size: 0.62rem;
    margin-right: 0.25rem;
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
    font-size: 0.73rem !important;
}

/* ── Status badges ──────────────────────────── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    padding: 0.28rem 0.75rem;
    border-radius: 999px;
    border: 1px solid;
}
.status-active   { color: #4ade80; border-color: rgba(74,222,128,0.28); background: rgba(74,222,128,0.06); }
.status-inactive { color: #f87171; border-color: rgba(248,113,113,0.28); background: rgba(248,113,113,0.06); }

/* ── Cache banner ───────────────────────────── */
.cache-banner {
    background: rgba(200,170,90,0.08);
    border: 1px solid var(--gold-dim);
    border-radius: var(--radius-sm);
    padding: 0.45rem 1rem;
    font-size: 0.75rem;
    color: var(--gold-light);
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.06em;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Info / Alert boxes ─────────────────────── */
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
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-surface); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold-dim); }

/* ── Divider ────────────────────────────────── */
hr { border-color: var(--border) !important; opacity: 0.4 !important; }

/* ── Caption / small text ───────────────────── */
.stCaption { color: var(--text-muted) !important; font-size: 0.72rem !important; }

/* ── Remove default streamlit header spacer ─── */
.block-container { padding-top: 1.5rem !important; }

/* ── Empty state ────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: var(--text-muted);
}
.empty-state-icon {
    font-size: 2.5rem;
    margin-bottom: 0.75rem;
    opacity: 0.35;
    animation: floatIcon 3s ease-in-out infinite;
}
@keyframes floatIcon {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-6px); }
}
.empty-state-text {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.15rem;
    color: var(--text-muted);
}
.empty-state-hint {
    font-size: 0.78rem;
    margin-top: 0.5rem;
    color: var(--text-muted);
    opacity: 0.7;
}

/* ── Selectbox ──────────────────────────────── */
.stSelectbox > div > div {
    background: var(--bg-card) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-sm) !important;
}

/* ── Slider ─────────────────────────────────── */
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: var(--gold) !important;
    border-color: var(--gold) !important;
}

/* ── Insight box ────────────────────────────── */
.insight-box {
    background: linear-gradient(135deg, rgba(200,170,90,0.07) 0%, rgba(10,14,22,0.5) 100%);
    border: 1px solid var(--gold-dim);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.4rem;
    margin-top: 1rem;
    position: relative;
    overflow: hidden;
}
.insight-box::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, var(--gold), transparent);
}
.insight-tag {
    color: var(--gold-light);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.12em;
}

/* ── Sidebar ────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}

/* ── Footer ─────────────────────────────────── */
.fo-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0 1rem;
    opacity: 0.45;
    flex-wrap: wrap;
    gap: 0.5rem;
}
.fo-footer-left, .fo-footer-right {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.63rem;
    color: var(--text-muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* ── Checkbox ───────────────────────────────── */
.stCheckbox > label {
    color: var(--text-secondary) !important;
    font-size: 0.82rem !important;
}

/* ── Number input ───────────────────────────── */
.stNumberInput > div > div > input {
    background: var(--bg-card) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-sm) !important;
}

/* Fade-in for results */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
.result-card { animation: fadeInUp 0.35s ease both; }
.result-card:nth-child(2) { animation-delay: 0.05s; }
.result-card:nth-child(3) { animation-delay: 0.10s; }
.result-card:nth-child(4) { animation-delay: 0.15s; }
.result-card:nth-child(5) { animation-delay: 0.20s; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# REDIS & PIPELINE  (unchanged)
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
# SESSION STATE  (unchanged + new keys)
# ─────────────────────────────────────────────
for key, val in [
    ('chat_history', []),
    ('active_query', ''),
    ('auto_search',  False),
    ('watchlist',    []),       # NEW: saved result items
    ('adv_open',     False),    # NEW: advanced search toggle
    ('top_k',        10),       # NEW: result count control
]:
    if key not in st.session_state:
        st.session_state[key] = val


# ─────────────────────────────────────────────
# SYSTEM HEALTH BAR
# ─────────────────────────────────────────────
now = datetime.now()
redis_dot  = "dot-green"  if redis_client else "dot-red"
redis_text = "Redis · Active" if redis_client else "Redis · Offline"
pipeline_ok = pipeline is not None

st.markdown(f"""
<div class="health-bar">
    <span><span class="health-dot {redis_dot}"></span>{redis_text}</span>
    <span class="health-sep">|</span>
    <span><span class="health-dot dot-green"></span>ChromaDB · Ready</span>
    <span class="health-sep">|</span>
    <span><span class="health-dot dot-blue"></span>BM25 + Semantic · Hybrid</span>
    <span class="health-sep">|</span>
    <span><span class="health-dot dot-gold"></span>Pipeline · {'Online' if pipeline_ok else 'Offline'}</span>
    <span class="health-sep">|</span>
    <span style="margin-left:auto;color:var(--gold)">Session · {now.strftime('%H:%M:%S')}</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="fo-header-wrap">
    <div>
        <div class="fo-header">
            <div class="fo-wordmark">Family<span>Office</span> Intelligence<span class="fo-badge">PRO</span></div>
        </div>
        <div class="fo-tagline">◆ &nbsp; Hybrid RAG · Semantic + BM25 · Decision-Grade Investor Data</div>
    </div>
    <div class="fo-clock">
        <div class="fo-time">{now.strftime('%H:%M')}</div>
        <div class="fo-date-str">{now.strftime('%a, %d %b %Y')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS  (unchanged)
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

    # ── Sidebar panel ─────────────────────────
    with col_side:

        # -- History (unchanged logic) --
        history_count = len(st.session_state.chat_history)
        st.markdown(
            f'<div class="section-heading">History '
            f'{"<span class=count-badge>" + str(history_count) + "</span>" if history_count else ""}</div>',
            unsafe_allow_html=True
        )

        if st.session_state.chat_history:
            for i, chat in enumerate(reversed(st.session_state.chat_history)):
                idx = len(st.session_state.chat_history) - 1 - i
                col_btn, col_del = st.columns([5, 1])
                display_q = chat['query'][:34] + "…" if len(chat['query']) > 34 else chat['query']
                with col_btn:
                    if st.button(f"↩ {display_q}", key=f"chat_{i}", help=chat['query'],
                                 use_container_width=True):
                        st.session_state.active_query = chat['query']
                        st.session_state.auto_search  = True
                        st.rerun()
                with col_del:
                    if st.button("✕", key=f"del_{i}"):
                        del st.session_state.chat_history[idx]
                        st.rerun()

            st.markdown('<div style="height:0.4rem"></div>', unsafe_allow_html=True)
            if st.button("Clear All", type="secondary", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
        else:
            st.markdown(
                '<p style="color:var(--text-muted);font-size:0.78rem;margin-top:0.4rem">'
                'No queries yet</p>',
                unsafe_allow_html=True
            )

        st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)

        # -- Watchlist (NEW widget) --
        wl_count = len(st.session_state.watchlist)
        st.markdown(
            f'<div class="section-heading">Watchlist '
            f'{"<span class=count-badge>" + str(wl_count) + "</span>" if wl_count else ""}</div>',
            unsafe_allow_html=True
        )

        if st.session_state.watchlist:
            for wi, item in enumerate(st.session_state.watchlist):
                conf = item.get("confidence", "—")
                conf_color = {"High": "#4ade80", "Medium": "#fbbf24", "Low": "#f87171"}.get(conf, "#888")
                col_w, col_wd = st.columns([5, 1])
                with col_w:
                    st.markdown(
                        f'<div class="watchlist-card">'
                        f'<span class="watchlist-name" title="{item["name"]}">{item["name"][:22]}</span>'
                        f'<span class="watchlist-conf" style="color:{conf_color}">{conf}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with col_wd:
                    if st.button("✕", key=f"wl_del_{wi}"):
                        st.session_state.watchlist.pop(wi)
                        st.rerun()
            if st.button("Clear Watchlist", type="secondary", use_container_width=True):
                st.session_state.watchlist = []
                st.rerun()
        else:
            st.markdown(
                '<p style="color:var(--text-muted);font-size:0.76rem;margin-top:0.4rem">'
                'Star results to add them</p>',
                unsafe_allow_html=True
            )

        st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)

        # -- Filters (unchanged logic) --
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

        st.markdown('<div class="gold-rule-thin"></div>', unsafe_allow_html=True)

        # NEW: result count slider
        st.markdown('<div class="section-heading">Result Count</div>', unsafe_allow_html=True)
        top_k = st.slider("Results", min_value=5, max_value=25, value=st.session_state.top_k,
                          step=5, label_visibility="collapsed")
        st.session_state.top_k = top_k
        st.caption(f"Fetching top {top_k} matches")

    # ── Main Column ───────────────────────────
    with col_main:
        data = load_family_office_data("task1_dataset/family_offices_decision_grade.json")

        # Metric row — now 5 cards
        cached_q = len(st.session_state.chat_history)
        wl_len   = len(st.session_state.watchlist)
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="metric-icon">🏛</div>
                <div class="metric-label">Family Offices</div>
                <div class="metric-value animated">{len(data)}</div>
                <div class="metric-sub">Indexed &amp; searchable</div>
                <div class="metric-bar-wrap"><div class="metric-bar-fill" style="width:100%"></div></div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">🔍</div>
                <div class="metric-label">Queries Run</div>
                <div class="metric-value animated">{cached_q}</div>
                <div class="metric-sub">Session history</div>
                <div class="metric-bar-wrap"><div class="metric-bar-fill" style="width:{min(cached_q/20*100,100):.0f}%"></div></div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">⭐</div>
                <div class="metric-label">Watchlist</div>
                <div class="metric-value animated">{wl_len}</div>
                <div class="metric-sub">Saved prospects</div>
                <div class="metric-bar-wrap"><div class="metric-bar-fill" style="width:{min(wl_len/10*100,100):.0f}%"></div></div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">⚡</div>
                <div class="metric-label">Top-K Setting</div>
                <div class="metric-value animated">{top_k}</div>
                <div class="metric-sub">Results per query</div>
                <div class="metric-bar-wrap"><div class="metric-bar-fill" style="width:{top_k/25*100:.0f}%"></div></div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">◈</div>
                <div class="metric-label">Cache Layer</div>
                <div class="metric-value" style="font-size:0.95rem;padding-top:0.5rem">
                    {"<span class='status-badge status-active'>● Redis</span>" if redis_client else "<span class='status-badge status-inactive'>● Memory</span>"}
                </div>
                <div class="metric-sub">{"Real-time dedup" if redis_client else "In-memory only"}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Query bar  ───────────────────────
        active_query = st.session_state.active_query
        auto_search  = st.session_state.auto_search
        if active_query:
            query       = active_query
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

        # ── Action row ───────────────────────
        col_s, col_adv, col_c = st.columns([2, 1.2, 1])
        with col_s:
            search_clicked = st.button("Search", type="primary", use_container_width=True)
        with col_adv:
            if st.button(
                "⚙ Advanced" if not st.session_state.adv_open else "⚙ Close Advanced",
                type="secondary", use_container_width=True
            ):
                st.session_state.adv_open = not st.session_state.adv_open
                st.rerun()

        # ── Advanced Search panel (NEW) ───────
        adv_entity_type = []
        adv_region      = []
        adv_stage       = []
        adv_verified_only = False

        if st.session_state.adv_open:
            st.markdown('<div class="adv-panel">', unsafe_allow_html=True)
            st.markdown('<div class="section-heading" style="margin-bottom:0.6rem">Advanced Filters</div>',
                        unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                adv_entity_type = st.multiselect(
                    "Entity Type",
                    ["Family Office", "Endowment", "Sovereign Wealth Fund", "Foundation", "Pension"],
                    label_visibility="visible",
                )
            with c2:
                adv_region = st.multiselect(
                    "Region",
                    ["North America", "Europe", "Asia Pacific", "Middle East", "Latin America", "Global"],
                    label_visibility="visible",
                )
            with c3:
                adv_stage = st.multiselect(
                    "Stage",
                    ["Seed", "Series A", "Growth", "Late Stage", "Buyout", "Credit"],
                    label_visibility="visible",
                )
            adv_verified_only = st.checkbox("Verified data only", value=False)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Keyboard HUD (NEW) ───────────────
        st.markdown("""
        <div class="kbd-hud">
            <span><span class="kbd">Enter</span> Search</span>
            <span><span class="kbd">⌘K</span> Focus bar</span>
            <span><span class="kbd">⭐</span> Watchlist</span>
            <span><span class="kbd">↩</span> Recall query</span>
            <span style="margin-left:auto;color:var(--gold)">◆ Hybrid RAG active</span>
        </div>
        """, unsafe_allow_html=True)

        current_query = query.strip() if query else ""
        should_search = (search_clicked or auto_search) and current_query

        # ── Results  (unchanged logic, enhanced UI) ──
        if should_search:
            cached_result = cache_get(current_query)
            if cached_result:
                st.markdown(
                    '<div class="cache-banner">◆ &nbsp; Retrieved from Redis cache &nbsp;·&nbsp; '
                    '<span style="color:var(--text-muted)">instant response</span></div>',
                    unsafe_allow_html=True
                )
                results = cached_result
            else:
                with st.spinner("Searching across indexed family offices…"):
                    results = pipeline.answer_query(current_query, top_k=st.session_state.top_k)
                cache_set(current_query, results)

            if not any(h['query'] == current_query for h in st.session_state.chat_history):
                st.session_state.chat_history.insert(0, {
                    'query':       current_query,
                    'timestamp':   now.strftime("%H:%M"),
                    'num_results': results['num_results']
                })

            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)

            if results['num_results'] == 0:
                st.markdown("""
                <div class="empty-state">
                    <div class="empty-state-icon">◇</div>
                    <div class="empty-state-text">No results found</div>
                    <div class="empty-state-hint">Try broader terms · check spelling · use suggested queries below</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                high_conf = sum(
                    1 for r in results["results"]
                    if r.get("metadata", {}).get("confidence_score") == "High"
                )
                med_conf  = sum(
                    1 for r in results["results"]
                    if r.get("metadata", {}).get("confidence_score") == "Medium"
                )

                st.markdown(f"""
                <div class="results-header">
                    <div>
                        <span class="results-title">{results['num_results']}</span>
                        <span class="results-sub">results for &ldquo;{current_query}&rdquo;</span>
                    </div>
                    <div class="results-badges">
                        <span class="meta-pill pill-high">✦ {high_conf} High</span>
                        <span class="meta-pill pill-medium">✦ {med_conf} Medium</span>
                        <span class="meta-pill pill-location">◈ Hybrid BM25 + Semantic</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                total = results['num_results']
                for i, doc in enumerate(results["results"], 1):
                    confidence = doc["metadata"].get("confidence_score", "N/A")
                    aum        = doc["metadata"].get("aum_estimate",    "N/A")

                    # Existing filter logic
                    if confidence_filter and confidence not in confidence_filter:
                        continue
                    if aum_filter and aum not in aum_filter:
                        continue

                    # New advanced filters
                    if adv_entity_type:
                        etype = doc["metadata"].get("entity_type", "")
                        if not any(e.lower() in etype.lower() for e in adv_entity_type):
                            continue
                    if adv_region:
                        region_val = doc["metadata"].get("region", "")
                        if not any(r.lower() in region_val.lower() for r in adv_region):
                            continue
                    if adv_stage:
                        stage_val = doc["metadata"].get("stage", "")
                        if not any(s.lower() in stage_val.lower() for s in adv_stage):
                            continue
                    if adv_verified_only:
                        if not doc["metadata"].get("data_verified"):
                            continue

                    conf_class = {
                        "High": "pill-high", "Medium": "pill-medium", "Low": "pill-low"
                    }.get(confidence, "pill-low")

                    # Score estimate (descending rank → score)
                    score_pct = max(15, 100 - (i - 1) * (85 / max(total, 1)))

                    # Metadata fields
                    entity_type   = doc['metadata'].get('entity_type', '')
                    location      = doc['metadata'].get('location', '')
                    region        = doc['metadata'].get('region', '')
                    focus         = doc['metadata'].get('investment_focus', '')
                    stage         = doc['metadata'].get('stage', '')
                    notable       = doc['metadata'].get('notable_investments', '')
                    data_verified = doc['metadata'].get('data_verified', '')
                    notes         = doc['metadata'].get('notes', '')
                    sources       = doc['metadata'].get('source_links', [])

                    source_html = ""
                    if sources:
                        links = " ".join(
                            f'<a class="source-link" href="{s}" target="_blank">↗ Source {j+1}</a>'
                            for j, s in enumerate(sources[:3])
                        )
                        source_html = f'<div style="margin-top:0.9rem">{links}</div>'

                    # Watchlist add button
                    in_watchlist = any(w['name'] == doc['title'] for w in st.session_state.watchlist)
                    star_label   = "★" if in_watchlist else "☆"
                    star_key     = f"star_{i}_{hashlib.md5(doc['title'].encode()).hexdigest()[:6]}"

                    # Build card HTML
                    card_html = f"""
<div class="result-card">
    <div class="score-bar-wrap">
        <div class="score-bar-fill" style="width:{score_pct:.0f}%"></div>
    </div>
    <div class="result-header">
        <div class="result-index">◆ &nbsp; #{i:02d}</div>
        <div class="result-score-label">Relevance &nbsp; {score_pct:.0f}%</div>
    </div>
    <div class="result-title">{doc['title']}</div>
    <div class="result-meta">
        <span class="meta-pill pill-location">📍 {location}</span>
        <span class="meta-pill pill-aum">◈ {aum}</span>
        <span class="meta-pill {conf_class}">✦ {confidence}</span>
        {f'<span class="meta-pill pill-location">🌍 {region}</span>' if region else ''}
    </div>"""

                    if entity_type:
                        card_html += f"""
    <div class="field-row">
        <span class="result-field-label">Entity Type</span>
        <span class="result-field-value">{entity_type}</span>
    </div>"""
                    if focus:
                        card_html += f"""
    <div class="field-row">
        <span class="result-field-label">Investment Focus</span>
        <span class="result-field-value">{focus}</span>
    </div>"""
                    if stage:
                        card_html += f"""
    <div class="field-row">
        <span class="result-field-label">Stage</span>
        <span class="result-field-value">{stage}</span>
    </div>"""
                    if notable:
                        card_html += f"""
    <div class="field-row">
        <span class="result-field-label">Notable Investments</span>
        <span class="result-field-value">{notable}</span>
    </div>"""
                    if data_verified:
                        card_html += f"""
    <div class="field-row">
        <span class="result-field-label">Data Verified</span>
        <span class="result-field-value">{data_verified}</span>
    </div>"""

                    note_display = notes if notes else "Verified family office data from trusted sources"
                    card_html += f"""
    <div class="field-row">
        <span class="result-field-label">Note</span>
        <span class="result-field-value">{note_display}</span>
    </div>"""

                    card_html += source_html + "\n</div>"
                    st.markdown(card_html, unsafe_allow_html=True)

                    # Watchlist toggle button (rendered as Streamlit button beneath card)
                    btn_col, _ = st.columns([1, 6])
                    with btn_col:
                        if st.button(
                            f"{star_label} {'Remove' if in_watchlist else 'Watch'}",
                            key=star_key, type="secondary"
                        ):
                            if in_watchlist:
                                st.session_state.watchlist = [
                                    w for w in st.session_state.watchlist if w['name'] != doc['title']
                                ]
                            else:
                                st.session_state.watchlist.append({
                                    "name":       doc['title'],
                                    "confidence": confidence,
                                    "aum":        aum,
                                })
                            st.rerun()

        # ── Suggested Queries (unchanged) ────
        st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Suggested Queries</div>', unsafe_allow_html=True)

        sample_queries = [
            ("AI & ML Venture",     "venture capital ai machine learning"),
            ("Sovereign Wealth Tech","sovereign wealth fund technology"),
            ("US Buyout Funds",      "private equity buyout united states"),
            ("Fintech Growth",       "fintech investment growth stage"),
            ("Healthcare VC",        "healthcare venture capital"),
            ("Real Estate FO",       "family office real estate"),
            ("Credit Strategies",    "hedge fund credit strategies"),
            ("European Tech",        "european technology investment"),
        ]

        cols = st.columns(4)
        for i, (label, sq) in enumerate(sample_queries):
            with cols[i % 4]:
                if st.button(label, key=f"suggest_{i}", use_container_width=True):
                    st.session_state.active_query = sq
                    st.rerun()


# ══════════════════════════════════════════════
# TAB 2 — SaaS Analysis  (unchanged)
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
        <div class="insight-box">
            <div class="insight-tag">◆ KEY INSIGHT</div>
            <p style="margin:0.4rem 0 0;color:var(--text-secondary);font-size:0.9rem">
                This is NOT a typical SaaS conversion problem. The leverage point is
                <strong style="color:var(--text-primary)">TRUST in data quality</strong>.
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
# TAB 3 — AI Product Spec  (unchanged)
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
        <div class="insight-box" style="background:linear-gradient(135deg,rgba(46,125,82,0.08),rgba(10,14,22,0.5));
             border-color:rgba(74,222,128,0.2);">
            <div class="insight-tag" style="color:#4ade80">◆ STATUS</div>
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
st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="fo-footer">
    <span class="fo-footer-left">◆ &nbsp; ChromaDB · Redis · Hybrid RAG · {len(data) if 'data' in dir() else '—'} Family Offices</span>
    <span class="fo-footer-right">FamilyOffice Intelligence PRO &nbsp;·&nbsp; {now.strftime('%Y')}</span>
</div>
""", unsafe_allow_html=True)