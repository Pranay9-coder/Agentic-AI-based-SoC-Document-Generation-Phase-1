from pathlib import Path
import os

# Import existing modules
from extractors.docx_extractor import extract_docx
from extractors.pdf_extractor import extract_pdf
from pipeline.segmenter import segment
from pipeline.enrich import enrich_with_gemini
from writers.dita_writer import write_topics_and_map
from utils.helpers import slugify, make_safe_filename
from utils.gemini_client import GeminiClient


class DITAConverter:
    """
    Service class to orchestrate PDF/DOCX to DITA conversion
    Uses existing extraction, segmentation, and writing modules
    """
    
    def __init__(self, gemini_key=None):
        """
        Initialize converter with optional Gemini API key
        
        Args:
            gemini_key: Optional Gemini API key for AI enrichment
        """
        self.gemini_key = gemini_key
        self.gemini_client = None
        
        if gemini_key:
            try:
                self.gemini_client = GeminiClient(api_key=gemini_key)
            except Exception as e:
                print(f"Warning: Could not initialize Gemini client: {e}")
    
    def convert(self, file_path, file_type, output_dir, doc_title):
        """
        Convert document to DITA format
        
        Args:
            file_path: Path to input file
            file_type: File extension ('pdf', 'docx', 'doc')
            output_dir: Directory for output files
            doc_title: Title for the document
            
        Returns:
            dict: Result with success status, stats, and any errors
        """
        try:
            print(f"\n{'='*60}")
            print(f"🔄 Starting DITA Conversion")
            print(f"{'='*60}")
            print(f"📄 File: {file_path}")
            print(f"📋 Type: {file_type}")
            print(f"📁 Output: {output_dir}")
            
            # Step 1: Extract content based on file type
            if file_type in ['docx', 'doc']:
                result = extract_docx(file_path)
            elif file_type == 'pdf':
                result = extract_pdf(file_path)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {file_type}'
                }
            
            blocks = result.get('blocks', [])
            print(f"📊 Extracted {len(blocks)} blocks")
            
            # Debug: Print first few blocks to see what we're working with
            print(f"\n🔍 Sample blocks:")
            for i, block in enumerate(blocks[:5]):
                block_type = block.get('type', 'unknown')
                block_style = block.get('style', '')
                block_text = str(block.get('text', ''))[:50]
                print(f"  [{i}] type={block_type}, style={block_style}, text={block_text}")
            
            if not blocks:
                return {
                    'success': False,
                    'error': 'No content extracted from document'
                }
            
            # Step 2: Segment blocks into document structure
            print(f"\n{'='*60}")
            print(f"🔧 Segmenting Document Structure")
            print(f"{'='*60}")
            doc_struct = segment(blocks)
            
            if not doc_struct:
                return {
                    'success': False,
                    'error': 'Failed to segment document structure'
                }
            
            print(f"📑 Created {len(doc_struct)} top-level topics")
            
            # Debug: Print the structure
            def print_structure(nodes, indent=0):
                for node in nodes:
                    if isinstance(node, dict):
                        title = node.get('title', 'Untitled')
                        level = node.get('level', 0)
                        content_count = len(node.get('content', []))
                        children_count = len(node.get('children', []))
                        print(f"{'  ' * indent}[L{level}] {title[:50]} (content: {content_count}, children: {children_count})")
                        if node.get('children'):
                            print_structure(node['children'], indent + 1)
            
            print(f"\n📋 Document Structure:")
            print_structure(doc_struct)
            
            # Step 3: Normalize titles (from streamlit_app logic)
            print(f"\n{'='*60}")
            print(f"✏️  Normalizing Titles")
            print(f"{'='*60}")
            self._normalize_titles(doc_struct)
            
            # Step 4: Optional Gemini enrichment
            if self.gemini_client:
                try:
                    print(f"\n{'='*60}")
                    print(f"🤖 Enriching with Gemini AI")
                    print(f"{'='*60}")
                    doc_struct = enrich_with_gemini(doc_struct, self.gemini_client)
                except Exception as e:
                    print(f"⚠️  Warning: Gemini enrichment failed: {e}")
            
            # Step 5: Create output directory structure
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Step 6: Write DITA files
            print(f"\n{'='*60}")
            print(f"📝 Writing DITA Files")
            print(f"{'='*60}")
            write_topics_and_map(doc_struct, str(output_path), doc_title)
            
            # 🆕 Step 7: Convert images to SVG if they exist
            print(f"\n{'='*60}")
            print(f"🎨 Converting Images to SVG")
            print(f"{'='*60}")
            self._convert_images_to_svg(output_path)
            
            # Step 8: Calculate statistics
            stats = self._calculate_stats(output_path)
            
            print(f"\n{'='*60}")
            print(f"✅ Conversion Complete")
            print(f"{'='*60}")
            print(f"📊 Statistics:")
            print(f"  • Topics: {stats['topics_count']}")
            print(f"  • Tables: {stats['tables_count']}")
            print(f"  • Media: {stats['media_count']}")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'stats': stats,
                'output_dir': str(output_path)
            }
            
        except Exception as e:
            import traceback
            print(f"\n{'='*60}")
            print(f"❌ Conversion Error")
            print(f"{'='*60}")
            print(traceback.format_exc())
            print(f"{'='*60}\n")
            return {
                'success': False,
                'error': f'Conversion error: {str(e)}'
            }
    
    def _convert_images_to_svg(self, output_dir):
        """
        🆕 Convert non-SVG images in media folder to SVG format
        Saves both original and SVG versions side-by-side
        
        Args:
            output_dir: Path to output directory containing media folder
        """
        media_dir = Path(output_dir) / "media"
        
        # Check if media directory exists
        if not media_dir.exists():
            print("ℹ️  No media folder found, skipping image-to-SVG conversion")
            return
        
        # Get Gemini API key from environment
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            print("⚠️  GEMINI_API_KEY not set, skipping image-to-SVG conversion")
            return
        
        # Initialize the image converter
        try:
            from services.image_to_svg_converter import ImageToSVGConverter
            converter = ImageToSVGConverter(gemini_key)
        except Exception as e:
            print(f"⚠️  Could not initialize ImageToSVGConverter: {e}")
            return
        
        # Supported image formats to convert
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']
        
        # Find all non-SVG images in media directory
        image_files = []
        for ext in image_extensions:
            image_files.extend(media_dir.glob(f"*{ext}"))
            # Also check uppercase extensions
            image_files.extend(media_dir.glob(f"*{ext.upper()}"))
        
        # Remove duplicates (in case of case-insensitive file systems)
        image_files = list(set(image_files))
        
        if not image_files:
            print("ℹ️  No raster images found in media folder")
            return
        
        print(f"📊 Found {len(image_files)} image(s) to convert")
        
        success_count = 0
        failed_count = 0
        
        # Convert each image
        for img_path in image_files:
            # Skip if SVG already exists (avoid re-conversion)
            svg_path = img_path.with_suffix('.svg')
            if svg_path.exists():
                print(f"⏭️  Skipping {img_path.name} (SVG already exists)")
                continue
            
            try:
                print(f"🔄 Converting: {img_path.name}")
                
                # Convert to SVG with auto-detection
                svg_content = converter.convert_to_svg(
                    str(img_path), 
                    diagram_type=None  # Auto-detect
                )
                
                # Save SVG with same name but .svg extension
                with open(svg_path, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                
                print(f"✅ Created: {svg_path.name}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ Failed to convert {img_path.name}: {e}")
                failed_count += 1
                # Continue with other images even if one fails
                continue
        
        # Summary
        print(f"\n📈 Image Conversion Summary:")
        print(f"  ✅ Success: {success_count}")
        if failed_count > 0:
            print(f"  ❌ Failed: {failed_count}")
    
    def _normalize_titles(self, doc_struct):
        """
        Apply title normalization (from streamlit_app.py logic)
        Ensures all topics have meaningful titles
        """
        def _first_text_snippet(content_items):
            """Extract first text snippet from content"""
            for item in content_items:
                if item.get("type") == "p" and item.get("text"):
                    words = item.get("text").split()
                    return " ".join(words[:8])
                if item.get("type") == "table" and item.get("title"):
                    return item.get("title")
                if item.get("type") == "image" and item.get("caption"):
                    return item.get("caption")
            return None
        
        def _apply_fallback_titles(nodes):
            """Apply fallback titles to nodes without titles"""
            counter = {"n": 1}
            
            def visit(node):
                if not isinstance(node, dict):
                    return
                    
                title = (node.get("title") or "").strip()
                
                if not title or title.lower() == "untitled":
                    # Try to get snippet from content
                    candidate = _first_text_snippet(node.get("content", []))
                    if candidate:
                        node["title"] = candidate
                    else:
                        node["title"] = f"Topic {counter['n']}"
                        counter["n"] += 1
                
                # Recursively visit children
                for child in node.get("children", []):
                    visit(child)
            
            # Process all nodes
            for node in nodes:
                if isinstance(node, dict):
                    visit(node)
        
        _apply_fallback_titles(doc_struct)
    
    def _calculate_stats(self, output_dir):
        """
        Calculate conversion statistics
        
        Returns:
            dict: Statistics about generated files
        """
        output_path = Path(output_dir)
        
        # Count DITA topics
        topics_dir = output_path / "topics"
        topics_count = 0
        if topics_dir.exists():
            topics_count = len(list(topics_dir.glob("*.dita")))
        
        # Count media files
        media_dir = output_path / "media"
        media_count = 0
        if media_dir.exists():
            media_count = len(list(media_dir.glob("*")))
        
        # Count tables (scan DITA files for table elements)
        tables_count = 0
        if topics_dir.exists():
            for dita_file in topics_dir.glob("*.dita"):
                try:
                    with open(dita_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        tables_count += content.count('<table')
                except Exception:
                    pass
        
        return {
            'topics_count': topics_count,
            'tables_count': tables_count,
            'media_count': media_count
        }