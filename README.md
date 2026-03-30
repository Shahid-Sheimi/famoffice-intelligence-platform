# PolarityIQ Assessment - Falcon Scaling

A comprehensive family office intelligence platform with RAG-powered search and SaaS analytics.

## Project Structure

```
Assesment/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
├── .env.example                 # Environment template
├── .env                         # API keys (not committed)
├── fo-insight-engine/           # Task 1: Family Office Data Pipeline
│   ├── schema.py                # Data schema definitions
│   ├── pipeline.py              # ETL pipeline
│   └── README.md                # Task 1 documentation
├── task2_rag/                   # Task 2: RAG Search System
│   ├── investor_rag.py          # RAG implementation
│   ├── .env                     # API keys for RAG
│   └── README.md                # Task 2 documentation
├── task3_saas_analysis/        # Task 3: SaaS Conversion Analysis
│   ├── conversion_analysis.py   # Analytics code
│   └── README.md                # Task 3 documentation
└── task4_ai_product/           # Task 4: Original AI Product
    ├── product_spec.py         # Product specification
    └── README.md                # Task 4 documentation
```

---

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your Google Gemini API key:
```
GOOGLE_API_KEY=your-actual-api-key-here
```

Get your Gemini API key from: https://aistudio.google.com/app/apikey

### 3. Run Tasks

**Task 1: Family Office Data Pipeline**
```bash
python3 fo-insight-engine/pipeline.py
```
Output: `family_office_processed.json`

**Task 2: RAG-Powered Investor Search**
```bash
python3 task2_rag/investor_rag.py
```
Output: Search results with embeddings from Gemini

**Task 3: SaaS Conversion Analysis**
```bash
python3 task3_saas_analysis/conversion_analysis.py
```
Output: Conversion funnel metrics and insights

**Task 4: AI Product Specification**
```bash
# View the product spec
cat task4_ai_product/product_spec.py
```
Output: Technical specification for "Deal Flow Monitor"

---

## Detailed Task Descriptions

### Task 1: Family Office Intelligence Pipeline

**Location:** `fo-insight-engine/`

A data pipeline that ingests family office information from multiple sources.

**Features:**
- Data normalization and validation
- Deduplication using MD5 hashing
- Support for multiple data formats (CSV, JSON)
- Country code standardization
- AUM range normalization

**Key Classes:**
- `DataPipeline` - Main pipeline orchestrator
- `DataSource` - Represents data sources
- Schema validation in `schema.py`

**Run:**
```bash
python3 fo-insight-engine/pipeline.py
```

**Output:** `family_office_processed.json` with validated records

---

### Task 2: RAG-Powered Investor Intelligence

**Location:** `task2_rag/`

A Retrieval-Augmented Generation system using Google Gemini API for embeddings.

**Features:**
- Semantic search using Gemini embeddings
- BM25 keyword-based fallback retrieval
- Hybrid search combining semantic + keyword
- ChromaDB integration (optional)
- Real-time query processing

**Architecture:**
```
User Query → Embedding (Gemini) → Vector Search → Results
                 ↓
           BM25 Keyword Search → Combined Results
```

**Key Classes:**
- `RAGPipeline` - Main RAG orchestrator
- `EmbeddingModel` - Gemini embedding wrapper
- `VectorStore` - ChromaDB vector storage
- `BM25Retriever` - Keyword search fallback

**Run:**
```bash
python3 task2_rag/investor_rag.py
```

**Sample Output:**
```
Query: family office venture capital
----------------------------------------
  1. Score: 0.120 [bm25]
     Family offices have become significant...
```

---

### Task 3: SaaS Conversion Analysis

**Location:** `task3_saas_analysis/`

Analytics framework for PolarityIQ SaaS platform conversion optimization.

**Features:**
- Conversion funnel modeling
- User journey mapping
- Pricing analysis
- Feature adoption metrics
- Market fit evaluation

**Key Classes:**
- `FunnelStage` - Represents funnel stages
- `ConversionMetrics` - Conversion calculations
- `CustomerJourney` - User journey analysis

**Run:**
```bash
python3 task3_saas_analysis/conversion_analysis.py
```

---

### Task 4: Original AI Product Specification

**Location:** `task4_ai_product/`

Product specification for an AI-powered family office deal flow monitor.

**Product:** Family Office Deal Flow Monitor

**Features:**
- Real-time investment opportunity surfacing
- Signal detection and scoring
- Integration with family office data sources
- Personalized alerts

**View:**
```bash
cat task4_ai_product/product_spec.py
```

---

## Dependencies

### Core Dependencies
- `pandas>=2.0.0` - Data manipulation
- `google-genai>=0.1.0` - Gemini API (free tier)

### Optional Dependencies (not currently used)
- `chromadb` - Vector database
- `langchain` - LLM orchestration
- `openai` - OpenAI API
- Various visualization and NLP libraries

---

## API Configuration

### Google Gemini (Free Tier)

1. Visit https://aistudio.google.com/app/apikey
2. Create a new API key
3. Add to `.env`:
   ```
   GOOGLE_API_KEY=your-key-here
   ```

The free tier includes:
- 15 requests per minute
- 1500 requests per day
- gemini-embedding-001 model

---

## Git Workflow

### Initialize Git (First Time)
```bash
git init
git add .
git commit -m "Initial commit"
```

### Make Changes
```bash
git add <changed-files>
git commit -m "Description of changes"
git status
```

### View Changes
```bash
git diff           # Unstaged changes
git diff --cached  # Staged changes
git log            # Commit history
```

---

## Troubleshooting

### "No API key was provided"
- Ensure `.env` file exists with `GOOGLE_API_KEY`
- Run: `source venv/bin/activate` before running scripts

### "models/embedding-001 not found"
- Update `google-genai`: `pip install --upgrade google-genai`
- Check API key is valid

### "ChromaDB: Not available"
- Install: `pip install chromadb`
- Or continue with BM25 fallback (works without ChromaDB)

---

## File Descriptions

| File | Purpose |
|------|---------|
| `requirements.txt` | Python package dependencies |
| `.env.example` | Template for environment variables |
| `.env` | Actual API keys (never commit this) |
| `.gitignore` | Files to exclude from version control |
| `family_office_processed.json` | Output from Task 1 pipeline |
| `chroma_db/` | Vector database storage (auto-created) |

---

## License

This project is part of the Falcon Scaling × PolarityIQ Assessment for Senior AI Engineer position.

---

## Notes

- All tasks use the Gemini free tier API
- No paid services required
- Works offline with mock embeddings as fallback
- Data is stored locally (no cloud dependencies)