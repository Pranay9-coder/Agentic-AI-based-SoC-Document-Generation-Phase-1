"""
Word document extractor for register specification documents
File: backend/extractors/regs_word_extractor.py
"""
from docx import Document
import re
from typing import List, Any
from extractors.regs_base_extractor import RegsBaseExtractor


class RegsWordExtractor(RegsBaseExtractor):
    def __init__(self):
        self.page_content = []
        
    def extract(self, filepath: str) -> str:
        """Extract text and tables from Word document with advanced parsing"""
        content = []
        try:
            doc = Document(filepath)
            print(f"Opening Word document: {len(doc.paragraphs)} paragraphs found")
            
            # Process by sections/pages (Word doesn't have page numbers directly)
            section_num = 1
            current_section = []
            current_section.append(f"\n{'='*80}")
            current_section.append(f"SECTION {section_num}")
            current_section.append(f"{'='*80}\n")
            
            # Extract paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    current_section.append(para.text)
                    
                    # Detect section breaks (headings or page breaks)
                    if para.style.name.startswith('Heading'):
                        if len(current_section) > 3:  # Has content
                            content.extend(current_section)
                            section_num += 1
                            current_section = []
                            current_section.append(f"\n{'='*80}")
                            current_section.append(f"SECTION {section_num}")
                            current_section.append(f"{'='*80}\n")
            
            # Extract tables
            print(f"Found {len(doc.tables)} table(s) in document")
            for idx, table in enumerate(doc.tables, 1):
                table_text = self._format_table_enhanced(table, f"Table {idx}")
                current_section.append(table_text)
            
            # Add register patterns detection
            full_text = '\n'.join([para.text for para in doc.paragraphs])
            register_patterns = self._extract_register_patterns(full_text)
            if register_patterns:
                current_section.append(register_patterns)
            
            # Add final section
            if current_section:
                content.extend(current_section)
            
            return '\n\n'.join(content)
            
        except Exception as e:
            print(f"Error extracting Word document: {e}")
            raise
    
    def _format_table_enhanced(self, table, table_name: str) -> str:
        """Format table with enhanced structure matching PDF extractor"""
        if not table or not table.rows:
            return ""
        
        lines = []
        lines.append(f"\n[{table_name}]")
        lines.append("-" * 80)
        
        for row_idx, row in enumerate(table.rows):
            formatted_cells = []
            for cell in row.cells:
                cell_text = cell.text.strip()
                # Clean whitespace
                cell_text = re.sub(r'\s+', ' ', cell_text)
                formatted_cells.append(cell_text)
            
            # Skip empty rows
            if not any(formatted_cells):
                continue
            
            # Format header row differently
            if row_idx == 0:
                lines.append(' | '.join(formatted_cells))
                lines.append('-' * 80)
            else:
                lines.append(' | '.join(formatted_cells))
        
        lines.append("-" * 80)
        return '\n'.join(lines)
    
    def _extract_register_patterns(self, text: str) -> str:
        """Extract register bit field diagrams and patterns"""
        patterns = []
        
        # Detect bit field diagrams (looking for bit numbers)
        bit_pattern = r'\b(31|30|29|28|27|26|25|24|23|22|21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|3|2|1|0)\b'
        if re.findall(bit_pattern, text):
            patterns.append("\n[BIT FIELD DIAGRAM DETECTED]")
        
        # Extract register names
        register_name_pattern = r'([A-Z][A-Z0-9_]*)\s+(?:Register|Reg\b|Control|Status)'
        register_names = re.findall(register_name_pattern, text)
        if register_names:
            patterns.append(f"[REGISTERS FOUND: {', '.join(set(register_names))}]")
        
        # Extract offset/address information
        offset_pattern = r'(?:Offset|Address):\s*(0x[0-9A-Fa-f]+|[0-9A-Fa-f]+h)'
        offsets = re.findall(offset_pattern, text, re.IGNORECASE)
        if offsets:
            patterns.append(f"[OFFSETS: {', '.join(offsets)}]")
        
        # Extract reset values
        reset_pattern = r'(?:Reset|Default)\s*(?:Value)?:\s*(0x[0-9A-Fa-f]+|[01]+b?)'
        resets = re.findall(reset_pattern, text, re.IGNORECASE)
        if resets:
            patterns.append(f"[RESET VALUES: {', '.join(resets)}]")
        
        return '\n'.join(patterns) if patterns else ""
    
    def get_supported_extensions(self) -> list:
        """Get supported file extensions"""
        return ['.docx', '.doc']