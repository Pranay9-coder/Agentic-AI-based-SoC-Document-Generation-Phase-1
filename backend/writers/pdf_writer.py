import os
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


def write_pdf(doc_struct, out_dir: str, root_title: str, *, single: bool=False, summarize: bool=False, gemini_client=None):
    """Generate PDF(s) for topics. If single=True, combine into one PDF.
    summarize=True uses Gemini to compress paragraphs if client is provided.
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


