"""
Base extractor class for register document extraction
File: backend/extractors/regs_base_extractor.py
"""
from abc import ABC, abstractmethod


class RegsBaseExtractor(ABC):
    """Abstract base class for register document extractors"""
    
    @abstractmethod
    def extract(self, filepath: str) -> str:
        """
        Extract content from document
        
        Args:
            filepath: Path to the document file
            
        Returns:
            str: Extracted content as text
        """
        pass
    
    def get_supported_extensions(self) -> list:
        """
        Get list of supported file extensions
        
        Returns:
            list: List of supported extensions
        """
        return []