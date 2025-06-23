"""PDF text extraction utility."""
import os
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

class PDFParser:
    """A class to handle PDF text extraction."""

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extracts text from a PDF file at the given path.

        Args:
            pdf_path: The path to the PDF file.

        Returns:
            The extracted text as a single string.
        
        Raises:
            FileNotFoundError: If the pdf_path does not exist.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"No such file or directory: '{pdf_path}'")
        
        # Using LAParams to improve layout analysis can sometimes yield better results
        laparams = LAParams()
        text = extract_text(pdf_path, laparams=laparams)
        return text.strip() 