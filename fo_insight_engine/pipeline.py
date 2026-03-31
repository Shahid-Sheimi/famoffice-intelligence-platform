"""
Family Office Intelligence Pipeline

Data pipeline that ingests, normalizes, validates, and processes
family office information from multiple sources.
"""

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from schema import FamilyOfficeSchema, validate_task1_dataset


class DataSource:
    """Represents a data source for family office information."""
    
    def __init__(self, name: str, source_type: str, url: str):
        self.name = name
        self.source_type = source_type  # csv, json, api
        self.url = url
        self.last_fetched: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.source_type,
            "url": self.url,
            "last_fetched": self.last_fetched
        }


class DataPipeline:
    """
    Main data pipeline for family office intelligence.
    
    Handles:
    - Data ingestion from multiple sources
    - Normalization and standardization
    - Deduplication using MD5 hashing
    - Schema validation
    - Export to multiple formats
    """
    
    def __init__(self, output_dir: str = "../task1_dataset"):
        self.output_dir = Path(output_dir)
        self.sources: List[DataSource] = []
        self.records: List[Dict[str, Any]] = []
        self.schema_validator = FamilyOfficeSchema()
        self.seen_hashes: set = set()
        
        # Standardize country codes
        self.country_mapping = {
            "USA": "USA",
            "United States": "USA",
            "UK": "UK",
            "United Kingdom": "UK",
            "UAE": "AE",
            "United Arab Emirates": "AE",
        }
    
    def add_source(self, source: DataSource) -> None:
        """Add a data source to the pipeline."""
        self.sources.append(source)
    
    def ingest_json(self, filepath: str) -> int:
        """
        Ingest records from a JSON file.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Number of records ingested
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            self.records.extend(data)
        elif isinstance(data, dict):
            self.records.append(data)
        
        return len(data)
    
    def generate_record_hash(self, record: Dict[str, Any]) -> str:
        """
        Generate MD5 hash for deduplication.
        
        Uses name + location as unique identifier.
        """
        identifier = f"{record.get('name', '')}|{record.get('location', '')}"
        return hashlib.md5(identifier.encode()).hexdigest()
    
    def deduplicate(self) -> int:
        """
        Remove duplicate records using MD5 hashing.
        
        Returns:
            Number of duplicates removed
        """
        unique_records = []
        initial_count = len(self.records)
        
        for record in self.records:
            record_hash = self.generate_record_hash(record)
            
            if record_hash not in self.seen_hashes:
                self.seen_hashes.add(record_hash)
                unique_records.append(record)
        
        self.records = unique_records
        return initial_count - len(self.records)
    
    def normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and standardize a single record.
        
        - Add verification date
        - Standardize country codes
        - Normalize AUM ranges
        - Add region field
        """
        normalized = record.copy()
        
        # Add verification timestamp if not present
        if "data_verified" not in normalized:
            normalized["data_verified"] = datetime.now().strftime("%Y-%m-%d")
        
        # Extract region from location
        location = normalized.get("location", "")
        if location:
            region = self._extract_region(location)
            normalized["region"] = region
        
        # Normalize AUM if present
        aum = normalized.get("aum_estimate", "")
        if aum:
            normalized["aum_estimate"] = self.schema_validator.normalize_aum(aum)
        
        return normalized
    
    def _extract_region(self, location: str) -> str:
        """Extract geographic region from location string."""
        location_lower = location.lower()
        
        # North America
        if any(x in location_lower for x in ['usa', 'united states', 'canada']):
            return "North America"
        
        # Europe
        if any(x in location_lower for x in ['uk', 'united kingdom', 'france', 'germany', 
                                              'switzerland', 'luxembourg', 'netherlands']):
            return "Europe"
        
        # Middle East
        if any(x in location_lower for x in ['uae', 'abu dhabi', 'dubai', 'qatar', 
                                              'saudi', 'kuwait']):
            return "Middle East"
        
        # Asia Pacific
        if any(x in location_lower for x in ['singapore', 'china', 'hong kong', 
                                              'japan', 'korea', 'australia', 'india']):
            return "Asia Pacific"
        
        return "Unknown"
    
    def process(self) -> Dict[str, Any]:
        """
        Run the full data processing pipeline.
        
        Returns:
            Processing results summary
        """
        results = {
            "initial_records": len(self.records),
            "duplicates_removed": 0,
            "validation_errors": 0,
            "final_records": 0,
            "errors": [],
            "warnings": []
        }
        
        # Step 1: Deduplicate
        results["duplicates_removed"] = self.deduplicate()
        
        # Step 2: Normalize
        normalized_records = []
        for record in self.records:
            normalized = self.normalize_record(record)
            normalized_records.append(normalized)
        
        self.records = normalized_records
        
        # Step 3: Validate
        validation_results = validate_task1_dataset(
            str(self.output_dir / "family_offices_decision_grade.json")
        )
        
        # We can also validate in-memory records
        for record in self.records:
            is_valid = self.schema_validator.validate_record(record)
            if not is_valid:
                results["validation_errors"] += 1
                results["errors"].extend([
                    f"{record.get('name', 'Unknown')}: {e.message}" 
                    for e in self.schema_validator.get_errors()
                ])
            results["warnings"].extend([
                f"{record.get('name', 'Unknown')}: {w.message}"
                for w in self.schema_validator.get_warnings()
            ])
        
        results["final_records"] = len(self.records)
        
        return results
    
    def export_json(self, filename: str = "family_offices_processed.json") -> str:
        """Export processed records to JSON."""
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(self.records, f, indent=2)
        
        return str(output_path)
    
    def export_csv(self, filename: str = "family_offices_processed.csv") -> str:
        """Export processed records to CSV."""
        import csv
        
        if not self.records:
            return ""
        
        output_path = self.output_dir / filename
        
        # Flatten nested structures
        flat_records = []
        for record in self.records:
            flat = {}
            for key, value in record.items():
                if isinstance(value, list):
                    flat[key] = "|".join(str(v) for v in value)
                else:
                    flat[key] = value
            flat_records.append(flat)
        
        fieldnames = list(flat_records[0].keys())
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_records)
        
        return str(output_path)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Generate statistics about the task1_dataset."""
        if not self.records:
            return {"error": "No records in pipeline"}
        
        # Entity type distribution
        entity_types = {}
        for record in self.records:
            etype = record.get("entity_type", "Unknown")
            entity_types[etype] = entity_types.get(etype, 0) + 1
        
        # AUM distribution
        aum_ranges = {}
        for record in self.records:
            aum = record.get("aum_estimate", "Unknown")
            aum_ranges[aum] = aum_ranges.get(aum, 0) + 1
        
        # Region distribution
        regions = {}
        for record in self.records:
            region = record.get("region", "Unknown")
            regions[region] = regions.get(region, 0) + 1
        
        # Confidence distribution
        confidence = {}
        for record in self.records:
            conf = record.get("confidence_score", "Unknown")
            confidence[conf] = confidence.get(conf, 0) + 1
        
        return {
            "total_records": len(self.records),
            "entity_types": entity_types,
            "aum_distribution": aum_ranges,
            "regions": regions,
            "confidence_levels": confidence
        }


def main():
    """Main entry point for running the pipeline."""
    print("=" * 60)
    print("Family Office Intelligence Pipeline")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = DataPipeline()
    
    # Add data source
    source = DataSource(
        name="Curated Family Office List",
        source_type="json",
        url="task1_dataset/family_offices_decision_grade.json"
    )
    pipeline.add_source(source)
    
    # Ingest data
    print("\n[1/4] Ingesting data...")
    count = pipeline.ingest_json(str(pipeline.output_dir / "family_offices_decision_grade.json"))
    print(f"    Ingested {count} records")
    
    # Process data
    print("\n[2/4] Processing data...")
    results = pipeline.process()
    print(f"    Duplicates removed: {results['duplicates_removed']}")
    print(f"    Validation errors: {results['validation_errors']}")
    print(f"    Final records: {results['final_records']}")
    
    # Show statistics
    print("\n[3/4] task1_dataset Statistics...")
    stats = pipeline.get_statistics()
    print(f"    Total records: {stats['total_records']}")
    print(f"    Entity types: {stats['entity_types']}")
    print(f"    AUM distribution: {stats['aum_distribution']}")
    print(f"    Regions: {stats['regions']}")
    
    # Export
    print("\n[4/4] Exporting data...")
    json_path = pipeline.export_json()
    print(f"    Exported to: {json_path}")
    
    # Re-validate exported file
    print("\n[Final] Validating exported task1_dataset...")
    validation = validate_task1_dataset(json_path)
    print(f"    Valid records: {validation['valid_records']}/{validation['total_records']}")
    
    if validation['errors']:
        print(f"    Errors: {len(validation['errors'])}")
        for err in validation['errors'][:5]:
            print(f"      - {err['field']}: {err['message']}")
    
    print("\n" + "=" * 60)
    print("Pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
