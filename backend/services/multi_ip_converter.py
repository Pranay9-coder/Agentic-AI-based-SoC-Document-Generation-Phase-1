"""
Multi-IP Converter Service - QUOTA-AWARE VERSION
File: backend/services/multi_ip_converter.py

Key fixes:
1. Uses centralized rate limiter
2. Skips optional operations when quota is low
3. Prioritizes essential operations
4. Respects API retry delays
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
import zipfile
import re
from typing import Optional
import xml.etree.ElementTree as ET

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from extractors.docx_extractor import extract_docx
from extractors.pdf_extractor import extract_pdf
from pipeline.segmenter import segment
from pipeline.enrich import enrich_with_gemini
from writers.dita_writer import write_topics_and_map
from writers.pdf_writer import write_multi_ip_pdf
from utils.regs_table_detector import RegsTableDetector
from utils.gemini_client import GeminiClient
from utils.gemini_processor import GeminiProcessor
from utils.xml_generator import XMLGenerator
from utils.gemini_rate_limiter import get_rate_limiter  # ✅ NEW
from services.image_to_svg_converter import ImageToSVGConverter
from services.regs_pdf_converter import RegsToPDFConverter


class MultiIpConverter:
    """
    Convert multiple IP documents with quota-aware processing
    """
    
    def __init__(self, gemini_api_key: str = None):
        """Initialize converter"""
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        self.gemini_client = None
        self.gemini_processor = None
        self.xml_generator = XMLGenerator()
        self.table_detector = RegsTableDetector()
        self.rate_limiter = get_rate_limiter()  # ✅ NEW
        
        if self.gemini_api_key:
            try:
                self.gemini_client = GeminiClient(api_key=self.gemini_api_key)
                self.gemini_processor = GeminiProcessor(api_key=self.gemini_api_key)
            except Exception as e:
                print(f"Warning: Could not initialize Gemini: {e}")
    
    def convert_multi_ip(
        self,
        file_paths: List[str],
        session_id: str
    ) -> Dict[str, Any]:
        """Convert multiple IP documents with quota management"""
        try:
            print("\n" + "="*80)
            print("🚀 Starting Multi-IP Documentation Generation")
            print("="*80)
            print(f"📊 Processing {len(file_paths)} IP document(s)")
            
            # ✅ Check quota before starting
            quota_status = self.rate_limiter.get_quota_status()
            print(f"📊 Initial Quota: {quota_status['daily_used']}/{quota_status['daily_limit']} daily, "
                  f"{quota_status['minute_used']}/{quota_status['minute_limit']} per minute")
            
            if quota_status['daily_remaining'] < 5:
                print(f"\n⚠️  WARNING: Only {quota_status['daily_remaining']} API calls remaining today!")
                print("   Some operations may be skipped to conserve quota.")
            
            backend_dir = Path(__file__).parent.parent
            spec_outputs_base = backend_dir / "spec_outputs"
            spec_outputs_base.mkdir(parents=True, exist_ok=True)
            
            session_dir = spec_outputs_base / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"📁 Session directory: {session_dir}")
            
            # Process each IP
            ip_results = []
            all_doc_structs = []
            
            for i, file_path in enumerate(file_paths, 1):
                print(f"\n{'='*80}")
                print(f"📄 Processing IP {i}/{len(file_paths)}: {Path(file_path).name}")
                print(f"{'='*80}")
                
                result = self._process_single_ip(
                    file_path=file_path,
                    ip_index=i,
                    session_dir=session_dir
                )
                
                ip_results.append(result)
                if result['success']:
                    all_doc_structs.append({
                        'ip_name': result['ip_name'],
                        'doc_struct': result['doc_struct'],
                        'regs_sections': result.get('regs_sections', [])
                    })
                
                # ✅ Check quota after each IP
                quota_status = self.rate_limiter.get_quota_status()
                print(f"\n📊 Quota after IP {i}: {quota_status['daily_used']}/{quota_status['daily_limit']} daily")
                
                if quota_status['daily_remaining'] < 3 and i < len(file_paths):
                    print(f"\n⚠️  WARNING: Low quota ({quota_status['daily_remaining']} calls left)")
                    print(f"   May skip optional operations for remaining {len(file_paths) - i} IP(s)")
            
            total_stats = self._aggregate_stats(ip_results)
            
            # Generate organized PDF
            print(f"\n{'='*80}")
            print("📚 Generating Organized PDF")
            print(f"{'='*80}")
            
            organized_pdf_path = self._generate_organized_pdf(
                all_doc_structs=all_doc_structs,
                session_dir=session_dir
            )
            
            # Create ZIP
            print(f"\n{'='*80}")
            print("📦 Creating ZIP Archive")
            print(f"{'='*80}")
            
            zip_path = self._create_zip_archive(session_dir)
            
            # ✅ Final quota report
            final_quota = self.rate_limiter.get_quota_status()
            print(f"\n{'='*80}")
            print("✅ Multi-IP Documentation Generation Complete")
            print(f"{'='*80}")
            print(f"📊 Summary:")
            print(f"  • Total IPs: {len(ip_results)}")
            print(f"  • Successful: {sum(1 for r in ip_results if r['success'])}")
            print(f"  • Total topics: {total_stats['total_topics']}")
            print(f"  • Total .REGS: {total_stats['total_regs']}")
            print(f"  • API calls used: {final_quota['daily_used']}/{final_quota['daily_limit']}")
            print(f"  • Remaining today: {final_quota['daily_remaining']}")
            print(f"{'='*80}\n")
            
            return {
                'success': True,
                'session_id': session_id,
                'ip_count': len(file_paths),
                'ip_results': ip_results,
                'stats': total_stats,
                'organized_pdf_path': str(organized_pdf_path),
                'zip_path': str(zip_path),
                'quota_used': final_quota['daily_used'],
                'quota_remaining': final_quota['daily_remaining']
            }
            
        except Exception as e:
            print(f"\n❌ Multi-IP conversion failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_single_ip(
        self,
        file_path: str,
        ip_index: int,
        session_dir: Path
    ) -> Dict[str, Any]:
        """Process a single IP document"""
        try:
            file_ext = Path(file_path).suffix.lower()
            ip_name = Path(file_path).stem
            
            print(f"📖 Extracting content...")
            
            if file_ext in ['.docx', '.doc']:
                result = extract_docx(file_path)
            elif file_ext == '.pdf':
                result = extract_pdf(file_path)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {file_ext}',
                    'ip_name': ip_name
                }
            
            blocks = result.get('blocks', [])
            print(f"✓ Extracted {len(blocks)} blocks")
            
            # Detect REGS tables
            print("🔍 Detecting register tables...")
            regs_tables = self.table_detector.scan_document_for_regs_tables(blocks)
            print(f"✓ Found {len(regs_tables)} register table(s)")
            
            regs_sections = []
            
            # Separate content
            regular_blocks = []
            regs_table_indices = {rt['block_index'] for rt in regs_tables}
            
            for i, block in enumerate(blocks):
                if i not in regs_table_indices:
                    regular_blocks.append(block)
            
            print(f"✓ Separated: {len(regular_blocks)} content blocks, {len(regs_tables)} REGS blocks")
            
            # Segment document
            print("🔧 Segmenting document structure...")
            doc_struct = segment(regular_blocks)
            doc_struct = self._filter_junk_sections(doc_struct)
            print(f"✓ Created {len(doc_struct)} valid sections")
            
            # ✅ Quota-aware AI enrichment (SKIP if low quota)
            quota_status = self.rate_limiter.get_quota_status()
            if self.gemini_client and quota_status['daily_remaining'] > 10:
                try:
                    print("🤖 Enriching with AI...")
                    doc_struct = enrich_with_gemini(doc_struct, self.gemini_client)
                except Exception as e:
                    print(f"⚠️  AI enrichment skipped: {e}")
            else:
                print(f"⚠️  Skipping AI enrichment (quota: {quota_status['daily_remaining']} remaining)")
            
            # Create folder structure
            ip_folder = session_dir / f"IP_{ip_index}_{ip_name}"
            spec_source = ip_folder / "spec_source"
            
            dita_topics_dir = spec_source / "dita_topics"
            dita_map_dir = spec_source / "dita_map"
            regs_dir = spec_source / "regs"
            images_dir = spec_source / "images"
            
            print(f"📁 Creating folder structure in: {spec_source}")
            for folder in [dita_topics_dir, dita_map_dir, regs_dir, images_dir]:
                folder.mkdir(parents=True, exist_ok=True)
            
            # Write DITA files
            print(f"📝 Writing DITA files...")
            temp_output = session_dir / "temp" / f"IP_{ip_index}"
            temp_output.mkdir(parents=True, exist_ok=True)
            
            write_topics_and_map(doc_struct, str(temp_output), ip_name)
            
            # Move files
            print(f"📦 Organizing files...")
            
            temp_topics = temp_output / "topics"
            if temp_topics.exists():
                for dita_file in temp_topics.glob("*.dita"):
                    dest = dita_topics_dir / dita_file.name
                    shutil.copy2(str(dita_file), str(dest))
            
            for ditamap_file in temp_output.glob("*.ditamap"):
                dest = dita_map_dir / ditamap_file.name
                shutil.copy2(str(ditamap_file), str(dest))
            
            temp_media = temp_output / "media"
            if temp_media.exists():
                for img_file in temp_media.glob("*.*"):
                    dest = images_dir / img_file.name
                    shutil.copy2(str(img_file), str(dest))
            
            shutil.rmtree(temp_output, ignore_errors=True)
            
            # ✅ Quota-aware image conversion (SKIP if low quota)
            image_count = len(list(images_dir.glob("*.*")))
            quota_status = self.rate_limiter.get_quota_status()
            
            if self.gemini_api_key and image_count > 0:
                # Each image needs 1 API call, check if we have enough quota
                if quota_status['daily_remaining'] >= image_count + 5:  # +5 buffer for REGS
                    print("🎨 Converting images to SVG...")
                    self._convert_images_to_svg(images_dir)
                else:
                    print(f"⚠️  Skipping image→SVG (need {image_count} calls, have {quota_status['daily_remaining']})")
            
            # ✅ Quota-aware REGS processing (PRIORITIZED)
            quota_status = self.rate_limiter.get_quota_status()
            
            if len(regs_tables) > 0:
                # REGS processing is HIGH PRIORITY - warn if quota is too low
                calls_needed = len(regs_tables)
                
                if quota_status['daily_remaining'] >= calls_needed:
                    print(f"📋 Processing {len(regs_tables)} register table(s)...")
                    regs_files = self._process_regs_tables(
                        regs_tables=regs_tables,
                        regs_dir=regs_dir,
                        device_name=ip_name
                    )
                    
                    if regs_files:
                        print(f"📄 Converting {len(regs_files)} .regs file(s) to PDF...")
                        regs_sections = self._convert_regs_to_pdf_sections(
                            regs_files=regs_files,
                            session_dir=session_dir,
                            ip_index=ip_index
                        )
                        print(f"✓ Created {len(regs_sections)} REGS PDF section(s)")
                else:
                    print(f"⚠️  WARNING: Cannot process REGS tables!")
                    print(f"   Need {calls_needed} API calls, only {quota_status['daily_remaining']} remaining")
                    print(f"   REGS processing SKIPPED - please retry later with fresh quota")
            
            # Verify output
            topic_count = len(list(dita_topics_dir.glob("*.dita")))
            map_count = len(list(dita_map_dir.glob("*.ditamap")))
            image_count = len(list(images_dir.glob("*.*")))
            regs_count = len(list(regs_dir.glob("*.regs")))
            
            print(f"\n✅ IP {ip_index} Output Summary:")
            print(f"  • DITA topics: {topic_count} files")
            print(f"  • DITA maps: {map_count} files")
            print(f"  • Images: {image_count} files")
            print(f"  • REGS files: {regs_count} files")
            
            stats = {
                'topics_count': topic_count,
                'tables_count': 0,
                'regs_count': regs_count,
                'svg_count': len(list(images_dir.glob("*.svg")))
            }
            
            return {
                'success': True,
                'ip_name': ip_name,
                'ip_index': ip_index,
                'output_folder': str(spec_source),
                'stats': stats,
                'doc_struct': doc_struct,
                'regs_sections': regs_sections
            }
            
        except Exception as e:
            print(f"❌ Failed to process IP {ip_index}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'ip_name': Path(file_path).stem,
                'ip_index': ip_index
            }
    
    def _filter_junk_sections(self, doc_struct: List[Dict]) -> List[Dict]:
        """Remove empty or meaningless sections"""
        filtered = []
        
        for section in doc_struct:
            if not isinstance(section, dict):
                continue
            
            title = section.get('title', '').strip()
            content = section.get('content', [])
            children = section.get('children', [])
            
            if re.match(r'^\d+\.$', title) or (len(title) < 3 and not content and not children):
                continue
            
            if children:
                section['children'] = self._filter_junk_sections(children)
            
            filtered.append(section)
        
        return filtered
    
    def _convert_images_to_svg(self, images_dir: Path):
        """Convert PNG/JPG to SVG with rate limiting"""
        try:
            converter = ImageToSVGConverter(self.gemini_api_key)
        except Exception as e:
            print(f"⚠️  Could not initialize converter: {e}")
            return
        
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp']
        
        for img_file in images_dir.glob('*.*'):
            if img_file.suffix.lower() not in image_extensions:
                continue
            
            svg_file = img_file.with_suffix('.svg')
            if svg_file.exists():
                continue
            
            try:
                # ✅ Check quota before each conversion
                quota_status = self.rate_limiter.get_quota_status()
                if quota_status['daily_remaining'] < 1:
                    print(f"  ⚠️  Skipping {img_file.name}: quota exhausted")
                    break
                
                print(f"  Converting: {img_file.name}")
                svg_content = converter.convert_to_svg(str(img_file), diagram_type='block_diagram')
                
                with open(svg_file, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                
                print(f"  ✓ Created: {svg_file.name}")
                
            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg or 'quota' in error_msg.lower():
                    print(f"  ⚠️  Quota exceeded, stopping image conversion")
                    break
                else:
                    print(f"  ⚠️  Skipped {img_file.name}: {e}")
                continue
    
    def _process_regs_tables(
        self,
        regs_tables: List[Dict],
        regs_dir: Path,
        device_name: str
    ) -> List[str]:
        """Process detected register tables with rate limiting"""
        if not self.gemini_processor:
            print("⚠️  Gemini not available, skipping .REGS conversion")
            return []
        
        regs_files = []
        
        for i, regs_table in enumerate(regs_tables, 1):
            try:
                # ✅ Check quota before each table
                quota_status = self.rate_limiter.get_quota_status()
                if quota_status['daily_remaining'] < 1:
                    print(f"  ⚠️  Skipping table {i}: quota exhausted")
                    print(f"     Processed {i-1}/{len(regs_tables)} tables")
                    break
                
                source = regs_table.get('source', 'unknown')
                metadata = regs_table['metadata']
                formatted_text = regs_table.get('formatted_text', '')
                
                print(f"  Processing table {i}/{len(regs_tables)} (source: {source})...")
                print(f"  Quota: {quota_status['daily_remaining']} calls remaining")
                
                if not formatted_text:
                    print(f"  ⚠️  No formatted text for table {i}, skipping")
                    continue
                
                # Extract with Gemini (this will use rate limiter internally)
                print(f"  🤖 Sending to Gemini...")
                register_data = self.gemini_processor.process_document(
                    raw_data=formatted_text,
                    device_name=device_name
                )
                
                if not register_data or not register_data.get('registers'):
                    print(f"  ⚠️  Gemini returned no register data for table {i}")
                    continue
                
                # Generate .REGS XML
                reg_name = metadata.get('register_name')
                if not reg_name:
                    if register_data.get('registers'):
                        reg_name = register_data['registers'][0].get('name', f'REG_{i}')
                    else:
                        reg_name = f'REG_{i}'
                
                reg_name = reg_name.replace(' ', '_').replace('(', '').replace(')', '')
                output_filename = f"{reg_name}.regs"
                output_path = regs_dir / output_filename
                
                xml_content = self.xml_generator.generate(register_data, device_name)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
                
                regs_files.append(str(output_path))
                print(f"  ✓ Created: {output_filename}")
                
            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg or 'quota' in error_msg.lower():
                    print(f"  ⚠️  Quota exceeded at table {i}")
                    print(f"     Processed {i-1}/{len(regs_tables)} tables")
                    break
                else:
                    print(f"  ⚠️  Failed table {i}: {e}")
                continue
        
        return regs_files
    
    def _convert_regs_to_pdf_sections(
        self,
        regs_files: List[str],
        session_dir: Path,
        ip_index: int
    ) -> List[Dict]:
        """Convert .regs files to PDF and extract pages"""
        regs_sections = []
        
        if not PYMUPDF_AVAILABLE:
            print("    ⚠️  PyMuPDF not available, cannot extract PDF pages")
            return regs_sections
        
        converter = RegsToPDFConverter()
        
        temp_regs_pdf_dir = session_dir / "temp_regs_pdfs" / f"IP_{ip_index}"
        temp_regs_pdf_dir.mkdir(parents=True, exist_ok=True)
        
        temp_regs_images_dir = session_dir / "temp_regs_images" / f"IP_{ip_index}"
        temp_regs_images_dir.mkdir(parents=True, exist_ok=True)
        
        for regs_file_path in regs_files:
            try:
                regs_file = Path(regs_file_path)
                reg_name = regs_file.stem
                
                pdf_output_path = temp_regs_pdf_dir / f"{reg_name}.pdf"
                
                print(f"    🔄 Converting {reg_name}.regs to PDF...")
                result = converter.convert(str(regs_file), str(pdf_output_path))
                
                if result['status'] != 'success':
                    print(f"    ⚠️  Failed to convert {reg_name}.regs: {result.get('message')}")
                    continue
                
                print(f"    ✓ Converted {reg_name}.regs to PDF")
                
                if pdf_output_path.exists():
                    doc = fitz.open(str(pdf_output_path))
                    page_images = []
                    
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        mat = fitz.Matrix(2, 2)
                        pix = page.get_pixmap(matrix=mat)
                        
                        image_path = temp_regs_images_dir / f"{reg_name}_page_{page_num + 1}.png"
                        pix.save(str(image_path))
                        page_images.append(str(image_path))
                        
                        print(f"    ✓ Extracted page {page_num + 1} from {reg_name}.pdf")
                    
                    doc.close()
                    
                    if page_images:
                        regs_section = {
                            'type': 'section',
                            'level': 3,
                            'title': f'{reg_name} Register Specification',
                            'content': [
                                {
                                    'type': 'regs_pdf_images',
                                    'image_paths': page_images,
                                    'register_name': reg_name,
                                    'page_count': len(page_images)
                                }
                            ],
                            'children': []
                        }
                        
                        regs_sections.append(regs_section)
                
            except Exception as e:
                print(f"    ⚠️  Error processing {regs_file.name}: {e}")
                continue
        
        return regs_sections
    
    def _aggregate_stats(self, ip_results: List[Dict]) -> Dict[str, int]:
        """Aggregate statistics"""
        return {
            'total_topics': sum(r.get('stats', {}).get('topics_count', 0) for r in ip_results if r['success']),
            'total_tables': sum(r.get('stats', {}).get('tables_count', 0) for r in ip_results if r['success']),
            'total_regs': sum(r.get('stats', {}).get('regs_count', 0) for r in ip_results if r['success']),
            'total_svgs': sum(r.get('stats', {}).get('svg_count', 0) for r in ip_results if r['success'])
        }
    
    def _generate_organized_pdf(
    self,
    all_doc_structs: List[Dict],
    session_dir: Path
) -> Path:
        """Generate organized PDF"""
        print("📚 Creating organized PDF structure...")
        
        quota_status = self.rate_limiter.get_quota_status()
        
        master_doc = []
        
        for i, ip_data in enumerate(all_doc_structs, 1):
            ip_name = ip_data['ip_name']
            doc_struct = ip_data['doc_struct']
            regs_sections = ip_data.get('regs_sections', [])
            
            chapter = {
                'type': 'section',
                'level': 1,
                'title': f'Chapter {i}: {ip_name}',
                'content': [],
                'children': doc_struct
            }
            
            if regs_sections:
                print(f"  📋 Adding {len(regs_sections)} REGS page(s) to chapter {i}")
                
                regs_header = {
                    'type': 'section',
                    'level': 2,
                    'title': 'Register Specifications',
                    'content': [
                        {
                            'type': 'paragraph',
                            'text': 'The following pages show the original register specifications from the source document.'
                        }
                    ],
                    'children': regs_sections
                }
                
                chapter['children'].append(regs_header)
            
            master_doc.append(chapter)
        
        final_pdf_path = session_dir / "organized_soc_documentation.pdf"
        
        try:
            temp_pdf_dir = session_dir / "temp_pdf"
            temp_pdf_dir.mkdir(exist_ok=True)
            
            # ✅ NEW: Copy images to temp_pdf/media BEFORE PDF generation
            self._copy_images_for_pdf_generation(all_doc_structs, temp_pdf_dir)
            
            if quota_status['daily_remaining'] < 20:
                print(f"⚠️  Low quota for PDF summarization ({quota_status['daily_remaining']} calls)")
                print(f"   PDF may have limited summaries")
            
            print(f"📝 Generating PDF...")
            
            pdf_files = write_multi_ip_pdf(
                doc_struct=master_doc,
                out_dir=str(temp_pdf_dir),
                root_title="SOC Documentation",
                gemini_api_key=self.gemini_api_key
            )
            
            possible_locations = [
                temp_pdf_dir / "pdfs" / "soc-documentation.pdf",
                temp_pdf_dir / "soc-documentation.pdf",
                Path(pdf_files[0]) if pdf_files and isinstance(pdf_files, list) else None
            ]
            
            generated_pdf = None
            for location in possible_locations:
                if location and location.exists():
                    generated_pdf = location
                    break
            
            if generated_pdf and generated_pdf.exists():
                shutil.copy2(str(generated_pdf), str(final_pdf_path))
                file_size = final_pdf_path.stat().st_size
                print(f"✓ PDF created: {final_pdf_path.name} ({file_size / 1024:.1f} KB)")
            else:
                print(f"  ⚠️  PDF not found, creating text version...")
                with open(final_pdf_path, 'w', encoding='utf-8') as f:
                    f.write("SOC Documentation\n\n")
                    for i, ip_data in enumerate(all_doc_structs, 1):
                        f.write(f"Chapter {i}: {ip_data['ip_name']}\n")
            
            shutil.rmtree(temp_pdf_dir, ignore_errors=True)
            
        except Exception as e:
            print(f"  ❌ PDF generation error: {e}")
            import traceback
            traceback.print_exc()
            
            with open(final_pdf_path, 'w', encoding='utf-8') as f:
                f.write(f"PDF Generation Error: {str(e)}\n")
        
        return final_pdf_path
    
    def _create_zip_archive(self, session_dir: Path) -> Path:
        """Create ZIP of all IP folders"""
        zip_path = session_dir / "spec_outputs.zip"
        
        print(f"📦 Creating ZIP archive...")
        
        file_count = 0
        
        with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zipf:
            for ip_folder in session_dir.glob('IP_*'):
                if ip_folder.is_dir():
                    for file_path in ip_folder.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(session_dir)
                            zipf.write(str(file_path), str(arcname))
                            file_count += 1
        
        if file_count == 0:
            print(f"  ⚠️  WARNING: ZIP is empty!")
        else:
            zip_size = zip_path.stat().st_size / (1024 * 1024)
            print(f"✓ ZIP created: {zip_path.name} ({zip_size:.2f} MB, {file_count} files)")
        
        return zip_path
    


    def regenerate_pdf_from_spec_source(self, session_id: str) -> Dict[str, Any]:
        """
        Regenerate PDF from existing edited spec_source files
        DEBUG VERSION - Prints everything
        """
        try:
            print("\n" + "=" * 80)
            print("🔄 Regenerating PDF from Edited Spec Source - DEBUG MODE")
            print("=" * 80)

            backend_dir = Path(__file__).parent.parent
            spec_outputs_base = backend_dir / "spec_outputs"
            session_dir = spec_outputs_base / session_id

            print(f"DEBUG: session_dir = {session_dir}")
            print(f"DEBUG: session_dir.exists() = {session_dir.exists()}")

            if not session_dir.exists():
                return {
                    'success': False,
                    'error': 'Session directory not found'
                }

            # Find all IP folders
            ip_folders = sorted([f for f in session_dir.glob('IP_*') if f.is_dir()])
            print(f"DEBUG: Found {len(ip_folders)} IP folders")
            for folder in ip_folders:
                print(f"  - {folder.name}")

            if not ip_folders:
                return {
                    'success': False,
                    'error': 'No IP folders found'
                }

            # Reconstruct doc_struct from DITA files for each IP
            all_doc_structs = []

            for ip_folder in ip_folders:
                ip_name = ip_folder.name.split('_', 2)[-1]
                spec_source = ip_folder / "spec_source"

                print(f"\nDEBUG: Processing {ip_folder.name}...")
                print(f"DEBUG: ip_name = {ip_name}")
                print(f"DEBUG: spec_source = {spec_source}")
                print(f"DEBUG: spec_source.exists() = {spec_source.exists()}")

                if not spec_source.exists():
                    print("DEBUG: SKIPPING - spec_source doesn't exist")
                    continue

                dita_map_dir = spec_source / "dita_map"
                dita_topics_dir = spec_source / "dita_topics"

                print(f"DEBUG: dita_map_dir = {dita_map_dir}")
                print(f"DEBUG: dita_map_dir.exists() = {dita_map_dir.exists()}")
                print(f"DEBUG: dita_topics_dir = {dita_topics_dir}")
                print(f"DEBUG: dita_topics_dir.exists() = {dita_topics_dir.exists()}")

                if not dita_map_dir.exists() or not dita_topics_dir.exists():
                    print("DEBUG: SKIPPING - Missing DITA directories")
                    continue

                ditamap_files = list(dita_map_dir.glob('*.ditamap'))
                print(f"DEBUG: Found {len(ditamap_files)} ditamap files")
                for dm in ditamap_files:
                    print(f"  - {dm.name}")

                if not ditamap_files:
                    print("DEBUG: SKIPPING - No ditamap found")
                    continue

                ditamap_path = ditamap_files[0]
                print(f"DEBUG: Using ditamap: {ditamap_path.name}")

                print("DEBUG: Calling _parse_dita_structure_from_files()...")
                doc_struct = self._parse_dita_structure_from_files(
                    ditamap_path=ditamap_path,
                    dita_topics_dir=dita_topics_dir
                )

                print(f"DEBUG: doc_struct length = {len(doc_struct)}")
                if doc_struct:
                    for i, section in enumerate(doc_struct[:3]):
                        print(f"  Section {i}: {section.get('title', 'NO TITLE')}")
                        print(f"    Content items: {len(section.get('content', []))}")
                        print(f"    Children: {len(section.get('children', []))}")
                        if section.get('content'):
                            first = section['content'][0]
                            print(f"    First content type: {first.get('type')}")
                else:
                    print("DEBUG: ⚠️ doc_struct is EMPTY!")

                print("DEBUG: Calling _load_regs_sections_for_pdf()...")
                regs_sections = self._load_regs_sections_for_pdf(ip_folder, spec_source)
                print(f"DEBUG: regs_sections length = {len(regs_sections)}")

                all_doc_structs.append({
                    'ip_name': ip_name,
                    'doc_struct': doc_struct,
                    'regs_sections': regs_sections
                })

                print("DEBUG: Added to all_doc_structs")

            print(f"\nDEBUG: all_doc_structs length = {len(all_doc_structs)}")

            if not all_doc_structs:
                return {
                    'success': False,
                    'error': 'No valid IP data found for PDF generation'
                }

            print("\n" + "=" * 80)
            print("DEBUG: Calling _generate_organized_pdf()...")
            print("=" * 80)

            organized_pdf_path = self._generate_organized_pdf(
                all_doc_structs=all_doc_structs,
                session_dir=session_dir
            )

            print(f"DEBUG: organized_pdf_path = {organized_pdf_path}")
            print(f"DEBUG: PDF exists = {organized_pdf_path.exists()}")

            if organized_pdf_path.exists():
                print(f"DEBUG: PDF size = {organized_pdf_path.stat().st_size} bytes")

            print("\n" + "=" * 80)
            print("✅ PDF Regeneration Complete")
            print("=" * 80 + "\n")

            return {
                'success': True,
                'pdf_path': str(organized_pdf_path),
                'ip_count': len(all_doc_structs)
            }

        except Exception as e:
            print(f"\n❌ PDF regeneration failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    
    def _parse_dita_structure_from_files(
    self,
    ditamap_path: Path,
    dita_topics_dir: Path
) -> List[Dict]:
        """
        Parse DITA structure from existing files
        FIXED: Handles path mismatch between ditamap hrefs and actual file locations
        """
        try:
            print(f"    📋 Parsing ditamap: {ditamap_path.name}")
            
            # Parse ditamap XML
            tree = ET.parse(str(ditamap_path))
            root = tree.getroot()
            
            doc_struct = []
            
            # Find topicrefs
            topicrefs = root.findall('.//{*}topicref')
            
            if not topicrefs:
                topicrefs = root.findall('.//topicref')
            
            print(f"    📄 Found {len(topicrefs)} topicref(s) in ditamap")
            
            for idx, topicref in enumerate(topicrefs):
                href = topicref.get('href')
                
                if not href:
                    continue
                
                # ✅ FIX: Strip "topics/" prefix if present
                # Ditamap might have "topics/file.dita" but files are in dita_topics/ directly
                clean_href = href
                if href.startswith('topics/'):
                    clean_href = href.replace('topics/', '', 1)
                
                # Build topic file path with cleaned href
                topic_file = dita_topics_dir / clean_href
                
                print(f"    📖 Loading topic {idx + 1}/{len(topicrefs)}: {href}")
                if href != clean_href:
                    print(f"       🔧 Adjusted path: {clean_href}")
                
                if not topic_file.exists():
                    print(f"       ⚠️  File not found: {topic_file}")
                    continue
                
                # Parse the topic file
                try:
                    section = self._parse_dita_topic_file(topic_file)
                    
                    if section:
                        content_count = len(section.get('content', []))
                        children_count = len(section.get('children', []))
                        print(f"       ✓ Parsed: {section.get('title')} (content: {content_count}, children: {children_count})")
                        
                        doc_struct.append(section)
                    else:
                        print(f"       ⚠️  Parsing returned None")
                        
                except Exception as e:
                    print(f"       ❌ Parse error: {e}")
                    continue
            
            print(f"    ✓ Total sections parsed: {len(doc_struct)}")
            
            return doc_struct
            
        except Exception as e:
            print(f"    ❌ Error parsing DITA structure: {e}")
            import traceback
            traceback.print_exc()
            return []
    
# ==================================================================
# STEP 1: REPLACE _parse_dita_topic_file() method (around line 790)
# ==================================================================

    def _parse_dita_topic_file(self, topic_file: Path) -> Optional[Dict]:
        """
        Parse a single DITA topic file and convert to doc_struct format
        Passes images_dir to recursive parser
        """
        try:
            tree = ET.parse(str(topic_file))
            root = tree.getroot()
            
            # Get title
            title_elem = root.find('.//{*}title')
            if title_elem is not None and title_elem.text:
                title = title_elem.text.strip()
            else:
                title = topic_file.stem.replace('_', ' ').title()
            
            # Extract content
            content = []
            children = []
            
            # Find body element
            body = root.find('.//{*}body')
            
            if body is not None:
                # ✅ Calculate images directory path
                # topic_file is in: spec_source/dita_topics/untitled-drawing.dita
                # images are in:    spec_source/images/
                images_dir = topic_file.parent.parent / "images"
                
                print(f"          ℹ️  Images dir: {images_dir}")
                print(f"          ℹ️  Images dir exists: {images_dir.exists()}")
                
                # Parse body content recursively WITH images_dir
                content, children = self._parse_dita_body_recursive(body, images_dir=images_dir)
            else:
                print(f"       ⚠️  No body element found in {topic_file.name}")
            
            return {
                'type': 'section',
                'level': 1,
                'title': title,
                'content': content,
                'children': children
            }
            
        except Exception as e:
            print(f"       ❌ Error parsing {topic_file.name}: {e}")
            import traceback
            traceback.print_exc()
            return None

# ==================================================================
# STEP 2: ADD NEW METHOD after _parse_dita_topic_file()
# ==================================================================

    def _parse_dita_body_recursive(self, element, level=1, images_dir=None):
        """
        Recursively parse DITA body content
        FIXED: Uses 'href' field that PDF writer expects
        Returns: (content_list, children_list)
        """
        content = []
        children = []
        
        for child in element:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            
            # Paragraphs
            if tag == 'p':
                text = ''.join(child.itertext()).strip()
                if text:
                    content.append({
                        'type': 'paragraph',
                        'text': text
                    })
            
            # Nested sections
            elif tag == 'section':
                section_title_elem = child.find('.//{*}title')
                section_title = section_title_elem.text if section_title_elem is not None else "Section"
                
                section_content, section_children = self._parse_dita_body_recursive(
                    child, level + 1, images_dir=images_dir
                )
                
                if section_content or section_children:
                    children.append({
                        'type': 'section',
                        'level': level + 1,
                        'title': section_title,
                        'content': section_content,
                        'children': section_children
                    })
            
            # Lists
            elif tag in ['ul', 'ol']:
                list_items = []
                for li in child.findall('.//{*}li'):
                    item_text = ''.join(li.itertext()).strip()
                    if item_text:
                        list_items.append(item_text)
                
                if list_items:
                    content.append({
                        'type': 'list',
                        'ordered': tag == 'ol',
                        'items': list_items
                    })
            
            # Tables
            elif tag == 'table':
                table_data = self._parse_dita_table(child)
                if table_data:
                    content.append(table_data)
            
            # Code blocks
            elif tag == 'codeblock':
                code_text = ''.join(child.itertext()).strip()
                if code_text:
                    content.append({
                        'type': 'code',
                        'text': code_text
                    })
            
            # ✅ IMAGES - Fixed to match PDF writer expectations
            elif tag == 'image':
                href = child.get('href')
                if href and images_dir:
                    # Extract filename
                    if '/' in href:
                        filename = href.split('/')[-1]
                    else:
                        filename = href
                    
                    # Try to find the image
                    base_name = Path(filename).stem
                    
                    possible_files = [
                        images_dir / filename,
                        images_dir / f"{base_name}.svg",
                        images_dir / f"{base_name}.png",
                        images_dir / f"{base_name}.jpg",
                        images_dir / f"{base_name}.jpeg"
                    ]
                    
                    found_file = None
                    for path in possible_files:
                        if path.exists():
                            found_file = path
                            print(f"          ✓ Found image: {path.name}")
                            break
                    
                    if found_file:
                        # ✅ Use 'href' with just the filename (PDF writer expects this)
                        content.append({
                            'type': 'image',
                            'href': found_file.name,  # Just filename, not full path
                            '_source_path': str(found_file)  # Store full path for copying later
                        })
                    else:
                        print(f"          ⚠️  Image not found: {href}")
            
            # Notes
            elif tag == 'note':
                note_text = ''.join(child.itertext()).strip()
                if note_text:
                    content.append({
                        'type': 'note',
                        'text': note_text
                    })
            
            # Skip title
            elif tag == 'title':
                continue
            
            # Other elements
            else:
                text = child.text.strip() if child.text else ''
                if text and len(text) > 3:
                    content.append({
                        'type': 'paragraph',
                        'text': text
                    })
                
                if len(child) > 0:
                    nested_content, nested_children = self._parse_dita_body_recursive(
                        child, level, images_dir=images_dir
                    )
                    content.extend(nested_content)
                    children.extend(nested_children)
        
        return content, children
    def _copy_images_for_pdf_generation(
    self,
    all_doc_structs: List[Dict],
    temp_pdf_dir: Path
) -> None:
        """
        Copy all images to temp_pdf/media directory for PDF generation
        The PDF writer expects images in this location
        """
        try:
            media_dir = temp_pdf_dir / "media"
            media_dir.mkdir(parents=True, exist_ok=True)
            
            print("  📸 Copying images for PDF generation...")
            
            def collect_images_from_node(node):
                """Recursively collect all image references"""
                images = []
                
                if not isinstance(node, dict):
                    return images
                
                for content_item in node.get("content", []):
                    if content_item.get("type") == "image":
                        source_path = content_item.get("_source_path")
                        if source_path and Path(source_path).exists():
                            images.append(source_path)
                
                for child in node.get("children", []):
                    images.extend(collect_images_from_node(child))
                
                return images
            
            # Collect all image paths from doc structure
            all_images = []
            for ip_data in all_doc_structs:
                for section in ip_data.get("doc_struct", []):
                    all_images.extend(collect_images_from_node(section))
            
            # Copy images to media_dir
            copied_count = 0
            for img_path in all_images:
                source = Path(img_path)
                dest = media_dir / source.name
                
                if not dest.exists():
                    try:
                        shutil.copy2(str(source), str(dest))
                        copied_count += 1
                    except Exception as e:
                        print(f"    ⚠️  Could not copy {source.name}: {e}")
            
            print(f"  ✓ Copied {copied_count} image(s) to temp_pdf/media")
            
        except Exception as e:
            print(f"  ⚠️  Error copying images: {e}")
            import traceback
            traceback.print_exc()

    def _parse_dita_table(self, table_elem) -> Optional[Dict]:
        """Parse DITA table element"""
        try:
            rows = []
            
            # Find thead and tbody
            thead = table_elem.find('.//{*}thead')
            tbody = table_elem.find('.//{*}tbody')
            
            # Header rows
            if thead is not None:
                for row in thead.findall('.//{*}row'):
                    cells = []
                    for entry in row.findall('.//{*}entry'):
                        text = ''.join(entry.itertext()).strip()
                        cells.append(text)
                    if cells:
                        rows.append(cells)
            
            # Body rows
            if tbody is not None:
                for row in tbody.findall('.//{*}row'):
                    cells = []
                    for entry in row.findall('.//{*}entry'):
                        text = ''.join(entry.itertext()).strip()
                        cells.append(text)
                    if cells:
                        rows.append(cells)
            
            if rows:
                return {
                    'type': 'table',
                    'rows': rows
                }
            
            return None
            
        except Exception as e:
            print(f"    ⚠️  Error parsing table: {e}")
            return None
    
    def _load_regs_sections_for_pdf(
    self,
    ip_folder: Path,
    spec_source: Path
) -> List[Dict]:
        """
        Load REGS sections by re-processing .regs files
        FIXED: Now re-converts .regs files to get latest edits
        """
        try:
            if not PYMUPDF_AVAILABLE:
                print("       ⚠️  PyMuPDF not available, REGS tables will be skipped")
                return []
            
            regs_sections = []
            
            # Find .regs files in spec_source/regs
            regs_dir = spec_source / "regs"
            
            if not regs_dir.exists():
                print(f"       ℹ️  No regs directory found")
                return []
            
            regs_files = list(regs_dir.glob("*.regs"))
            
            if not regs_files:
                print(f"       ℹ️  No .regs files found")
                return []
            
            print(f"       📋 Found {len(regs_files)} .regs file(s), converting to PDF...")
            
            # Create temp directories for this regeneration
            session_dir = ip_folder.parent
            temp_regs_pdf_dir = session_dir / "temp_regs_pdfs_regen" / ip_folder.name
            temp_regs_images_dir = session_dir / "temp_regs_images_regen" / ip_folder.name
            
            temp_regs_pdf_dir.mkdir(parents=True, exist_ok=True)
            temp_regs_images_dir.mkdir(parents=True, exist_ok=True)
            
            converter = RegsToPDFConverter()
            
            for regs_file in regs_files:
                try:
                    reg_name = regs_file.stem
                    pdf_output_path = temp_regs_pdf_dir / f"{reg_name}.pdf"
                    
                    print(f"          🔄 Converting {reg_name}.regs to PDF...")
                    result = converter.convert(str(regs_file), str(pdf_output_path))
                    
                    if result['status'] != 'success':
                        print(f"          ⚠️  Conversion failed: {result.get('message')}")
                        continue
                    
                    # Extract pages as images
                    if pdf_output_path.exists():
                        doc = fitz.open(str(pdf_output_path))
                        page_images = []
                        
                        for page_num in range(len(doc)):
                            page = doc[page_num]
                            mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
                            pix = page.get_pixmap(matrix=mat)
                            
                            image_path = temp_regs_images_dir / f"{reg_name}_page_{page_num + 1}.png"
                            pix.save(str(image_path))
                            page_images.append(str(image_path))
                        
                        doc.close()
                        
                        print(f"          ✓ Extracted {len(page_images)} page(s)")
                        
                        if page_images:
                            regs_section = {
                                'type': 'section',
                                'level': 3,
                                'title': f'{reg_name} Register Specification',
                                'content': [
                                    {
                                        'type': 'regs_pdf_images',
                                        'image_paths': page_images,
                                        'register_name': reg_name,
                                        'page_count': len(page_images)
                                    }
                                ],
                                'children': []
                            }
                            
                            regs_sections.append(regs_section)
                    
                except Exception as e:
                    print(f"          ⚠️  Error processing {regs_file.name}: {e}")
                    continue
            
            print(f"       ✓ Created {len(regs_sections)} REGS section(s)")
            
            return regs_sections
            
        except Exception as e:
            print(f"       ⚠️  Error loading REGS sections: {e}")
            import traceback
            traceback.print_exc()
            return []
