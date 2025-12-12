"""
Excel extractor for register specification documents
File: backend/extractors/regs_excel_extractor.py
"""
import pandas as pd
import re
from typing import List, Any, Optional
from extractors.regs_base_extractor import RegsBaseExtractor


class RegsExcelExtractor(RegsBaseExtractor):
    def __init__(self):
        self.sheet_content = []
        
    def extract(self, filepath: str) -> str:
        """Extract data from Excel with advanced parsing and pattern detection"""
        content = []
        try:
            excel_file = pd.ExcelFile(filepath)
            print(f"Opening Excel: {len(excel_file.sheet_names)} sheet(s) found")
            
            for sheet_idx, sheet_name in enumerate(excel_file.sheet_names, 1):
                print(f"Processing sheet {sheet_idx}: {sheet_name}...")
                sheet_content = []
                
                # Sheet header
                sheet_content.append(f"\n{'='*80}")
                sheet_content.append(f"SHEET {sheet_idx}: {sheet_name}")
                sheet_content.append(f"{'='*80}\n")
                
                # Read the sheet
                df = pd.read_excel(filepath, sheet_name=sheet_name)
                
                # Extract main data with layout preservation
                if not df.empty:
                    data_text = self._extract_data_with_layout(df, sheet_name)
                    if data_text:
                        sheet_content.append(data_text)
                
                # Detect and extract tables
                tables = self._detect_tables(df, sheet_name)
                if tables:
                    print(f"  Found {len(tables)} table region(s) in sheet {sheet_name}")
                    for idx, table_info in enumerate(tables, 1):
                        table_text = self._format_table_enhanced(
                            table_info['data'], 
                            f"Table {sheet_idx}.{idx}",
                            table_info.get('header_row')
                        )
                        sheet_content.append(table_text)
                
                # Extract register patterns
                register_patterns = self._extract_register_patterns(df, sheet_name)
                if register_patterns:
                    sheet_content.append(register_patterns)
                
                # Detect numeric patterns and statistics
                numeric_info = self._extract_numeric_patterns(df)
                if numeric_info:
                    sheet_content.append(numeric_info)
                
                content.extend(sheet_content)
                
        except Exception as e:
            print(f"Error extracting Excel: {e}")
            raise
        
        return '\n\n'.join(content)
    
    def _extract_data_with_layout(self, df: pd.DataFrame, sheet_name: str) -> str:
        """Extract data while preserving layout and structure"""
        try:
            if df.empty:
                return ""
            
            # Convert to string representation with proper formatting
            output_lines = []
            
            # Add column headers
            headers = ' | '.join([str(col) for col in df.columns])
            output_lines.append(headers)
            output_lines.append('-' * len(headers))
            
            # Add data rows
            for idx, row in df.iterrows():
                row_text = ' | '.join([self._format_cell(val) for val in row])
                output_lines.append(row_text)
            
            return '\n'.join(output_lines)
        except Exception as e:
            print(f"Error extracting layout: {e}")
            return df.to_string()
    
    def _format_cell(self, value: Any) -> str:
        """Format individual cell values"""
        if pd.isna(value) or value is None or value == '':
            return ''
        
        # Clean and format cell text
        cell_text = str(value).strip()
        cell_text = re.sub(r'\s+', ' ', cell_text)
        
        return cell_text
    
    def _detect_tables(self, df: pd.DataFrame, sheet_name: str) -> List[dict]:
        """Detect distinct table regions within the sheet"""
        tables = []
        
        if df.empty:
            return tables
        
        # For now, treat entire non-empty dataframe as one table
        # You can enhance this to detect multiple tables by finding empty rows/columns
        if not df.dropna(how='all').empty:
            tables.append({
                'data': df,
                'header_row': 0,
                'name': sheet_name
            })
        
        return tables
    
    def _format_table_enhanced(self, df: pd.DataFrame, table_name: str, 
                                header_row: Optional[int] = 0) -> str:
        """Format table with enhanced structure matching PDF style"""
        if df.empty:
            return ""
        
        lines = []
        lines.append(f"\n[{table_name}]")
        lines.append("-" * 80)
        
        # Format headers
        headers = []
        for col in df.columns:
            if pd.notna(col) and col != '':
                headers.append(self._format_cell(col))
            else:
                headers.append('')
        
        if any(headers):
            lines.append(' | '.join(headers))
            lines.append('-' * 80)
        
        # Format data rows
        for idx, row in df.iterrows():
            formatted_cells = [self._format_cell(val) for val in row]
            
            # Skip completely empty rows
            if not any(formatted_cells):
                continue
            
            lines.append(' | '.join(formatted_cells))
        
        lines.append("-" * 80)
        return '\n'.join(lines)
    
    def _extract_register_patterns(self, df: pd.DataFrame, sheet_name: str) -> str:
        """Extract register bit field patterns and hardware register information"""
        if df.empty:
            return ""
        
        patterns = []
        
        # Convert entire dataframe to text for pattern matching
        df_text = df.to_string()
        
        # Detect bit field patterns (common in register documentation)
        bit_pattern = r'\b(31|30|29|28|27|26|25|24|23|22|21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|3|2|1|0)\b'
        bit_matches = re.findall(bit_pattern, df_text)
        if len(bit_matches) > 5:  # Threshold to indicate bit field diagram
            patterns.append("\n[BIT FIELD DIAGRAM DETECTED]")
            patterns.append(f"[BIT POSITIONS FOUND: {len(set(bit_matches))} unique positions]")
        
        # Detect register names
        register_name_pattern = r'\b([A-Z][A-Z0-9_]{2,})\s*(?:Register|Reg\b|Control|Status|Config|Command|Data)\b'
        register_names = []
        for col in df.columns:
            matches = re.findall(register_name_pattern, str(col), re.IGNORECASE)
            register_names.extend(matches)
        
        for row in df.itertuples(index=False):
            for cell in row:
                if pd.notna(cell):
                    matches = re.findall(register_name_pattern, str(cell), re.IGNORECASE)
                    register_names.extend(matches)
        
        if register_names:
            unique_registers = list(set(register_names))[:10]  # Limit to first 10
            patterns.append(f"[REGISTERS FOUND: {', '.join(unique_registers)}]")
        
        # Detect offset/address patterns
        offset_pattern = r'(?:Offset|Address|Addr)[\s:]*(?:0x[0-9A-Fa-f]+|[0-9A-Fa-f]+h)'
        offsets = re.findall(offset_pattern, df_text, re.IGNORECASE)
        if offsets:
            unique_offsets = list(set(offsets))[:10]
            patterns.append(f"[OFFSETS/ADDRESSES: {', '.join(unique_offsets)}]")
        
        # Detect reset/default values
        reset_pattern = r'(?:Reset|Default|Init)(?:\s+Value)?[\s:]*(?:0x[0-9A-Fa-f]+|[01]{4,}b?)'
        resets = re.findall(reset_pattern, df_text, re.IGNORECASE)
        if resets:
            unique_resets = list(set(resets))[:10]
            patterns.append(f"[RESET/DEFAULT VALUES: {', '.join(unique_resets)}]")
        
        # Detect access types (R/W, RO, WO, etc.)
        access_pattern = r'\b(R/W|RW|RO|WO|R|W|Read/Write|Read-Only|Write-Only)\b'
        access_types = re.findall(access_pattern, df_text, re.IGNORECASE)
        if len(access_types) > 3:
            patterns.append(f"[ACCESS TYPES DETECTED: {', '.join(set(access_types))}]")
        
        return '\n'.join(patterns) if patterns else ""
    
    def _extract_numeric_patterns(self, df: pd.DataFrame) -> str:
        """Extract numeric patterns and statistical information"""
        if df.empty:
            return ""
        
        patterns = []
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) > 0:
            patterns.append("\n[NUMERIC DATA ANALYSIS]")
            
            for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    patterns.append(f"  Column '{col}':")
                    patterns.append(f"    Range: {col_data.min()} to {col_data.max()}")
                    patterns.append(f"    Count: {len(col_data)} values")
                    
                    # Check for hex values
                    hex_count = sum(1 for val in col_data if isinstance(val, str) and 
                                   re.match(r'0x[0-9A-Fa-f]+', str(val)))
                    if hex_count > 0:
                        patterns.append(f"    Hex values detected: {hex_count}")
        
        return '\n'.join(patterns) if patterns else ""
    
    def get_supported_extensions(self) -> list:
        """Get supported file extensions"""
        return ['.xlsx', '.xls']