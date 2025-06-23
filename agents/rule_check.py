"""The RuleCheck agent: validates extracted data against business rules."""

from dataclasses import dataclass
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from agents.info_extract import ExtractionOutput

@dataclass
class ValidationResult:
    """Represents the outcome of the validation process."""
    is_valid: bool
    violations: List[str]
    validated_data: Dict[str, Any]
    source_uri: str

class RuleCheckAgent(BaseAgent):
    """
    An agent that validates extracted information against a set of
    pre-defined business rules.
    """

    def process(self, input_data: ExtractionOutput) -> ValidationResult:
        """
        Validates the extracted data against business rules.

        Args:
            input_data: The structured data from the InfoExtractAgent.

        Returns:
            A ValidationResult object with the outcome of the validation.
        """
        violations = []
        data = input_data.extracted_data

        # Rule 1: Check for required fields
        required_fields = ["claimant_name", "policy_number", "claim_amount"]
        for field in required_fields:
            if field not in data or data[field] is None:
                violations.append(f"Missing required field: {field}")

        # Rule 2: Check claim amount
        if "claim_amount" in data and isinstance(data["claim_amount"], (int, float)):
            if not 0 < data["claim_amount"] <= 50000:
                violations.append(f"Claim amount ${data['claim_amount']} is outside the acceptable range (0, 50000].")

        # Rule 3: Check policy number format (simple example)
        if "policy_number" in data and data["policy_number"]:
             if not (isinstance(data["policy_number"], str) and data["policy_number"].startswith("PN-")):
                violations.append(f"Policy number '{data['policy_number']}' has an invalid format.")

        return ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            validated_data=data,
            source_uri=input_data.source_uri,
        ) 