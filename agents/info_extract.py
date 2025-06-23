"""The InfoExtract agent: extracts structured data from analyzed documents."""

import json
import re
from dataclasses import dataclass
from typing import Dict, Any

from agents.base_agent import BaseAgent
from agents.doc_intel import DocIntelOutput
from services.gemini_client import GeminiClient

@dataclass
class ExtractionOutput:
    """Represents the structured data extracted from a document."""
    extracted_data: Dict[str, Any]
    source_uri: str

class InfoExtractAgent(BaseAgent):
    """
    An agent that uses Gemini to extract structured information from the
    text content provided by the DocIntelAgent.
    """

    def __init__(self, gemini_client: GeminiClient):
        self._gemini = gemini_client

    def process(self, input_data: DocIntelOutput) -> ExtractionOutput:
        """
        Takes the output from DocIntelAgent and uses Gemini to extract structured data.

        Args:
            input_data: The output from the document intelligence agent.

        Returns:
            An ExtractionOutput object containing the structured data.
        """
        prompt = f"""
        Based on the following document analysis, extract the key information
        into a structured JSON object. Please return ONLY the JSON object, no additional text.

        The required fields are:
        - claimant_name (string)
        - policy_number (string)
        - date_of_incident (string, YYYY-MM-DD format)
        - claim_amount (float)
        - vehicle_details (string)

        If a field is not present, use a value of null.

        Document Analysis:
        ---
        {input_data.content}
        ---

        Return only the JSON object:
        """

        # Get the response from Gemini
        extracted_json_string = self._gemini.generate_content(prompt=prompt)
        
        # Parse the JSON response safely
        try:
            # Clean the response by removing any code block markers
            clean_json_string = extracted_json_string.strip()
            
            # Remove markdown code blocks if present
            if clean_json_string.startswith("```json"):
                clean_json_string = clean_json_string[7:]
            if clean_json_string.startswith("```"):
                clean_json_string = clean_json_string[3:]
            if clean_json_string.endswith("```"):
                clean_json_string = clean_json_string[:-3]
            
            clean_json_string = clean_json_string.strip()
            
            # Try to find JSON object in the response using regex
            json_match = re.search(r'\{.*\}', clean_json_string, re.DOTALL)
            if json_match:
                clean_json_string = json_match.group(0)
            
            # Parse the JSON safely
            extracted_data = json.loads(clean_json_string)
            
        except (json.JSONDecodeError, AttributeError) as e:
            # Fallback if parsing fails
            print(f"⚠️ Warning: Failed to parse JSON from Gemini response: {e}")
            print(f"Raw response: {extracted_json_string}")
            extracted_data = {
                "error": "Failed to parse extraction model output",
                "raw_output": extracted_json_string,
                "claimant_name": None,
                "policy_number": None,
                "date_of_incident": None,
                "claim_amount": None,
                "vehicle_details": None
            }

        return ExtractionOutput(
            extracted_data=extracted_data,
            source_uri=input_data.source_uri,
        ) 