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
        
        # ✅ Check quota before PDF summarization
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
            
            # ✅ Warn about summarization quota needs
            if quota_status['daily_remaining'] < 20:
                print(f"⚠️  Low quota for PDF summarization ({quota_status['daily_remaining']} calls)")
                print(f"   PDF may have limited summaries")
            
            print(f"📝 Generating PDF...")
            
            # This function will use the rate limiter internally
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