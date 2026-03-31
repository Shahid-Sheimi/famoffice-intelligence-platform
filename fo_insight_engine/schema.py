"""
Family Office Intelligence task1_dataset Schema Validation

This module provides schema validation for the family office task1_dataset
to ensure data quality and decision-grade reliability.
"""

import logging
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


# Valid entity types for classification
VALID_ENTITY_TYPES = [
    "Single Family Office",
    "Multi Family Office",
    "Wealth Manager",
    "Family Holding Company",
    "Corporate Family Office",
    "Sovereign Wealth Fund",
    "Pension Fund",
    "Hedge Fund",
    "Venture Capital",
    "Private Equity",
]

# Valid AUM ranges
VALID_AUM_RANGES = [
    "$500M-$1B",
    "$1B-$5B",
    "$5B-$10B",
    "$10B+",
]

# Valid confidence scores
VALID_CONFIDENCE_SCORES = ["High", "Medium", "Low"]

# Valid investment stages
VALID_STAGES = [
    "Seed",
    "Early-stage",
    "Growth",
    "Late-stage",
    "Buyout",
    "All stages",
    "Fund allocation",
    "Project finance",
    "Distressed",
]

# Country code mapping
COUNTRY_CODE_MAP = {
    "USA": "US",
    "United States": "US",
    "UK": "GB",
    "United Kingdom": "GB",
    "UAE": "AE",
    "United Arab Emirates": "AE",
}


@dataclass
class ValidationError:
    """Represents a validation error."""
    field: str
    message: str
    severity: str = "error"


