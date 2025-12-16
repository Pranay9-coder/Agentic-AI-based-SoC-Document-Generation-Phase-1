import os
import time
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, ListFlowable, ListItem
from reportlab.lib.units import inch
from reportlab.lib import colors
from utils.helpers import slugify


def _save_image_if_needed(node, media_dir, topic_slug, index):
    os.makedirs(media_dir, exist_ok=True)
    if node.get("href"):
        # Already saved by DITA writer
        href = node.get("href")
        # Resolve relative path ../media/x to actual file path
        filename = os.path.basename(href)
        return os.path.join(media_dir, filename)
    if node.get("bytes"):
        ext = node.get("ext", "png")
        name = f"{topic_slug}-{index}.{ext}"
        path = os.path.join(media_dir, name)
        with open(path, 'wb') as f:
            f.write(node.get("bytes"))
        return path
    return None


def _summarize_text(text: str, client=None) -> str:
    # If Gemini client available, try to simplify; otherwise do a light extractive summary.
    if client:
        try:
            s = client.simplify_text(text)
            if s:
                return s
        except Exception:
            pass
    # Fallback summarization: first sentence or first ~30 words
    stripped = (text or "").strip()
    if not stripped:
        return ""
    import re
    m = re.split(r"(?<=[.!?])\s+", stripped)
    first_sent = m[0] if m else stripped
    words = first_sent.split()
    if len(words) > 30:
        return " ".join(words[:30]) + "…"
    return first_sent


def _table_with_spans(rows, spans=None):
    # rows: list of lists of strings
    # spans: list of (row, col, rowspan, colspan)
    tbl = Table(rows, hAlign='LEFT')
    style_cmds = [
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]
    if spans:
        for r, c, rs, cs in spans:
            if rs > 1 or cs > 1:
                style_cmds.append(('SPAN', (c, r), (c+cs-1, r+rs-1)))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


