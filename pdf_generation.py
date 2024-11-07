import streamlit as st
import os
from pathlib import Path
from markdown_pdf import MarkdownPdf, Section



# Get base directory and temp settings
BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_ROOT = os.environ.get('TEMP_ROOT', BASE_DIR / 'temp')
TEMP_URL = os.environ.get('TEMP_URL', '/temp/')

# Ensure temp directory exists
os.makedirs(TEMP_ROOT, exist_ok=True)


def create_pdf(text: str, filename: str) -> bytes:
    """
    Creates a PDF from markdown text and returns the PDF content.
    Uses the configured TEMP_ROOT directory.
    
    Args:
        text: Markdown text to convert
        filename: Output filename
        
    Returns:
        bytes: The PDF content
    """
    try:
        # Create the full path for the PDF in the temp directory
        temp_pdf_path = os.path.join(TEMP_ROOT, filename)
        
        # Create the PDF
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(text))
        pdf.save(temp_pdf_path)
        
        # Read the PDF content
        with open(temp_pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
            
        # Clean up the temporary file
        try:
            os.remove(temp_pdf_path)
        except Exception as cleanup_error:
            st.warning(f"Warning: Could not clean up temporary file: {cleanup_error}")
        
        return pdf_content
    except Exception as e:
        raise Exception(f"Error creating PDF: {str(e)}")
