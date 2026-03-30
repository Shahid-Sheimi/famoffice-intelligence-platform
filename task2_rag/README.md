# Family Office Dataset & RAG Pipeline

## Overview

This project delivers decision-grade data on Family Offices combined with a production-ready RAG (Retrieval-Augmented Generation) pipeline for investor intelligence queries.

---

## Task 1: Dataset — Family Offices (Decision-Grade)

### Goal
Build a curated dataset of 30-50 high-quality Family Offices suitable for investment decisions.

### Schema

```json
{
  "name": "string",
  "location": "string",
  "aum_estimate": "string (e.g., $500M-$1B)",
  "investment_focus": "string (e.g., Technology, Healthcare)",
  "stage": "string (e.g., Seed, Growth, Buyout)",
  "notable_investments": "string (comma-separated)",
  "source_links": ["array of URLs"],
  "confidence_score": "High | Medium | Low"
}
```

### Data Collection Methodology

1. **Source Prioritization**
   - Primary: Official websites, SEC EDGAR filings, annual reports
   - Secondary: Crunchbase, LinkedIn, industry databases
   - Tertiary: News articles, press releases

2. **Validation Criteria**
   - Cross-reference multiple sources
   - Verify AUM figures against regulatory filings
   - Confirm investment activities through portfolio companies

3. **Confidence Scoring**
   - **High**: Multiple verified sources, regulatory filings, official announcements
   - **Medium**: 2+ sources, industry reports, credible news
   - **Low**: Single source, inferential data

### Dataset Statistics
- **Total Records**: 50 Family Offices
- **Geographic Distribution**: US (22), Europe (5), Asia (10), Middle East (5), Other (8)
- **AUM Distribution**: $10B+ (15), $5B-$10B (10), $1B-$5B (15), $500M-$1B (10)

### Notable Investors Included
- Sequoia Capital, Andreessen Horowitz, Benchmark
- SoftBank Vision Fund, Hillhouse Capital
- Sovereign wealth funds (GIC, Temasek, ADIA, PIF)

---

## Task 2: RAG Pipeline

### Goal
Build a queryable system that leverages the Family Office dataset with semantic search.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG Pipeline                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  1. Load FO Data (JSON)                             │    │
│  │  2. Embed Query (sentence-transformers/Gemini)      │    │
│  │  3. ChromaDB Semantic Search                         │    │
│  │  4. BM25 Keyword Search (hybrid)                     │    │
│  │  5. Combine Scores (α × semantic + (1-α) × bm25)     │    │
│  │  6. Return Ranked Results                           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Query Results                             │
│  - Family Office names                                       │
│  - AUM estimates                                            │
│  - Investment focus                                         │
│  - Confidence scores                                        │
│  - Source links                                             │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (local, free) or Gemini API
- **Vector DB**: ChromaDB (local persistence)
- **Hybrid Search**: Semantic + BM25 keyword matching

### Usage

```bash
# Run the RAG pipeline
cd task2_rag
python3 investor_rag.py

# Or run with Gemini API
export GOOGLE_API_KEY=your-key-here
python3 investor_rag.py
```

### Example Queries
```python
# Family offices investing in AI/ML
"family office artificial intelligence"

# Sovereign wealth funds in Asia
"sovereign wealth fund singapore technology"

# Venture capital in healthcare
"healthcare venture capital growth stage"

# Buyout funds in US
"private equity buyout united states"
```

---

## Dependencies

```
# Core dependencies
pip install chromadb
pip install sentence-transformers
pip install google-genai  # Optional, for Gemini embeddings
pip install python-dotenv
```

---

## Project Structure

```
.
├── task1_dataset/
│   └── family_offices_decision_grade.json  # 50 FOs with full schema
├── task2_rag/
│   ├── investor_rag.py                     # Main RAG pipeline
│   └── README.md                           # This file
├── chroma_db/                              # Vector database
└── requirements.txt
```

---

## Quality Assurance

1. **Data Validation**
   - All entries have at least one source link
   - Confidence scores reflect source reliability
   - Geographic and AUM data cross-verified

2. **Pipeline Testing**
   - Tests with sample queries verify retrieval accuracy
   - Hybrid search ensures both semantic and keyword matching

---

## Limitations & Future Work

1. **Dataset**
   - Add more European and emerging market FOs
   - Include contact information for direct outreach
   - Track portfolio company exits for performance data

2. **Pipeline**
   - Add LLM for natural language answer generation
   - Implement re-ranking for better result quality
   - Add filtering by AUM range, geography, stage

---

*Generated: 2026-03-30*
*Dataset: 50 Family Offices | Pipeline: Hybrid RAG with ChromaDB*