# ============================================================================
# EXISTING FUNCTION - DO NOT MODIFY - USED BY OTHER MODULES
# ============================================================================
def write_pdf(doc_struct, out_dir: str, root_title: str, *, single: bool=False, summarize: bool=False, gemini_client=None):
    """Generate PDF(s) for topics. If single=True, combine into one PDF.
    summarize=True uses Gemini to compress paragraphs if client is provided.
    
    NOTE: This function is used by multiple modules. DO NOT MODIFY.
    For multi-IP specific features, use write_multi_ip_pdf() instead.
    """
    pdf_dir = os.path.join(out_dir, "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    media_dir = os.path.join(out_dir, "media")
    styles = getSampleStyleSheet()
    generated_pdfs = []
    summarizer = (lambda t: _summarize_text(t, gemini_client)) if summarize else (lambda t: t)

    def write_topic_pdf(node: dict, parent_slug: str = None) -> str:
        """Write a single PDF for a topic node"""
        title = node.get("title") or ""
        if not title.strip():
            title = "Topic"
        slug_base = slugify(title)
        slug = slug_base if not parent_slug else f"{parent_slug}-{slug_base}"
        pdf_filename = f"{slug}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, title=title)
        story = []
        # Add title
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 0.2 * inch))
        
        img_index = 1
        
        # Add content
        for content_item in node.get("content", []):
            t = content_item.get("type")
            if t == "p":
                text = summarizer(content_item.get("text", ""))
                story.append(Paragraph(text, styles['BodyText']))
                story.append(Spacer(1, 0.1 * inch))
            elif t == "table":
                rows = content_item.get("rows", [])
                if content_item.get("title"):
                    story.append(Paragraph(content_item.get("title"), styles['Heading3']))
                if rows:
                    spans = content_item.get("spans")  # list of (r,c,rowspan,colspan)
                    tbl = _table_with_spans(rows, spans)
                    story.append(tbl)
                    story.append(Spacer(1, 0.15 * inch))
            elif t == "image":
                img_path = _save_image_if_needed(content_item, media_dir, slug, img_index)
                if img_path and os.path.exists(img_path):
                    try:
                        im = Image(img_path)
                        im._restrictSize(5.5 * inch, 5.5 * inch)
                        story.append(im)
                        if content_item.get("caption"):
                            story.append(Paragraph(content_item.get("caption"), styles['Italic']))
                        story.append(Spacer(1, 0.15 * inch))
                        img_index += 1
                    except Exception:
                        pass
        
        doc.build(story)
        return pdf_path

    def process_node_recursive(node: dict, parent_slug: str = None):
        """Recursively process all nodes and generate PDFs"""
        if not isinstance(node, dict):
            return
            
        # Generate PDF for current node
        pdf_path = write_topic_pdf(node, parent_slug)
        generated_pdfs.append(pdf_path)
        
        # Process children
        title = node.get("title", "Untitled")
        slug_base = slugify(title)
        current_slug = slug_base if not parent_slug else f"{parent_slug}-{slug_base}"
        
        for child in node.get("children", []):
            process_node_recursive(child, current_slug)

    if single:
        # Build a single combined PDF
        combined_path = os.path.join(pdf_dir, f"{slugify(root_title)}.pdf")
        doc = SimpleDocTemplate(combined_path, pagesize=A4, title=root_title)
        story = []
        img_index = [1]

        import re
        bullet_re = re.compile(r"^(\s*[\u2022\-\–\*]|\s*\d+[\.)]|\s*[a-zA-Z][\.)])\s+")
        def _strip_bullet(text: str) -> str:
            return bullet_re.sub("", (text or "").strip())

        def _flush_list(list_buf):
            if not list_buf:
                return
            items = [ListItem(Paragraph(_strip_bullet(t), styles['BodyText'])) for t in list_buf]
            story.append(ListFlowable(items, bulletType='bullet', start='•', leftIndent=18))
            story.append(Spacer(1, 0.1 * inch))
            list_buf.clear()

        def _render_node(node: dict, heading_level: int = 1):
            if not isinstance(node, dict):
                return
            title = node.get("title") or "Topic"
            # Choose heading style
            if heading_level <= 1:
                story.append(Paragraph(title, styles['Title']))
            elif heading_level == 2:
                story.append(Paragraph(title, styles['Heading2']))
            else:
                story.append(Paragraph(title, styles['Heading3']))
            story.append(Spacer(1, 0.2 * inch))

            list_buf = []
            for content_item in node.get("content", []):
                t = content_item.get("type")
                if t == "p":
                    _flush_list(list_buf)
                    story.append(Paragraph(summarizer(content_item.get("text", "")), styles['BodyText']))
                    story.append(Spacer(1, 0.1 * inch))
                elif t == "list_item":
                    list_buf.append(content_item.get("text", ""))
                elif t == "table":
                    _flush_list(list_buf)
                    rows = content_item.get("rows", [])
                    if content_item.get("title"):
                        story.append(Paragraph(content_item.get("title"), styles['Heading3']))
                    if rows:
                        spans = content_item.get("spans")
                        tbl = _table_with_spans(rows, spans)
                        story.append(tbl)
                        story.append(Spacer(1, 0.15 * inch))
                elif t == "image":
                    _flush_list(list_buf)
                    img_path = _save_image_if_needed(content_item, media_dir, slugify(title), img_index[0])
                    if img_path and os.path.exists(img_path):
                        try:
                            im = Image(img_path)
                            im._restrictSize(5.5 * inch, 5.5 * inch)
                            story.append(im)
                            if content_item.get("caption"):
                                story.append(Paragraph(content_item.get("caption"), styles['Italic']))
                            story.append(Spacer(1, 0.15 * inch))
                            img_index[0] += 1
                        except Exception:
                            pass
            _flush_list(list_buf)

            for child in node.get("children", []):
                _render_node(child, heading_level + 1)

        # Render all top-level nodes and their descendants
        first = True
        for item in doc_struct:
            if not (isinstance(item, dict) and item.get("level") == 1):
                continue
            if not first:
                story.append(PageBreak())
            _render_node(item, 1)
            first = False
        if story and isinstance(story[-1], PageBreak):
            story.pop()
        doc.build(story)
        generated_pdfs = [combined_path]
    else:
        # Process all top-level nodes separately
        for item in doc_struct:
            if isinstance(item, dict) and item.get("level") == 1:
                process_node_recursive(item)

    return generated_pdfs


# ============================================================================
# NEW FUNCTIONS FOR MULTI-IP - SEPARATE FROM EXISTING FUNCTIONALITY
# ============================================================================

