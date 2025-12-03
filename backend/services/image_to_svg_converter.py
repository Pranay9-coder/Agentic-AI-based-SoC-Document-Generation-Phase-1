"""
Image to SVG Converter Service - FIXED VERSION
Optimized for Gemini API quota limits + XML entity escaping
"""
import os
import re
import time
import html
from PIL import Image
from pathlib import Path
import google.generativeai as genai

class ImageToSVGConverter:
    def __init__(self, api_key: str):
        """Initialize converter with Gemini API key"""
        genai.configure(api_key=api_key)
        
        # FIXED: Use stable model instead of experimental
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.max_image_size = (1024, 1024)
        
        # Track last API call for rate limiting
        self.last_api_call = 0
        self.min_call_interval = 4.5  # 4.5 seconds between calls (safe for 15 RPM)
        
        # Diagram type prompts
        self.diagram_prompts = {
            'flowchart': """
            Convert this flowchart to SVG with high accuracy and precision:
            1. Shape Elements: Create exact rectangles, diamonds, circles, or parallelograms with proper dimensions and positioning
            2. Connection Fidelity: Preserve original connection geometry - straight lines must remain straight using simple line elements, curved connections only where visually curved in source using quadratic/cubic Bezier path elements
            3. Arrow Markers: Define and apply consistent arrow markers at connection endpoints with proper orientation
            4. Typography: Position all text labels precisely within shapes and along connections with appropriate font sizing
            5. Layout Preservation: Maintain exact spatial relationships, alignment, and proportions from original diagram
            6. Path Optimization: Use minimal anchor points for clean, scalable paths
            Generate clean, semantic SVG with viewBox for scalability and proper element hierarchy.
            """,
            
            'waveform': """
            Convert this waveform diagram to SVG with signal accuracy:
            1. Signal Traces: Render accurate waveforms using smooth SVG path elements with appropriate sampling points
            2. Grid System: Generate precise grid lines, axis labels, and measurement scales with proper spacing
            3. Multi-Signal Support: Handle overlapping signals with distinct colors and proper z-index layering
            4. Time/Amplitude Scaling: Maintain correct proportional scaling for both time and amplitude axes
            5. Reference Elements: Keep grid lines, axis markers, and reference levels as straight line elements
            6. Signal Fidelity: Only actual signal traces should use smooth curves; infrastructure remains geometric
            Output optimized SVG with proper coordinate system and efficient path definitions.
            """,
            
            'block_diagram': """
            Convert this block diagram to SVG ensuring system-level accuracy:
            1. Component Blocks: Create precise rectangular blocks with correct dimensions, borders, and fill colors
            2. Connection Intelligence: Analyze original routing - maintain straight orthogonal connections as line elements, apply Bezier curves only to visually curved interconnects
            3. Signal Flow: Implement directional arrow markers showing proper data/signal flow with consistent styling
            4. Text Integration: Position component labels, pin names, and signal descriptions with proper font hierarchy
            5. Hierarchical Structure: Organize SVG elements in logical groups for maintainability and styling
            6. Connection Types: Differentiate between bus lines, single signals, and control connections through line weight and style
            Generate structured SVG with semantic grouping and scalable vector precision.
            """,
            
            'power_architecture': """
            Convert this power architecture diagram to SVG with electrical precision:
            1. Component Symbols: Render standard electrical symbols (transformers, switches, loads) with IEEE/IEC compliance
            2. Power Routing: Preserve original conductor geometry - straight power lines remain as line elements, only curved routing uses path elements with appropriate arc commands
            3. Line Hierarchy: Implement different stroke weights for power transmission, distribution, and control circuits
            4. Flow Indicators: Add directional arrows showing power flow with proper electrical conventions
            5. Component Labels: Position voltage ratings, current ratings, and component identifiers accurately
            6. Circuit Topology: Maintain correct electrical connections and junction points with proper node representation
            7. Safety Annotations: Include protective device symbols and safety markings where present
            Generate electrically-accurate SVG with proper symbol libraries and connection semantics.
            """
        }
    
    def _rate_limit_wait(self):
        """Smart rate limiting to avoid quota exhaustion"""
        time_since_last_call = time.time() - self.last_api_call
        if time_since_last_call < self.min_call_interval:
            wait_time = self.min_call_interval - time_since_last_call
            print(f"⏳ Rate limiting: waiting {wait_time:.1f}s to avoid quota exhaustion...")
            time.sleep(wait_time)
        self.last_api_call = time.time()
    
    def detect_diagram_type(self, image_path: str) -> str:
        """Detect the type of diagram using Gemini with retry logic"""
        image = Image.open(image_path)
        if image.size[0] > self.max_image_size[0] or image.size[1] > self.max_image_size[1]:
            image.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
        
        detection_prompt = """
        Analyze this technical diagram and classify it as one of:
        - flowchart
        - waveform  
        - block_diagram
        - power_architecture
        
        Return only the classification word, nothing else.
        """
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🔍 Detecting diagram type (attempt {attempt + 1}/{max_retries})...")
                
                # Rate limiting before API call
                self._rate_limit_wait()
                
                # Make API call
                response = self.model.generate_content([detection_prompt, image])
                diagram_type = response.text.strip().lower()
                
                valid_types = ['flowchart', 'waveform', 'block_diagram', 'power_architecture']
                detected_type = diagram_type if diagram_type in valid_types else 'block_diagram'
                print(f"✅ Detected type: {detected_type}")
                return detected_type
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Error during detection (attempt {attempt + 1}/{max_retries}): {error_msg}")
                
                # Handle quota errors
                if "429" in error_msg or "quota" in error_msg.lower() or "resource_exhausted" in error_msg.lower():
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                        print(f"⏳ Quota limit hit. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Final retry failed, use fallback
                        print("⚠️ All retries exhausted. Using fallback: block_diagram")
                        return 'block_diagram'
                
                # For other errors, use fallback immediately
                print("⚠️ Using fallback: block_diagram")
                return 'block_diagram'
        
        return 'block_diagram'
    
    def convert_to_svg(self, image_path: str, diagram_type: str = None) -> str:
        """Convert image to SVG code with optimized API usage"""
        
        # OPTIMIZATION: Skip detection if user specified a type
        if diagram_type is None or diagram_type == 'auto':
            diagram_type = self.detect_diagram_type(image_path)
            print(f"📊 Using detected diagram type: {diagram_type}")
        else:
            print(f"📊 Using user-specified diagram type: {diagram_type}")
            print("💡 Skipping auto-detection to save API quota")
        
        # Load and prepare image
        image = Image.open(image_path)
        if image.size[0] > self.max_image_size[0] or image.size[1] > self.max_image_size[1]:
            image.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
        
        # Get specialized prompt for diagram type
        base_prompt = self.diagram_prompts.get(diagram_type, self.diagram_prompts['block_diagram'])
        
        # Enhanced prompt for better SVG generation
        enhanced_prompt = f"""
            {base_prompt}

            CRITICAL SVG GENERATION REQUIREMENTS:

            OUTPUT FORMAT:
            1. Generate ONLY valid SVG XML code - no markdown formatting, no code blocks, no explanations
            2. Start immediately with: <svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
            3. End with closing </svg> tag only

            PATH SYNTAX PRECISION:
            4. Straight connections: Use simple line elements <line x1="x1" y1="y1" x2="x2" y2="y2"/> or path moveto-lineto 'M x1,y1 L x2,y2'
            5. Curved connections: ONLY for visually curved elements in original, use quadratic 'M x1,y1 Q cx,cy x2,y2' or cubic 'M x1,y1 C cx1,cy1 cx2,cy2 x2,y2' Bézier curves
            6. Orthogonal routing: Maintain 90-degree angles for technical diagrams using multiple lineto commands 'M x1,y1 L x2,y1 L x2,y2'

            VISUAL FIDELITY:
            7. Exact proportions: Preserve original aspect ratios and spatial relationships with mathematical precision
            8. Coordinate accuracy: Use integer coordinates for crisp rendering at standard zoom levels
            9. Consistent spacing: Maintain uniform gaps between parallel elements and standard grid alignment

            TECHNICAL SPECIFICATIONS:
            10. Arrow markers: Define once in <defs> section, reference with marker-end="url(#arrowhead)"
            11. Semantic grouping: Use <g> elements with descriptive id attributes for logical organization
            12. Typography: Position text with dominant-baseline="middle" text-anchor="middle" for center alignment
            13. Stroke optimization: Use stroke-width="1.5" for standard lines, "2.5" for emphasis, "1" for fine details
            14. Color consistency: Apply systematic color scheme with proper contrast for accessibility

            STRUCTURE TEMPLATE:
            <svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="currentColor"/>
                </marker>
            </defs>
            
            <g id="components"><!-- Shape elements --></g>
            <g id="connections"><!-- Path and line elements --></g>
            <g id="labels"><!-- Text elements --></g>
            </svg>

            IMPORTANT: Escape all special XML characters in text content:
            - Use &amp; instead of &
            - Use &lt; instead of <
            - Use &gt; instead of >
            - Use &quot; instead of "
            - Use &apos; instead of '

            Generate production-ready SVG with pixel-perfect accuracy and semantic structure.
            """
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🎨 Creating SVG (attempt {attempt + 1}/{max_retries})...")
                
                # Rate limiting before API call
                self._rate_limit_wait()
                
                # Make API call
                response = self.model.generate_content([enhanced_prompt, image])
                
                svg_code = self._extract_svg_code(response.text)
                optimized_svg = self._optimize_svg_code(svg_code)
                
                print("✅ SVG generation complete!")
                return optimized_svg
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Error during conversion (attempt {attempt + 1}/{max_retries}): {error_msg}")
                
                # Handle quota errors with retry
                if "429" in error_msg or "quota" in error_msg.lower() or "resource_exhausted" in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 10  # 10s, 20s, 40s
                        print(f"⏳ Quota limit hit. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(
                            "API quota exceeded after all retries. Please wait 1-2 minutes and try again, "
                            "or consider:\n"
                            "1. Waiting for quota reset (resets every minute)\n"
                            "2. Creating a new Google Cloud project with fresh API key\n"
                            "3. Enabling billing for higher limits at https://aistudio.google.com/"
                        )
                
                # Re-raise other errors
                if attempt == max_retries - 1:
                    raise Exception(f"SVG conversion failed: {error_msg}")
        
        raise Exception("SVG conversion failed after all retries")
    
    def _extract_svg_code(self, response_text: str) -> str:
        """Extract SVG code from Gemini response"""
        text = response_text.strip()
        
        # Remove markdown code blocks
        if '```xml' in text:
            text = text.split('```xml')[1].split('```')[0].strip()
        elif '```svg' in text:
            text = text.split('```svg')[1].split('```')[0].strip()
        elif '```' in text:
            parts = text.split('```')
            if len(parts) >= 2:
                text = parts[1].strip()
        
        # Find SVG content
        svg_match = re.search(r'<svg[^>]*>.*?</svg>', text, re.DOTALL | re.IGNORECASE)
        if svg_match:
            return svg_match.group(0)
        
        # If no complete SVG found, look for SVG start
        if '<svg' in text.lower():
            start_idx = text.lower().find('<svg')
            return text[start_idx:]
        
        return text
    
    def _optimize_svg_code(self, svg_code: str) -> str:
        """🆕 FIXED: Optimize and sanitize the generated SVG with proper XML escaping"""
        
        # Step 1: Fix unescaped ampersands in text and attributes
        # This regex finds & that are not part of existing entities
        svg_code = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', svg_code)
        
        # Step 2: Escape special characters in text content between tags
        def escape_text_content(match):
            text = match.group(1)
            # Only escape if not already escaped and not inside CDATA
            if '<![CDATA[' not in text:
                text = html.escape(text, quote=False)  # Don't escape quotes in text content
            return f'>{text}<'
        
        # Find text between tags and escape
        svg_code = re.sub(r'>([^<>]+)<', escape_text_content, svg_code)
        
        # Step 3: Clean up common invalid patterns
        # Remove any stray < or > in attribute values
        svg_code = re.sub(r'(="[^"]*)<([^"]*")', r'\1&lt;\2', svg_code)
        svg_code = re.sub(r'(="[^"]*)>([^"]*")', r'\1&gt;\2', svg_code)
        
        # Step 4: Add arrow marker definitions if missing
        if 'marker' not in svg_code and ('arrow' in svg_code or 'M ' in svg_code):
            arrow_defs = '''    <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="3" 
                markerWidth="10" markerHeight="10" orient="auto">
            <path d="M0,0 L0,6 L9,3 z" fill="black"/>
        </marker>
        <marker id="curved-arrow" viewBox="0 0 12 12" refX="10" refY="6" 
                markerWidth="12" markerHeight="12" orient="auto">
            <path d="M2,2 L2,10 L10,6 z" fill="blue"/>
        </marker>
    </defs>'''
            
            svg_code = re.sub(r'(<svg[^>]*>)', r'\1\n' + arrow_defs, svg_code)
        
        # Step 5: Ensure proper SVG structure
        if not svg_code.strip().startswith('<svg'):
            svg_code = f'<svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">\n{svg_code}\n</svg>'
        
        # Step 6: Validate and fix xmlns if missing
        if 'xmlns=' not in svg_code:
            svg_code = svg_code.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        
        return svg_code