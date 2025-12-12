"""
PDF extractor for register specification documents
File: backend/extractors/regs_pdf_extractor.py
"""
import pdfplumber
import re
from typing import List, Any
from extractors.regs_base_extractor import RegsBaseExtractor


class RegsPDFExtractor(RegsBaseExtractor):
    def __init__(self):
        self.page_content = []
        
    def extract(self, filepath: str) -> str:
        """Extract text and tables from PDF with advanced parsing"""
        content = []
        try:
            with pdfplumber.open(filepath) as pdf:
                print(f"Opening PDF: {len(pdf.pages)} pages found")
                for page_num, page in enumerate(pdf.pages, 1):
                    print(f"Processing page {page_num}...")
                    page_content = []
                    page_content.append(f"\n{'='*80}")
                    page_content.append(f"PAGE {page_num}")
                    page_content.append(f"{'='*80}\n")
                    
                    text = self._extract_text_with_layout(page)
                    if text:
                        page_content.append(text)
                    
                    tables = page.extract_tables()
                    if tables:
                        print(f"  Found {len(tables)} table(s) on page {page_num}")
                        for idx, table in enumerate(tables, 1):
                            table_text = self._format_table_enhanced(table, f"Table {page_num}.{idx}")
                            page_content.append(table_text)
                    
                    register_patterns = self._extract_register_patterns(page)
                    if register_patterns:
                        page_content.append(register_patterns)
                    
                    content.extend(page_content)
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            raise
        
        return '\n\n'.join(content)
    
    def _extract_text_with_layout(self, page) -> str:
        """Extract text while preserving layout"""
        try:
            text = page.extract_text(layout=True)
            if text:
                return text
        except:
            pass
        return page.extract_text() or ""
    
    def _format_table_enhanced(self, table: List[List[Any]], table_name: str) -> str:
        """Format table with enhanced structure"""
        if not table or not any(table):
            return ""
        
        lines = []
        lines.append(f"\n[{table_name}]")
        lines.append("-" * 80)
        
        for row_idx, row in enumerate(table):
            if not row:
                continue
            
            formatted_cells = []
            for cell in row:
                if cell is None or cell == '':
                    formatted_cells.append('')
                else:
                    cell_text = str(cell).strip()
                    cell_text = re.sub(r'\s+', ' ', cell_text)
                    formatted_cells.append(cell_text)
            
            if not any(formatted_cells):
                continue
            
            if row_idx == 0:
                lines.append(' | '.join(formatted_cells))
                lines.append('-' * 80)
            else:
                lines.append(' | '.join(formatted_cells))
        
        lines.append("-" * 80)
        return '\n'.join(lines)
    
    def _extract_register_patterns(self, page) -> str:
        """Extract register bit field diagrams and patterns"""
        text = page.extract_text() or ""
        patterns = []
        
        bit_pattern = r'\b(31|30|29|28|27|26|25|24|23|22|21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|3|2|1|0)\b'
        if re.findall(bit_pattern, text):
            patterns.append("\n[BIT FIELD DIAGRAM DETECTED]")
        
        register_name_pattern = r'([A-Z][A-Z0-9_]*)\s+(?:Register|Reg\b|Control|Status)'
        register_names = re.findall(register_name_pattern, text)
        if register_names:
            patterns.append(f"[REGISTERS FOUND: {', '.join(set(register_names))}]")
        
        offset_pattern = r'(?:Offset|Address):\s*(0x[0-9A-Fa-f]+|[0-9A-Fa-f]+h)'
        offsets = re.findall(offset_pattern, text, re.IGNORECASE)
        if offsets:
            patterns.append(f"[OFFSETS: {', '.join(offsets)}]")
        
        reset_pattern = r'(?:Reset|Default)\s*(?:Value)?:\s*(0x[0-9A-Fa-f]+|[01]+b?)'
        resets = re.findall(reset_pattern, text, re.IGNORECASE)
        if resets:
            patterns.append(f"[RESET VALUES: {', '.join(resets)}]")
        
        return '\n'.join(patterns) if patterns else ""
    
    def get_supported_extensions(self) -> list:
        """Get supported file extensions"""
        return ['.pdf']