def _batch_summarize_with_gemini(texts: list, api_key: str) -> dict:
    """
    Batch summarize texts using Gemini Flash Lite with rate limiting
    
    Rate Limits: gemini-2.5-flash-lite = 12 RPM
    Strategy: Process in batches with delays to stay under limit
    """
    if not texts or not api_key:
        return {i: text for i, text in enumerate(texts)}
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Use Flash Lite for better rate limits (12 RPM vs 7 RPM)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        summaries = {}
        batch_size = 10  # Process 10 texts per request
        delay_between_requests = 6  # 6 seconds = 10 requests/minute (safe margin)
        
        print(f"  📝 Summarizing {len(texts)} text blocks...")
        print(f"  ⏱️  Using rate-limited batching (10 RPM to stay safe)")
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_indices = list(range(i, min(i+batch_size, len(texts))))
            
            # Create batch prompt
            batch_prompt = "Summarize each of the following technical texts. Keep important technical details and specifications. Remove redundancy. Return summaries in order, separated by '---NEXT---'.\n\n"
            
            for idx, text in enumerate(batch):
                if not text or len(text.strip()) < 50:
                    summaries[batch_indices[idx]] = text
                    continue
                batch_prompt += f"TEXT {idx+1}:\n{text[:1000]}\n\n"  # Limit to 1000 chars per text
            
            if len([t for t in batch if t and len(t.strip()) >= 50]) == 0:
                continue
            
            try:
                # Make API call
                response = model.generate_content(batch_prompt)
                
                if response and response.text:
                    # Split responses
                    results = response.text.split('---NEXT---')
                    
                    for idx, result in enumerate(results):
                        if idx < len(batch_indices):
                            summaries[batch_indices[idx]] = result.strip()
                
                print(f"    ✓ Batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1} complete")
                
                # Rate limiting delay
                if i + batch_size < len(texts):
                    time.sleep(delay_between_requests)
                    
            except Exception as e:
                print(f"    ⚠️  Batch failed, using original: {e}")
                for idx in batch_indices:
                    if idx not in summaries:
                        summaries[idx] = texts[idx]
        
        # Fill any missing with original text
        for i, text in enumerate(texts):
            if i not in summaries:
                summaries[i] = text
        
        print(f"  ✓ Summarization complete")
        return summaries
        
    except Exception as e:
        print(f"  ⚠️  Batch summarization failed: {e}")
        return {i: text for i, text in enumerate(texts)}


def _collect_all_texts_from_doc(doc_struct: list) -> tuple:
    """Collect all paragraph texts from document structure for batch processing"""
    texts = []
    text_map = []  # Track where each text came from
    
    def collect_recursive(node, path):
        if not isinstance(node, dict):
            return
        
        for content_item in node.get("content", []):
            if content_item.get("type") in ["p", "paragraph"]:
                text = content_item.get("text", "")
                if text and len(text.strip()) >= 50:
                    texts.append(text)
                    text_map.append((path, content_item))
        
        for idx, child in enumerate(node.get("children", [])):
            collect_recursive(child, path + [idx])
    
    for idx, item in enumerate(doc_struct):
        collect_recursive(item, [idx])
    
    return texts, text_map


def _apply_summaries_to_doc(doc_struct: list, summaries: dict, text_map: list):
    """Apply summarized texts back to document structure"""
    for idx, (path, content_item) in enumerate(text_map):
        if idx in summaries:
            content_item['text'] = summaries[idx]


