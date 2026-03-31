# Family Office Intelligence Engine

Data pipeline and schema definitions for the PolarityIQ family office intelligence platform.

## Overview

This module provides:
- Schema definitions for validating family office data
- ETL pipeline for ingesting and processing data from multiple sources
- Data normalization and deduplication
- Export to JSON format for the RAG pipeline

## Components

### schema.py
- `FamilyOfficeSchema` - Data schema with validation rules
- `validate_task1_dataset()` - Full task1_dataset validation function
- Field validators for AUM, location, confidence scores

### pipeline.py
- `DataPipeline` - Main ETL pipeline class
- `DataSource` - Represents a data source
- Methods: ingest, deduplicate, normalize, export

## Usage

```bash
# Run the pipeline
python3 pipeline.py

# Validate existing data
python3 -c "from schema import validate_task1_dataset; print(validate_task1_dataset('../task1_dataset/family_offices_processed.json'))"
```

## Input Sources

The pipeline can ingest from:
- JSON files
- CSV files (future)
- APIs (future)

## Output

Processed data is saved to `../task1_dataset/family_offices_processed.json`

## Dependencies

This module uses the main requirements.txt. Key dependencies:
- `pandas` - Data manipulation
- `jsonschema` - Schema validation
- `python-dotenv` - Environment variables