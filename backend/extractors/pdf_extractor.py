import fitz


def extract_pdf(path: str):
    """
    Extract content from PDF with improved heading detection
    """
    doc = fitz.open(path)
    blocks = []
    
    print(f"\n📄 Extracting PDF: {path}")
    print(f"📃 Pages: {len(doc)}")
    
    for page_index, page in enumerate(doc):
        # Text blocks with font information
        text_dict = page.get_text("dict")
        text_blocks = text_dict.get("blocks", [])
        
        for b in text_blocks:
            if "lines" not in b:
                continue
            
            # Collect spans from all lines in this block
            for l in b["lines"]:
                for s in l["spans"]:
                    text = s.get("text", "").strip()
                    if not text:
                        continue
                    
                    # Capture font size and flags for heading detection
                    size = s.get("size", 0)
                    flags = s.get("flags", 0)
                    font = s.get("font", "")
                    
                    blocks.append({
                        "type": "paragraph",
                        "style": "",
                        "text": text,
                        "size": size,
                        "flags": flags,  # Font flags (bold, italic, etc.)
                        "font": font,
                        "page": page_index + 1
                    })
        
        # Extract images
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n >= 5:  # CMYK
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                img_bytes = pix.tobytes("png")
                blocks.append({
                    "type": "image",
                    "bytes": img_bytes,
                    "ext": "png",
                    "page": page_index + 1,
                    "caption": None,
                })
            except Exception as e:
                print(f"⚠️  Error extracting image from page {page_index + 1}: {e}")
                continue

    print(f"✅ Extracted {len(blocks)} blocks from PDF")
    
    # Merge consecutive text blocks into paragraphs
    merged = []
    buf = []
    prev_size = None
    
    for b in blocks:
        if b.get("type") == "paragraph":
            text = b.get("text", "")
            current_size = b.get("size")
            
            # Start new paragraph if:
            # 1. Text ends with period/newline (sentence boundary)
            # 2. Font size changes significantly (likely a heading)
            if text.endswith((".", "!", "?", "\n")) or (prev_size and abs(current_size - prev_size) > 1):
                if buf:
                    buf.append(text.rstrip())
                    merged.append({
                        "type": "paragraph",
                        "style": "",
                        "text": " ".join(buf).strip(),
                        "size": prev_size or current_size
                    })
                    buf = []
                    prev_size = None
                else:
                    merged.append(b)
                    prev_size = current_size
            else:
                buf.append(text)
                prev_size = current_size
        else:
            # Flush buffer before non-text element
            if buf:
                merged.append({
                    "type": "paragraph",
                    "style": "",
                    "text": " ".join(buf).strip(),
                    "size": prev_size
                })
                buf = []
                prev_size = None
            merged.append(b)
    
    # Flush any remaining buffer
    if buf:
        merged.append({
            "type": "paragraph",
            "style": "",
            "text": " ".join(buf).strip(),
            "size": prev_size
        })

    print(f"📦 Merged into {len(merged)} structured blocks")
    
    # Debug: Show sample sizes for heading detection
    sizes = [b.get("size", 0) for b in merged if b.get("type") == "paragraph"]
    if sizes:
        unique_sizes = sorted(set(sizes), reverse=True)
        print(f"📏 Font sizes found: {unique_sizes[:5]}")  # Show top 5 sizes
    
    return {"blocks": merged}