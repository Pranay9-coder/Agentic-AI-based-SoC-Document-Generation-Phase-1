"""
Service for converting any document format to .regs
File: backend/services/any_to_regs_converter.py
"""
import os
from pathlib import Path
from typing import Dict, Any
from extractors import RegsExcelExtractor, RegsPDFExtractor, RegsWordExtractor
from utils.gemini_processor import GeminiProcessor
from utils.xml_generator import XMLGenerator


class AnyToRegsConverter:
    """Convert PDF, Word, or Excel documents to .regs format"""
    
    def __init__(self, gemini_api_key: str = None):
        """Initialize converter with Gemini API key"""
        self.gemini_processor = GeminiProcessor(gemini_api_key)
        self.xml_generator = XMLGenerator()
        
        # Initialize extractors
        self.extractors = {
            '.pdf': RegsPDFExtractor(),
            '.docx': RegsWordExtractor(),
            '.doc': RegsWordExtractor(),
            '.xlsx': RegsExcelExtractor(),
            '.xls': RegsExcelExtractor()
        }
    
    def convert(self, input_path: str, output_path: str, device_name: str = None) -> Dict[str, Any]:
        """
        Convert document to .regs format
        
        Args:
            input_path: Path to input document (PDF, Word, or Excel)
            output_path: Path for output .regs file
            device_name: Optional device name (extracted from filename if not provided)
            
        Returns:
            dict: Conversion result with status and details
        """
        try:
            print("\n" + "="*80)
            print("🔄 Starting ANY to REGS Conversion")
            print("="*80)
            
            # Validate input file exists
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            # Detect file type
            file_ext = Path(input_path).suffix.lower()
            print(f"📄 Input file: {os.path.basename(input_path)}")
            print(f"📋 Detected file type: {file_ext}")
            
            # Get appropriate extractor
            if file_ext not in self.extractors:
                return {
                    'status': 'error',
                    'message': f'Unsupported file type: {file_ext}. Supported: .pdf, .docx, .doc, .xlsx, .xls'
                }
            
            extractor = self.extractors[file_ext]
            
            # Extract device name from filename if not provided
            if not device_name:
                device_name = Path(input_path).stem
                device_name = device_name.replace('_', ' ').replace('-', ' ').title()
            
            print(f"🏷️  Device name: {device_name}")
            
            # Step 1: Extract raw data from document
            print("\n📖 Step 1: Extracting document content...")
            raw_data = extractor.extract(input_path)
            print(f"✓ Extracted {len(raw_data)} characters of data")
            
            # Save raw extraction for debugging
            debug_file = output_path.replace('.regs', '_extracted.txt')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(raw_data)
            print(f"💾 Saved raw extraction to: {debug_file}")
            
            # Step 2: Process with Gemini AI
            print("\n🤖 Step 2: Processing with Gemini AI...")
            register_data = self.gemini_processor.process_document(raw_data, device_name)
            
            # Validate register data
            if not register_data.get('registers'):
                raise ValueError("No registers extracted from document")
            
            num_registers = len(register_data['registers'])
            total_fields = sum(len(reg.get('fields', [])) for reg in register_data['registers'])
            print(f"✓ Extracted {num_registers} register(s) with {total_fields} total fields")
            
            # Step 3: Generate .regs XML
            print("\n📝 Step 3: Generating .regs XML...")
            xml_content = self.xml_generator.generate(register_data, device_name)
            
            # Write output file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            print(f"✓ Generated .regs file: {output_path}")
            
            # Verify output file exists
            if not os.path.exists(output_path):
                raise Exception(f"Output file not created: {output_path}")
            
            output_size = os.path.getsize(output_path)
            print(f"✓ Output file size: {output_size} bytes")
            
            print("\n" + "="*80)
            print("✅ Conversion completed successfully!")
            print("="*80 + "\n")
            
            return {
                'status': 'success',
                'message': f'Successfully converted to .regs format',
                'device_name': device_name,
                'register_count': num_registers,
                'field_count': total_fields,
                'output_file': output_path,
                'output_size': output_size
            }
            
        except FileNotFoundError as e:
            error_msg = str(e)
            print(f"\n❌ File not found: {error_msg}")
            return {
                'status': 'error',
                'message': error_msg
            }
            
        except ValueError as e:
            error_msg = str(e)
            print(f"\n❌ Extraction error: {error_msg}")
            return {
                'status': 'error',
                'message': f'Failed to extract register data: {error_msg}'
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Conversion failed: {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'Conversion failed: {error_msg}'
            }
    
    def detect_file_type(self, filepath: str) -> str:
        """
        Detect file type from extension
        
        Args:
            filepath: Path to file
            
        Returns:
            str: File type description
        """
        ext = Path(filepath).suffix.lower()
        type_map = {
            '.pdf': 'PDF Document',
            '.docx': 'Word Document (DOCX)',
            '.doc': 'Word Document (DOC)',
            '.xlsx': 'Excel Spreadsheet (XLSX)',
            '.xls': 'Excel Spreadsheet (XLS)'
        }
        return type_map.get(ext, 'Unknown')
    
    def get_supported_formats(self) -> list:
        """Get list of supported file formats"""
        return list(self.extractors.keys())