"""The DocIntel agent: classifies documents and extracts raw content."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any

from agents.base_agent import BaseAgent
from services.storage_service import IStorageService
from services.gemini_client import GeminiClient
from utils.pdf_parser import PDFParser
from pdfminer.pdfparser import PDFSyntaxError

@dataclass
class DocIntelOutput:
    doc_type: str
    content: str
    source_uri: str

class DocIntelAgent(BaseAgent):
    """
    An agent that classifies a document based on its file type and
    extracts its raw content (text from PDF, description from image).
    """

    def __init__(
        self,
        storage_service: IStorageService,
        pdf_parser: PDFParser,
        gemini_client: GeminiClient,
    ):
        self._storage = storage_service
        self._pdf_parser = pdf_parser
        self._gemini = gemini_client

    def process(self, input_data: str) -> DocIntelOutput:
        """
        Downloads a file from GCS, classifies it, and extracts content.

        Args:
            input_data: The gs:// URI of the document to process.

        Returns:
            A DocIntelOutput object containing the document type and content.
        """
        gcs_uri = input_data
        file_name = Path(gcs_uri.split("/")[-1])
        suffix = file_name.suffix.lower()

        # In a real-world scenario, you might stream this for large files
        # For the hackathon, downloading to a temp file is sufficient.
        temp_file_path = f"/tmp/{file_name.name}"
        self._storage.download_file(source=gcs_uri, target_path=temp_file_path)
        
        content: str
        doc_type: str

        try:
            if suffix == ".pdf":
                doc_type = "pdf_document"
                try:
                    raw_text = self._pdf_parser.extract_text_from_pdf(temp_file_path)
                except PDFSyntaxError:
                    raw_text = "" # Or set a specific error message
                    content = "Error: Invalid PDF file, could not extract text."
                    doc_type = "invalid_pdf"

                if doc_type != "invalid_pdf":
                    # Use Gemini to analyze the extracted text
                    prompt = f"""
                    Analyze the following document text and provide a concise summary
                    and extract key entities such as names, dates, and claim numbers.
                    
                    Document Text:
                    ---
                    {raw_text}
                    ---
                    
                    Analysis:
                    """
                    content = self._gemini.generate_content(prompt=prompt)
                
            elif suffix in [".jpg", ".jpeg", ".png"]:
                doc_type = "image"
                # Gemini Vision integration will be handled by a later agent.
                content = f"Placeholder for image analysis of {file_name.name}"
            else:
                doc_type = "unsupported"
                content = f"Unsupported file type: {suffix}"
        finally:
            # Clean up the temporary file
            Path(temp_file_path).unlink(missing_ok=True)

        return DocIntelOutput(
            doc_type=doc_type,
            content=content,
            source_uri=gcs_uri
        ) 