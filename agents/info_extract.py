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
    Enhanced with collaborative capabilities for dynamic agent interaction.
    """

    def __init__(self, gemini_client: GeminiClient):
        self._gemini = gemini_client

    def process(self, input_data: DocIntelOutput) -> ExtractionOutput:
        """
        Takes the output from DocIntelAgent and uses Gemini to extract structured data.
        Now handles multiple document types and file formats intelligently.

        Args:
            input_data: The output from the document intelligence agent.

        Returns:
            An ExtractionOutput object containing the structured data.
        """
        # Customize prompt based on document type
        if input_data.doc_type in ["image_document", "image_pdf", "dicom_image"]:
            prompt = self._create_image_extraction_prompt(input_data)
        elif input_data.doc_type in ["word_document", "insurance_word_document"]:
            prompt = self._create_document_extraction_prompt(input_data)
        elif input_data.doc_type == "medical_imaging":
            prompt = self._create_medical_extraction_prompt(input_data)
        else:
            prompt = self._create_standard_extraction_prompt(input_data)

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
    
    def collaborative_extract(self, source_document: DocIntelOutput, focus_areas: list, context: str = "") -> Dict[str, Any]:
        """
        Collaborative method for targeted information extraction requested by other agents.
        
        Args:
            source_document: Original document intelligence output
            focus_areas: List of specific fields or areas to focus on
            context: Additional context from requesting agent
            
        Returns:
            Dict containing the targeted extracted information
        """
        prompt = f"""
        You are performing a collaborative information extraction task requested by another AI agent.
        
        CONTEXT FROM REQUESTING AGENT:
        {context}
        
        FOCUS AREAS REQUESTED:
        {', '.join(focus_areas)}
        
        DOCUMENT CONTENT:
        ---
        {source_document.content}
        ---
        
        Please perform a DEEP, FOCUSED extraction on the requested areas only.
        Look for subtle details, implied information, and cross-references.
        
        For each focus area, provide:
        1. Direct extracted value (if found)
        2. Confidence level (High/Medium/Low)
        3. Additional context or related information found
        4. Potential inconsistencies or red flags
        
        Return as JSON object with this structure:
        {{
            "focus_area_name": {{
                "value": "extracted_value_or_null",
                "confidence": "High/Medium/Low",
                "context": "additional_context_found",
                "red_flags": ["list", "of", "concerns"]
            }}
        }}
        
        Return only the JSON object:
        """
        
        try:
            response = self._gemini.generate_content(prompt=prompt)
            
            # Clean and parse response
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            
            clean_response = clean_response.strip()
            
            # Try to find JSON object
            json_match = re.search(r'\{.*\}', clean_response, re.DOTALL)
            if json_match:
                clean_response = json_match.group(0)
            
            extracted_data = json.loads(clean_response)
            
            return {
                "collaboration_success": True,
                "extracted_data": extracted_data,
                "source_agent": "InfoExtractAgent",
                "focus_areas": focus_areas
            }
            
        except Exception as e:
            return {
                "collaboration_success": False,
                "error": str(e),
                "fallback_data": {},
                "source_agent": "InfoExtractAgent",
                "focus_areas": focus_areas
            }

    def _create_standard_extraction_prompt(self, input_data: DocIntelOutput) -> str:
        """Create standard extraction prompt for PDF documents"""
        return f"""
        Based on the following document analysis, extract the key information
        into a structured JSON object. Please return ONLY the JSON object, no additional text.

        The required fields are:
        - claimant_name (string)
        - policy_number (string)
        - date_of_incident (string, YYYY-MM-DD format)
        - claim_amount (float)
        - vehicle_details (string)
        - incident_description (string)
        - contact_information (object with phone, email, address)

        If a field is not present, use a value of null.

        Document Analysis:
        ---
        {input_data.content}
        ---

        Return only the JSON object:
        """

    def _create_image_extraction_prompt(self, input_data: DocIntelOutput) -> str:
        """Create specialized prompt for image-based documents"""
        return f"""
        This is an image-based insurance document. Please extract ALL visible information
        with special attention to handwritten text, form fields, and visual elements.

        Document Type: {input_data.document_type}
        Processing Method: {input_data.metadata.get('processing_method', 'unknown')}

        Required fields (extract ALL that are visible):
        - claimant_name (string)
        - policy_number (string)
        - date_of_incident (string, YYYY-MM-DD format)
        - claim_amount (float)
        - vehicle_details (string)
        - incident_description (string)
        - contact_information (object)
        - damage_description (string)
        - visible_signatures (boolean)
        - form_completion_percentage (integer 0-100)
        - image_quality_assessment (string)
        - handwritten_vs_printed (object with counts)

        Document Analysis:
        ---
        {input_data.content}
        ---

        Additional Instructions:
        - Pay special attention to form fields that might be partially filled
        - Note any visible damage in photos
        - Identify if signatures are present
        - Assess overall document completeness

        Return only the JSON object:
        """

    def _create_document_extraction_prompt(self, input_data: DocIntelOutput) -> str:
        """Create prompt for Word/document files"""
        return f"""
        This is a structured insurance document (Word format).
        Extract comprehensive information including document metadata.

        Document Format: {input_data.metadata.get('format', 'unknown')}

        Required fields:
        - claimant_name (string)
        - policy_number (string)
        - date_of_incident (string, YYYY-MM-DD format)
        - claim_amount (float)
        - vehicle_details (string)
        - incident_description (string)
        - contact_information (object)
        - document_version (string)
        - document_template_type (string)
        - creation_metadata (object)
        - approval_signatures (array)
        - referenced_attachments (array)

        Document Content:
        ---
        {input_data.content}
        ---

        Special Instructions:
        - Extract any version numbers or template identifiers
        - Identify document creation/modification metadata
        - Look for cross-references to other documents
        - Note any embedded approval workflows

        Return only the JSON object:
        """

    def _create_medical_extraction_prompt(self, input_data: DocIntelOutput) -> str:
        """Create prompt for medical/DICOM files"""
        return f"""
        This is a medical imaging file related to an insurance claim.
        Extract relevant medical and claim information while respecting privacy.

        File Type: {input_data.metadata.get('file_type', 'medical')}

        Required fields:
        - patient_identifier (string, anonymized if needed)
        - imaging_date (string, YYYY-MM-DD format)
        - body_part_examined (string)
        - imaging_modality (string)
        - radiologist_findings (string)
        - related_claim_number (string)
        - medical_facility (string)
        - imaging_quality (string)
        - privacy_compliance_notes (array)
        - medical_necessity_indicators (array)

        Document Analysis:
        ---
        {input_data.content}
        ---

        Privacy Instructions:
        - Anonymize all personal identifiers
        - Focus on claim-relevant medical information only
        - Note any compliance requirements
        - Highlight medical necessity evidence

        Return only the JSON object:
        """