class FamilyOfficeSchema:
    """Schema validator for family office records.

    Ensures data quality through field-level validation,
    cross-field checks, and data standardization.
    """
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        logger.info("[SCHEMA] FamilyOfficeSchema class initialized")
    
    def validate_record(self, record: Dict[str, Any]) -> bool:
        """
        Validate a single family office record.
        
        Args:
            record: Dictionary containing family office data
            
        Returns:
            True if valid, False otherwise
        """
        self.errors = []
        self.warnings = []
        
        # Required fields validation
        self._validate_required_fields(record)
        
        # Entity type validation
        self._validate_entity_type(record)
        
        # AUM validation
        self._validate_aum(record)
        
        # Confidence score validation
        self._validate_confidence(record)
        
        # Source links validation
        self._validate_sources(record)
        
        # Investment focus validation
        self._validate_investment_focus(record)
        
        # Location validation
        self._validate_location(record)
        
        # Data verification date
        self._validate_verification_date(record)
        
        return len(self.errors) == 0
    
    def _validate_required_fields(self, record: Dict[str, Any]) -> None:
        """Check all required fields are present."""
        required = ["name", "location", "aum_estimate", "investment_focus", 
                    "stage", "source_links", "confidence_score", "entity_type"]
        
        for field in required:
            if field not in record or not record[field]:
                self.errors.append(ValidationError(
                    field=field,
                    message=f"Required field '{field}' is missing or empty"
                ))
    
    def _validate_entity_type(self, record: Dict[str, Any]) -> None:
        """Validate entity_type is recognized."""
        entity_type = record.get("entity_type", "")
        if entity_type and entity_type not in VALID_ENTITY_TYPES:
            self.warnings.append(ValidationError(
                field="entity_type",
                message=f"Unknown entity type: {entity_type}",
                severity="warning"
            ))
    
    def _validate_aum(self, record: Dict[str, Any]) -> None:
        """Validate AUM range format."""
        aum = record.get("aum_estimate", "")
        if aum and aum not in VALID_AUM_RANGES:
            self.errors.append(ValidationError(
                field="aum_estimate",
                message=f"Invalid AUM range: {aum}. Must be one of {VALID_AUM_RANGES}"
            ))
    
    def _validate_confidence(self, record: Dict[str, Any]) -> None:
        """Validate confidence score."""
        confidence = record.get("confidence_score", "")
        if confidence and confidence not in VALID_CONFIDENCE_SCORES:
            self.errors.append(ValidationError(
                field="confidence_score",
                message=f"Invalid confidence: {confidence}. Must be High, Medium, or Low"
            ))
    
    def _validate_sources(self, record: Dict[str, Any]) -> None:
        """Validate source links."""
        sources = record.get("source_links", [])
        
        if not sources:
            self.errors.append(ValidationError(
                field="source_links",
                message="At least one source link is required"
            ))
            return
        
        # Check for valid URLs
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        for source in sources:
            if not url_pattern.match(source):
                self.warnings.append(ValidationError(
                    field="source_links",
                    message=f"Invalid URL format: {source}",
                    severity="warning"
                ))
        
        # Warning for single source (less reliable)
        if len(sources) == 1:
            self.warnings.append(ValidationError(
                field="source_links",
                message="Only one source provided - recommend multiple sources for decision-grade data",
                severity="warning"
            ))
    
    def _validate_investment_focus(self, record: Dict[str, Any]) -> None:
        """Validate investment focus."""
        focus = record.get("investment_focus", "")
        if not focus:
            self.warnings.append(ValidationError(
                field="investment_focus",
                message="Investment focus is empty",
                severity="warning"
            ))
    
    def _validate_location(self, record: Dict[str, Any]) -> None:
        """Validate location format."""
        location = record.get("location", "")
        if location and "," not in location:
            self.warnings.append(ValidationError(
                field="location",
                message="Location should include city and country (e.g., 'New York, USA')",
                severity="warning"
            ))
    
    def _validate_verification_date(self, record: Dict[str, Any]) -> None:
        """Validate data verification timestamp."""
        verified = record.get("data_verified", "")
        if verified:
            try:
                datetime.strptime(verified, "%Y-%m-%d")
            except ValueError:
                self.warnings.append(ValidationError(
                    field="data_verified",
                    message="Invalid date format - should be YYYY-MM-DD",
                    severity="warning"
                ))
    
    def get_errors(self) -> List[ValidationError]:
        """Return all validation errors."""
        return self.errors
    
    def get_warnings(self) -> List[ValidationError]:
        """Return all validation warnings."""
        return self.warnings
    
    def standardize_country_code(self, country: str) -> str:
        """Convert country name to ISO code."""
        return COUNTRY_CODE_MAP.get(country, country)
    
    def normalize_aum(self, aum_str: str) -> str:
        """Normalize AUM string format."""
        # Already in standard format
        if aum_str in VALID_AUM_RANGES:
            return aum_str
        
        # Try to normalize
        aum_str = aum_str.upper().replace(" ", "")
        
        if "BILLION" in aum_str or "B" in aum_str:
            num = float(re.findall(r'[\d.]+', aum_str)[0]) if re.findall(r'[\d.]+', aum_str) else 0
            if num >= 10:
                return "$10B+"
            elif num >= 5:
                return "$5B-$10B"
            elif num >= 1:
                return "$1B-$5B"
        
        if "MILLION" in aum_str or "M" in aum_str:
            num = float(re.findall(r'[\d.]+', aum_str)[0]) if re.findall(r'[\d.]+', aum_str) else 0
            if num >= 500:
                return "$500M-$1B"
        
        return aum_str


def validate_task1_dataset(filepath: str) -> Dict[str, Any]:
    """
    Validate entire task1_dataset file.
    
    Args:
        filepath: Path to JSON task1_dataset
        
    Returns:
        Dictionary with validation results
    """
    import json
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    validator = FamilyOfficeSchema()
    results = {
        "total_records": len(data),
        "valid_records": 0,
        "invalid_records": 0,
        "errors": [],
        "warnings": [],
        "record_results": []
    }
    
    for i, record in enumerate(data):
        is_valid = validator.validate_record(record)
        record_result = {
            "index": i,
            "name": record.get("name", "Unknown"),
            "valid": is_valid,
            "errors": [e.__dict__ for e in validator.get_errors()],
            "warnings": [w.__dict__ for w in validator.get_warnings()]
        }
        
        if is_valid:
            results["valid_records"] += 1
        else:
            results["invalid_records"] += 1
            results["errors"].extend([e.__dict__ for e in validator.get_errors()])
        
        results["warnings"].extend([w.__dict__ for w in validator.get_warnings()])
        results["record_results"].append(record_result)
    
    return results


if __name__ == "__main__":
    # Run validation
    results = validate_task1_dataset("../task1_dataset/family_offices_decision_grade.json")
    print(f"Total records: {results['total_records']}")
    print(f"Valid: {results['valid_records']}")
    print(f"Invalid: {results['invalid_records']}")
    print(f"Total errors: {len(results['errors'])}")
    print(f"Total warnings: {len(results['warnings'])}")
