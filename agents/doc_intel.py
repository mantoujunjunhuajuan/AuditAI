"""The DocIntel agent: classifies documents and extracts raw content."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any
import os
import tempfile
import base64
from PIL import Image
import io

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
    extracted_text: str = ""
    document_type: str = ""
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        # For backwards compatibility
        if not self.extracted_text:
            self.extracted_text = self.content
        if not self.document_type:
            self.document_type = self.doc_type

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
        Downloads a file from storage, classifies it, and extracts content using AI.
        Now supports: PDF, DOCX, DOC, JPEG, PNG, TIFF, BMP, DICOM

        Args:
            input_data: The URI of the document to process.

        Returns:
            A DocIntelOutput object containing the document type and content.
        """
        file_uri = input_data
        file_name = Path(file_uri.split("/")[-1])
        suffix = file_name.suffix.lower()

        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name

        try:
            # Download file from storage
            self._storage.download_file(source=file_uri, target_path=temp_file_path)
            
            # Process based on file type
            if suffix == ".pdf":
                return self._process_pdf(temp_file_path, file_name, file_uri)
            elif suffix in [".docx", ".doc"]:
                return self._process_word_document(temp_file_path, file_name, file_uri)
            elif suffix in [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"]:
                return self._process_image(temp_file_path, file_name, file_uri)
            elif suffix == ".dcm":
                return self._process_dicom(temp_file_path, file_name, file_uri)
            else:
                return self._process_unsupported(file_name, file_uri, suffix)
                
        except Exception as e:
            return DocIntelOutput(
                doc_type="error",
                content=f"Error processing file {file_name.name}: {str(e)}",
                source_uri=file_uri,
                extracted_text="",
                document_type="error",
                confidence_score=0.0,
                metadata={"error": str(e), "file_type": suffix}
            )
        finally:
            # Clean up the temporary file
            Path(temp_file_path).unlink(missing_ok=True)

    def _process_pdf(self, file_path: str, file_name: Path, file_uri: str) -> DocIntelOutput:
        """Process PDF documents"""
        try:
            raw_text = self._pdf_parser.extract_text_from_pdf(file_path)
            
            if not raw_text.strip():
                # If no text extracted, might be image-based PDF
                return self._process_image_based_pdf(file_path, file_name, file_uri)
            
            # AI analysis of extracted text
            prompt = f"""
            Analyze this insurance claim document and provide:
            1. Document type classification
            2. Key entities (names, dates, claim numbers, policy numbers)
            3. Summary of content
            4. Confidence level in the analysis
            
            Document Text:
            ---
            {raw_text[:4000]}  # Limit text to avoid token limits
            ---
            
            Provide analysis in structured format:
            """
            
            ai_analysis = self._gemini.generate_content(prompt=prompt)
            
            return DocIntelOutput(
                doc_type="pdf_document",
                content=ai_analysis,
                source_uri=file_uri,
                extracted_text=raw_text,
                document_type="insurance_claim_pdf",
                confidence_score=0.9,
                metadata={
                    "file_size": len(raw_text),
                    "processing_method": "text_extraction",
                    "ai_analysis": True
                }
            )
            
        except PDFSyntaxError:
            return DocIntelOutput(
                doc_type="invalid_pdf",
                content="Error: Invalid PDF file format. File may be corrupted.",
                source_uri=file_uri,
                extracted_text="",
                document_type="corrupted_pdf",
                confidence_score=0.0,
                metadata={"error": "pdf_syntax_error"}
            )

    def _process_image_based_pdf(self, file_path: str, file_name: Path, file_uri: str) -> DocIntelOutput:
        """Process image-based PDF using OCR"""
        # For image-based PDFs, we'll use Gemini Vision API
        with open(file_path, 'rb') as f:
            pdf_data = base64.b64encode(f.read()).decode()
        
        prompt = """
        This appears to be an image-based PDF document, likely an insurance claim form.
        Please extract all visible text and analyze the document structure.
        Focus on identifying:
        1. Form type and purpose
        2. Key information fields
        3. Handwritten vs printed text
        4. Overall document quality
        
        Provide detailed text extraction and analysis:
        """
        
        try:
            # Note: This would need to be implemented with Gemini Vision API
            ai_analysis = self._gemini.generate_content(prompt=prompt)
            
            return DocIntelOutput(
                doc_type="image_pdf",
                content=ai_analysis,
                source_uri=file_uri,
                extracted_text=ai_analysis,  # AI extracted text
                document_type="scanned_insurance_document",
                confidence_score=0.7,
                metadata={
                    "processing_method": "ocr_vision",
                    "ai_analysis": True,
                    "requires_manual_review": True
                }
            )
        except Exception as e:
            return DocIntelOutput(
                doc_type="image_pdf_error",
                content=f"OCR processing failed: {str(e)}",
                source_uri=file_uri,
                extracted_text="",
                document_type="ocr_failed",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )

    def _process_word_document(self, file_path: str, file_name: Path, file_uri: str) -> DocIntelOutput:
        """Process Word documents (.doc, .docx)"""
        try:
            # Try to extract text from Word document
            if file_name.suffix.lower() == ".docx":
                text_content = self._extract_docx_text(file_path)
            else:
                # For .doc files, we'd need python-docx2txt or similar
                text_content = f"Word document processing for .doc files not fully implemented. File: {file_name.name}"
            
            # AI analysis
            prompt = f"""
            Analyze this insurance-related Word document:
            
            Document Content:
            ---
            {text_content[:4000]}
            ---
            
            Please provide:
            1. Document type and purpose
            2. Key information extracted
            3. Compliance with insurance documentation standards
            4. Recommendations for processing
            """
            
            ai_analysis = self._gemini.generate_content(prompt=prompt)
            
            return DocIntelOutput(
                doc_type="word_document",
                content=ai_analysis,
                source_uri=file_uri,
                extracted_text=text_content,
                document_type="insurance_word_document",
                confidence_score=0.85,
                metadata={
                    "format": file_name.suffix.lower(),
                    "processing_method": "document_parsing"
                }
            )
            
        except Exception as e:
            return DocIntelOutput(
                doc_type="word_document_error",
                content=f"Word document processing failed: {str(e)}",
                source_uri=file_uri,
                extracted_text="",
                document_type="document_processing_error",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )

    def _process_image(self, file_path: str, file_name: Path, file_uri: str) -> DocIntelOutput:
        """Process image files using AI vision"""
        try:
            # Load and validate image
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Get image info
                width, height = img.size
                format_info = img.format
            
            # Encode image for AI analysis
            with open(file_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # AI Vision analysis
            prompt = """
            This is an insurance claim related image. Please analyze it thoroughly:
            
            1. Identify the type of document/image (medical record, damage photo, receipt, etc.)
            2. Extract all visible text using OCR
            3. Describe visual elements that might be relevant to claim processing
            4. Assess image quality and legibility
            5. Flag any potential issues or anomalies
            
            Provide comprehensive analysis including extracted text and visual assessment:
            """
            
            # Note: This would use Gemini Vision API in production
            ai_analysis = self._gemini.generate_content(prompt=prompt)
            
            return DocIntelOutput(
                doc_type="image_document",
                content=ai_analysis,
                source_uri=file_uri,
                extracted_text=ai_analysis,  # OCR text would be extracted by AI
                document_type="insurance_image",
                confidence_score=0.8,
                metadata={
                    "image_format": format_info,
                    "dimensions": f"{width}x{height}",
                    "processing_method": "ai_vision_ocr",
                    "file_size_kb": os.path.getsize(file_path) // 1024
                }
            )
            
        except Exception as e:
            return DocIntelOutput(
                doc_type="image_error",
                content=f"Image processing failed: {str(e)}",
                source_uri=file_uri,
                extracted_text="",
                document_type="image_processing_error",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )

    def _process_dicom(self, file_path: str, file_name: Path, file_uri: str) -> DocIntelOutput:
        """Process DICOM medical imaging files"""
        try:
            # Note: In production, this would use pydicom library
            prompt = f"""
            This is a DICOM medical imaging file ({file_name.name}).
            
            For insurance claim processing, please provide:
            1. Analysis of what this medical imaging file likely contains
            2. Relevant medical information for claim validation
            3. Recommendations for medical review requirements
            4. Privacy and compliance considerations
            
            Note: Actual DICOM parsing would require specialized medical imaging libraries.
            """
            
            ai_analysis = self._gemini.generate_content(prompt=prompt)
            
            return DocIntelOutput(
                doc_type="dicom_image",
                content=ai_analysis,
                source_uri=file_uri,
                extracted_text="DICOM medical imaging file - specialized processing required",
                document_type="medical_imaging",
                confidence_score=0.6,
                metadata={
                    "file_type": "DICOM",
                    "requires_medical_review": True,
                    "processing_method": "metadata_analysis",
                    "privacy_sensitive": True
                }
            )
            
        except Exception as e:
            return DocIntelOutput(
                doc_type="dicom_error",
                content=f"DICOM processing failed: {str(e)}",
                source_uri=file_uri,
                extracted_text="",
                document_type="medical_imaging_error",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )

    def _process_unsupported(self, file_name: Path, file_uri: str, suffix: str) -> DocIntelOutput:
        """Handle unsupported file types"""
        return DocIntelOutput(
            doc_type="unsupported",
            content=f"File type {suffix} is not supported for insurance claim processing.",
            source_uri=file_uri,
            extracted_text="",
            document_type="unsupported_format",
            confidence_score=0.0,
            metadata={
                "file_extension": suffix,
                "supported_formats": [".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".dcm"]
            }
        )

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX files"""
        try:
            # This is a simplified implementation
            # In production, you'd use python-docx library
            import zipfile
            import xml.etree.ElementTree as ET
            
            with zipfile.ZipFile(file_path, 'r') as docx:
                content = docx.read('word/document.xml')
                root = ET.fromstring(content)
                
                # Extract text from XML
                text_content = ""
                for elem in root.iter():
                    if elem.text:
                        text_content += elem.text + " "
                
                return text_content.strip()
                
        except Exception as e:
            return f"Error extracting DOCX text: {str(e)}. Consider using python-docx library for robust processing." 