"""
.REGS Table Detector - TUNED FOR YOUR EXACT FORMAT
File: backend/utils/regs_table_detector.py
"""
import re
from typing import List, Dict, Any, Tuple


class RegsTableDetector:
    """Detect register specification tables matching your specific format"""
    
    def __init__(self):
        # Your format: "CTRL (Control)" or "STATUS (Status Register)"
        self.register_name_patterns = [
            r'\b[A-Z][A-Z0-9_]{2,}\s*\([^)]*\)',  # CTRL (Control)
            r'\b(?:CTRL|STATUS|CONFIG|REG|COMMAND|DATA)\b',
        ]
        
        # Your format: "CTRL 4h" or "STATUS 8h" or "0x10"
        self.offset_patterns = [
            r'\b[A-Z][A-Z0-9_]+\s+[0-9A-Fa-f]+h\b',  # CTRL 4h
            r'Offset:\s*[0-9A-Fa-f]+h',
            r'0x[0-9A-Fa-f]{1,8}\b',
        ]
        
        # Your format: "Bits 31 30-16 15-8 7-2 1 0"
        self.bit_diagram_patterns = [
            r'Bits\s+31',  # Almost always starts with "Bits 31"
            r'\d+-\d+',     # Ranges like 30-16, 15-8, 7-2
            r'Bits\s+\d+\s+\d+',  # "Bits 31 30" format
        ]
        
        # Your format: "0b0 (read):", "0b1 (write):"
        self.access_description_patterns = [
            r'0b[01]\s*\((?:read|write)\)',
            r'\(read\):',
            r'\(write\):',
        ]
        
        # Field structure indicators
        self.field_indicators = [
            r'Fields?\s*$',  # Line that just says "Fields"
            r'Field\s+Function',
            r'RESERVED',
        ]
    
    def is_regs_table(self, table_data: Dict[str, Any]) -> Tuple[bool, float]:
        """Check if a table structure is a register table"""
        if not table_data or 'rows' not in table_data:
            return False, 0.0
        
        rows = table_data['rows']
        if not rows or len(rows) < 2:
            return False, 0.0
        
        # Convert to text
        all_text = ' '.join([
            str(cell) for row in rows for cell in row if cell
        ])
        
        return self._check_register_content(all_text, source='table')
    
    def is_regs_text_block(self, text: str) -> Tuple[bool, float]:
        """Check if a text block contains register information"""
        if not text or len(text) < 100:
            return False, 0.0
        
        return self._check_register_content(text, source='text')
    
    def _check_register_content(self, text: str, source: str) -> Tuple[bool, float]:
        """
        Check if content matches YOUR specific register format
        """
        # === CRITICAL PATTERNS FOR YOUR FORMAT ===
        
        # 1. Check for "Bits 31" - this is THE signature of your format
        has_bits_31 = re.search(r'Bits\s+31', text, re.IGNORECASE) is not None
        
        # 2. Check for register name pattern
        has_register_name = any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in self.register_name_patterns
        )
        
        # 3. Check for your offset format (CTRL 4h)
        has_offset = any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in self.offset_patterns
        )
        
        # 4. Check for bit ranges (30-16, 15-8, 7-2)
        bit_range_matches = len(re.findall(r'\d+-\d+', text))
        
        # 5. Check for binary access patterns (0b0 (read):)
        access_matches = sum(
            len(re.findall(pattern, text, re.IGNORECASE))
            for pattern in self.access_description_patterns
        )
        
        # 6. Check for field indicators
        field_matches = sum(
            1 for pattern in self.field_indicators
            if re.search(pattern, text, re.IGNORECASE)
        )
        
        # === SCORING ===
        scores = {
            'bits_31_signature': 0.0,
            'register_name': 0.0,
            'offset': 0.0,
            'bit_ranges': 0.0,
            'access_descriptions': 0.0,
            'field_structure': 0.0,
        }
        
        # "Bits 31" is the STRONGEST indicator (0.30)
        if has_bits_31:
            scores['bits_31_signature'] = 0.30
        
        # Register name (0.20)
        if has_register_name:
            scores['register_name'] = 0.20
        
        # Offset (0.20)
        if has_offset:
            scores['offset'] = 0.20
        
        # Bit ranges like 30-16, 15-8 (0.15)
        if bit_range_matches >= 2:
            scores['bit_ranges'] = 0.15
        elif bit_range_matches >= 1:
            scores['bit_ranges'] = 0.08
        
        # Access descriptions (0.10)
        if access_matches >= 3:
            scores['access_descriptions'] = 0.10
        elif access_matches >= 1:
            scores['access_descriptions'] = 0.05
        
        # Field structure (0.05)
        if field_matches >= 1:
            scores['field_structure'] = 0.05
        
        confidence = sum(scores.values())
        
        # === DECISION ===
        # Must have "Bits 31" OR (register name + offset + bit ranges)
        mandatory_criteria_met = (
            has_bits_31 or 
            (has_register_name and has_offset and bit_range_matches >= 2)
        )
        
        is_regs = mandatory_criteria_met and confidence >= 0.50
        
        if is_regs:
            print(f"    ✅ REGS DETECTED ({source}) - confidence: {confidence:.2f}")
            print(f"       Breakdown: bits31={scores['bits_31_signature']:.2f}, "
                  f"name={scores['register_name']:.2f}, "
                  f"offset={scores['offset']:.2f}, "
                  f"ranges={scores['bit_ranges']:.2f}, "
                  f"access={scores['access_descriptions']:.2f}, "
                  f"fields={scores['field_structure']:.2f}")
        
        return is_regs, confidence
    
    def extract_regs_metadata(self, table_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from register table"""
        metadata = {
            'register_name': None,
            'offset': None,
            'has_bit_fields': False,
            'has_access_modes': False,
            'estimated_width': 32
        }
        
        if not table_data or 'rows' not in table_data:
            return metadata
        
        rows = table_data['rows']
        all_text = ' '.join([str(cell) for row in rows for cell in row if cell])
        
        return self._extract_metadata_from_text(all_text)
    
    def extract_text_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from text block"""
        metadata = {
            'register_name': None,
            'offset': None,
            'has_bit_fields': False,
            'has_access_modes': False,
            'estimated_width': 32
        }
        
        return self._extract_metadata_from_text(text)
    
    def _extract_metadata_from_text(self, text: str) -> Dict[str, Any]:
        """Extract metadata from text - shared implementation"""
        metadata = {
            'register_name': None,
            'offset': None,
            'has_bit_fields': False,
            'has_access_modes': False,
            'estimated_width': 32
        }
        
        # Extract register name - YOUR FORMAT: "CTRL (Control)"
        for pattern in self.register_name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(0)
                # Extract just the register code (CTRL from "CTRL (Control)")
                code_match = re.match(r'([A-Z][A-Z0-9_]+)', name)
                if code_match:
                    metadata['register_name'] = code_match.group(1)
                else:
                    metadata['register_name'] = name.strip()
                break
        
        # Extract offset - YOUR FORMAT: "CTRL 4h" or "0x4"
        for pattern in self.offset_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                offset_str = match.group(0)
                # Extract just the hex value
                hex_match = re.search(r'[0-9A-Fa-f]+h|0x[0-9A-Fa-f]+', offset_str)
                if hex_match:
                    offset_val = hex_match.group(0)
                    # Convert "4h" to "0x4" format
                    if offset_val.endswith('h'):
                        offset_val = '0x' + offset_val[:-1]
                    metadata['offset'] = offset_val
                break
        
        # Check for bit fields
        metadata['has_bit_fields'] = (
            re.search(r'Bits\s+31', text, re.IGNORECASE) is not None or
            len(re.findall(r'\d+-\d+', text)) >= 2
        )
        
        # Check for access modes
        metadata['has_access_modes'] = any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in self.access_description_patterns
        )
        
        return metadata
    
    def format_text_for_gemini(self, text: str, metadata: Dict[str, Any]) -> str:
        """Format text block for Gemini processing"""
        lines = []
        
        # Clear header
        lines.append("=" * 80)
        lines.append("REGISTER SPECIFICATION")
        lines.append("=" * 80)
        lines.append("")
        
        # Add metadata
        if metadata.get('register_name'):
            lines.append(f"Register: {metadata['register_name']}")
        
        if metadata.get('offset'):
            lines.append(f"Offset: {metadata['offset']}")
        
        lines.append("")
        lines.append("Full Register Description:")
        lines.append("-" * 80)
        
        # Add original text
        for line in text.split('\n'):
            line = line.strip()
            if line:
                lines.append(line)
        
        lines.append("-" * 80)
        
        return '\n'.join(lines)
    
    def format_table_for_gemini(self, table_data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Format table data for Gemini processing"""
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("REGISTER SPECIFICATION")
        lines.append("=" * 80)
        lines.append("")
        
        # Metadata
        if metadata.get('register_name'):
            lines.append(f"Register: {metadata['register_name']}")
        
        if metadata.get('offset'):
            lines.append(f"Offset: {metadata['offset']}")
        
        lines.append("")
        lines.append("Register Table:")
        lines.append("-" * 80)
        
        # Format table rows
        rows = table_data.get('rows', [])
        for row in rows:
            formatted_cells = [str(cell) if cell else '' for cell in row]
            lines.append(' | '.join(formatted_cells))
        
        lines.append("-" * 80)
        
        return '\n'.join(lines)
    
    def scan_document_for_regs_tables(
        self,
        blocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Scan document for register tables - YOUR FORMAT
        """
        detected_tables = []
        
        print(f"  🔍 Scanning {len(blocks)} blocks for register specifications...")
        
        for i, block in enumerate(blocks):
            # Check table structures
            if block.get('type') == 'table':
                is_regs, confidence = self.is_regs_table(block)
                
                if is_regs:
                    metadata = self.extract_regs_metadata(block)
                    formatted_text = self.format_table_for_gemini(block, metadata)
                    
                    detected_tables.append({
                        'block_index': i,
                        'confidence': confidence,
                        'table_data': block,
                        'metadata': metadata,
                        'source': 'table',
                        'formatted_text': formatted_text
                    })
                    
                    print(f"  ✅ Block {i}: Register table (confidence: {confidence:.2f})")
                    if metadata['register_name']:
                        print(f"      Register: {metadata['register_name']}")
                    if metadata['offset']:
                        print(f"      Offset: {metadata['offset']}")
            
            # Check text blocks
            elif block.get('type') == 'paragraph':
                text = block.get('text', '')
                
                if len(text) > 100:
                    is_regs, confidence = self.is_regs_text_block(text)
                    
                    if is_regs:
                        metadata = self.extract_text_metadata(text)
                        formatted_text = self.format_text_for_gemini(text, metadata)
                        
                        detected_tables.append({
                            'block_index': i,
                            'confidence': confidence,
                            'raw_text': text,
                            'metadata': metadata,
                            'source': 'text',
                            'formatted_text': formatted_text
                        })
                        
                        print(f"  ✅ Block {i}: Register text (confidence: {confidence:.2f})")
                        if metadata['register_name']:
                            print(f"      Register: {metadata['register_name']}")
                        if metadata['offset']:
                            print(f"      Offset: {metadata['offset']}")
        
        if len(detected_tables) == 0:
            print(f"  ℹ️  No register specifications detected")
            print(f"  💡 Tip: Looking for format like:")
            print(f"      • 'CTRL (Control)'")
            print(f"      • 'CTRL 4h' or '0x4'")
            print(f"      • 'Bits 31 30-16 15-8 7-2 1 0'")
        else:
            print(f"  ✅ Found {len(detected_tables)} register specification(s)")
        
        return detected_tables