def write_multi_ip_pdf(
    doc_struct,
    out_dir: str,
    root_title: str,
    gemini_api_key: str = None
):
    """
    Generate organized PDF for Multi-IP documentation with:
    1. Batch-summarized topic text (rate-limit safe)
    2. Original page images for REGS sections
    
    This is a SEPARATE function that does NOT affect existing write_pdf() functionality.
    """
    pdf_dir = os.path.join(out_dir, "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    media_dir = os.path.join(out_dir, "media")
    styles = getSampleStyleSheet()
    
    print(f"📚 Generating Multi-IP organized PDF...")
    
    # Step 1: Collect all texts that need summarization
    if gemini_api_key:
        print(f"  🤖 Collecting texts for batch summarization...")
        texts, text_map = _collect_all_texts_from_doc(doc_struct)
        
        if texts:
            # Step 2: Batch summarize with rate limiting
            summaries = _batch_summarize_with_gemini(texts, gemini_api_key)
            
            # Step 3: Apply summaries back to doc structure
            _apply_summaries_to_doc(doc_struct, summaries, text_map)
            print(f"  ✓ Applied {len(summaries)} summaries")
    else:
        print(f"  ℹ️  No Gemini API key, skipping summarization")
    
    # Step 4: Build PDF
    combined_path = os.path.join(pdf_dir, f"{slugify(root_title)}.pdf")
    doc = SimpleDocTemplate(combined_path, pagesize=A4, title=root_title)
    story = []
    img_index = [1]
    
    import re
    bullet_re = re.compile(r"^(\s*[\u2022\-\–\*]|\s*\d+[\.)]|\s*[a-zA-Z][\.)])\s+")
    
    def _strip_bullet(text: str) -> str:
        return bullet_re.sub("", (text or "").strip())
    
    def _flush_list(list_buf):
        if not list_buf:
            return
        items = [ListItem(Paragraph(_strip_bullet(t), styles['BodyText'])) for t in list_buf]
        story.append(ListFlowable(items, bulletType='bullet', start='•', leftIndent=18))
        story.append(Spacer(1, 0.1 * inch))
        list_buf.clear()
    
    def _render_node(node: dict, heading_level: int = 1):
        if not isinstance(node, dict):
            return
        
        title = node.get("title") or "Topic"
        
        # Choose heading style
        if heading_level <= 1:
            story.append(Paragraph(title, styles['Title']))
        elif heading_level == 2:
            story.append(Paragraph(title, styles['Heading2']))
        else:
            story.append(Paragraph(title, styles['Heading3']))
        story.append(Spacer(1, 0.2 * inch))
        
        list_buf = []
        for content_item in node.get("content", []):
            t = content_item.get("type")
            
            # ✅ NEW: Handle REGS PDF images (from converted .regs files)
            if t == "regs_pdf_images":
                _flush_list(list_buf)
                image_paths = content_item.get("image_paths", [])
                reg_name = content_item.get("register_name", "Register")
                page_count = content_item.get("page_count", 0)
                
                if image_paths:
                    # Add header
                    story.append(Paragraph(
                        f"<i>Register specification for {reg_name} ({page_count} page{'s' if page_count > 1 else ''}):</i>",
                        styles['BodyText']
                    ))
                    story.append(Spacer(1, 0.1 * inch))
                    
                    # Insert each page image
                    for idx, img_path in enumerate(image_paths, 1):
                        if os.path.exists(img_path):
                            try:
                                im = Image(img_path)
                                # Scale to fit page width while maintaining aspect ratio
                                im._restrictSize(6.5 * inch, 9 * inch)
                                story.append(im)
                                
                                if idx < len(image_paths):
                                    story.append(Spacer(1, 0.1 * inch))
                                
                                print(f"    ✓ Inserted REGS page {idx}/{page_count}: {reg_name}")
                            except Exception as e:
                                print(f"    ⚠️  Could not insert REGS image {idx}: {e}")
                        else:
                            print(f"    ⚠️  Image not found: {img_path}")
                    
                    story.append(Spacer(1, 0.2 * inch))
                else:
                    story.append(Paragraph(
                        f"[REGS specification for {reg_name} - Images unavailable]",
                        styles['BodyText']
                    ))
                    story.append(Spacer(1, 0.1 * inch))
                continue
            
            # OLD: Handle old REGS page image type (kept for compatibility)
            if t == "regs_page_image":
                _flush_list(list_buf)
                img_path = content_item.get("image_path")
                reg_name = content_item.get("register_name", "Register")
                page_num = content_item.get("page_num", 0)
                
                if img_path and os.path.exists(img_path):
                    try:
                        # Add caption
                        story.append(Paragraph(
                            f"<i>Original document page {page_num + 1} - {reg_name} Register Specification</i>",
                            styles['BodyText']
                        ))
                        story.append(Spacer(1, 0.1 * inch))
                        
                        # Insert full page image
                        im = Image(img_path)
                        im._restrictSize(6.5 * inch, 9 * inch)
                        story.append(im)
                        story.append(Spacer(1, 0.2 * inch))
                        
                        print(f"    ✓ Inserted REGS page: {reg_name} (page {page_num + 1})")
                    except Exception as e:
                        print(f"    ⚠️  Could not insert REGS image: {e}")
                        story.append(Paragraph(
                            f"[REGS Page for {reg_name} - Image unavailable]",
                            styles['BodyText']
                        ))
                        story.append(Spacer(1, 0.1 * inch))
                continue
            
            if t in ["p", "paragraph"]:
                _flush_list(list_buf)
                text = content_item.get("text", "")
                story.append(Paragraph(text, styles['BodyText']))
                story.append(Spacer(1, 0.1 * inch))
            elif t == "list_item":
                list_buf.append(content_item.get("text", ""))
            elif t == "table":
                _flush_list(list_buf)
                rows = content_item.get("rows", [])
                if content_item.get("title"):
                    story.append(Paragraph(content_item.get("title"), styles['Heading3']))
                if rows:
                    spans = content_item.get("spans")
                    tbl = _table_with_spans(rows, spans)
                    story.append(tbl)
                    story.append(Spacer(1, 0.15 * inch))
            elif t == "image":
                _flush_list(list_buf)
                img_path = _save_image_if_needed(content_item, media_dir, slugify(title), img_index[0])
                if img_path and os.path.exists(img_path):
                    try:
                        im = Image(img_path)
                        im._restrictSize(5.5 * inch, 5.5 * inch)
                        story.append(im)
                        if content_item.get("caption"):
                            story.append(Paragraph(content_item.get("caption"), styles['Italic']))
                        story.append(Spacer(1, 0.15 * inch))
                        img_index[0] += 1
                    except Exception:
                        pass
        _flush_list(list_buf)
        
        for child in node.get("children", []):
            _render_node(child, heading_level + 1)
    
    # Render all chapters
    first = True
    for item in doc_struct:
        if not (isinstance(item, dict) and item.get("level") == 1):
            continue
        if not first:
            story.append(PageBreak())
        _render_node(item, 1)
        first = False
    
    if story and isinstance(story[-1], PageBreak):
        story.pop()
    
    doc.build(story)
    
    print(f"  ✓ PDF created: {combined_path}")
    
    return [combined_path]