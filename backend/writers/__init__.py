"""
Writers package for output generation
"""
from .dita_writer import write_topics_and_map
from .pdf_writer import write_pdf

__all__ = ['write_topics_and_map', 'write_pdf']

