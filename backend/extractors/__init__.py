"""
Extractors package for document content extraction
"""
from .docx_extractor import extract_docx
from .pdf_extractor import extract_pdf

__all__ = ['extract_docx', 'extract_pdf']
