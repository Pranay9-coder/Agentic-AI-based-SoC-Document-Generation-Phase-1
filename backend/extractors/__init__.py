"""
Extractors package for document content extraction
"""
# Existing DITA extractors
from .docx_extractor import extract_docx
from .pdf_extractor import extract_pdf

# New REGS extractors
from .regs_base_extractor import RegsBaseExtractor
from .regs_excel_extractor import RegsExcelExtractor
from .regs_pdf_extractor import RegsPDFExtractor
from .regs_word_extractor import RegsWordExtractor

__all__ = [
    # DITA extractors
    'extract_docx',
    'extract_pdf',
    # REGS extractors
    'RegsBaseExtractor',
    'RegsExcelExtractor',
    'RegsPDFExtractor',
    'RegsWordExtractor'
]