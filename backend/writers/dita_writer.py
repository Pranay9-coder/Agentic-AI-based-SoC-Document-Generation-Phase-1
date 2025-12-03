from lxml import etree
from utils.helpers import slugify
import os

NSMAP = {None: "http://dita.oasis-open.org/architecture/2005/"}

def make_topic(title: str, content: list) -> etree._ElementTree:
    """Create a DITA topic XML structure"""
    topic = etree.Element("topic", nsmap=NSMAP)
    title_el = etree.SubElement(topic, "title")
    title_el.text = title

    body = etree.SubElement(topic, "body")

    for node in content:
        t = node.get("type")
        if t == "section":
            sec = etree.SubElement(body, "section")
            st = etree.SubElement(sec, "title")
            st.text = node.get("title","Section")
        elif t == "p":
            p = etree.SubElement(body, "p")
            p.text = node.get("text","")
        elif t == "table":
            rows = node.get("rows", [])
            spans = node.get("spans") or []  # list of (r,c,rowspan,colspan)
            if rows:
                table = etree.SubElement(body, "table")
                if node.get("title"):
                    tbl_title = etree.SubElement(table, "title")
                    tbl_title.text = node.get("title")
                
                # Add a comment showing the spans for debugging
                if spans:
                    comment_text = f" Spans: {spans} "
                    comment = etree.Comment(comment_text)
                    table.append(comment)
                
                tgroup = etree.SubElement(table, "tgroup")
                cols = len(rows[0]) if rows and len(rows[0]) > 0 else 0
                if cols:
                    tgroup.set("cols", str(cols))
                    # define colspec names c1..cN for spanning
                    for i in range(cols):
                        cs = etree.SubElement(tgroup, "colspec")
                        cs.set("colname", f"c{i+1}")
                
                # Create thead before tbody to keep valid order
                thead = etree.SubElement(tgroup, "thead")
                tbody = etree.SubElement(tgroup, "tbody")
                
                # Build a lookup for spans and create a coverage map
                span_lookup = {}
                covered_cells = set()
                
                for (r, c, rowspan, colspan) in spans:
                    span_lookup[(r, c)] = (rowspan, colspan)
                    # Mark all cells covered by this span as occupied
                    for dr in range(rowspan):
                        for dc in range(colspan):
                            if dr > 0 or dc > 0:  # Don't mark the origin cell as covered
                                covered_cells.add((r + dr, c + dc))
                
                for r_index, row in enumerate(rows):
                    container = thead if r_index == 0 else tbody
                    row_el = etree.SubElement(container, "row")
                    
                    # Add row comment for debugging merged rows
                    if any((r_index, c) in span_lookup for c in range(len(row))):
                        row_spans = [(c, span_lookup[(r_index, c)]) for c in range(len(row)) if (r_index, c) in span_lookup]
                        if row_spans:
                            row_comment = etree.Comment(f" Row {r_index} spans: {row_spans} ")
                            row_el.append(row_comment)
                    
                    for c_index, cell_content in enumerate(row):
                        # Skip cells that are covered by spans from other cells
                        if (r_index, c_index) in covered_cells:
                            # Add comment showing this cell is covered
                            covered_comment = etree.Comment(f" Cell ({r_index},{c_index}) covered by span ")
                            row_el.append(covered_comment)
                            continue
                            
                        # Create the entry
                        cell_el = etree.SubElement(row_el, "entry")
                        cell_el.text = cell_content or ""
                        
                        # Apply span attributes if this cell has spans
                        if (r_index, c_index) in span_lookup:
                            rowspan, colspan = span_lookup[(r_index, c_index)]
                            
                            # Add attributes to show span information clearly
                            if rowspan > 1 or colspan > 1:
                                cell_el.set("outputclass", f"span-r{rowspan}-c{colspan}")
                            
                            # Handle colspan (horizontal span)
                            if colspan > 1:
                                cell_el.set("namest", f"c{c_index+1}")
                                cell_el.set("nameend", f"c{c_index+colspan}")
                            
                            # Handle rowspan (vertical span) 
                            if rowspan > 1:
                                cell_el.set("morerows", str(rowspan-1))
                                # Add a clear comment about the rowspan
                                span_comment = etree.Comment(f" This cell spans {rowspan} rows ")
                                cell_el.append(span_comment)
        elif t == "image":
            href = node.get("href")
            if href:
                fig = etree.SubElement(body, "fig")
                image = etree.SubElement(fig, "image")
                image.set("href", href)
                caption = node.get("caption")
                if caption:
                    title = etree.SubElement(fig, "title")
                    title.text = caption
        elif t == "list_item":
            # group consecutive list items into a single <ul>
            pass
    # Second pass for lists (grouping)
    regroup_lists(body)
    return etree.ElementTree(topic)

def regroup_lists(body):
    """Group consecutive list items into proper list structures"""
    items = []
    for child in list(body):
        if child.tag.endswith('p') and child.text and is_listy(child.text):
            items.append(child)
        else:
            if items:
                ul = etree.Element("ul")
                for it in items:
                    li = etree.SubElement(ul, "li")
                    li.text = strip_bullet(it.text)
                    body.replace(it, ul)  # replace first occurrence
                    for rem in items[1:]:
                        body.remove(rem)
                items.clear()
    if items:
        ul = etree.Element("ul")
        for it in items:
            li = etree.SubElement(ul, "li")
            li.text = strip_bullet(it.text)
            body.replace(items[0], ul)
            for rem in items[1:]:
                body.remove(rem)

def is_listy(text: str) -> bool:
    """Check if text looks like a list item"""
    import re
    return bool(re.match(r"^(\s*[\u2022\-\–\*]|\s*\d+[\.)]|\s*[a-zA-Z][\.)])\s+.+", text.strip()))

def strip_bullet(text: str) -> str:
    """Remove bullet/number from beginning of list item"""
    import re
    return re.sub(r"^(\s*[\u2022\-\–\*]|\s*\d+[\.)]|\s*[a-zA-Z][\.)])\s+", "", text.strip())


def write_topics_and_map(doc_struct: list, out_dir: str, root_title: str):
    """
    Write DITA topic files and map.
    Creates separate .dita file for each node in the document structure.
    """
    print(f"\n=== Writing DITA Files ===")
    print(f"Output directory: {out_dir}")
    print(f"Root title: {root_title}")
    
    os.makedirs(out_dir, exist_ok=True)

    topic_dir = os.path.join(out_dir, "topics")
    os.makedirs(topic_dir, exist_ok=True)
    media_dir = os.path.join(out_dir, "media")
    os.makedirs(media_dir, exist_ok=True)

    written = []  # [(node, filename)]
    image_topics_by_node = {}  # id(node) -> [filename]

    def rewrite_and_save_media(title: str, content: list) -> list:
        """Save media files and update content references"""
        rewritten = []
        image_index = 1
        for node in content:
            if node.get("type") == "image" and node.get("bytes"):
                ext = node.get("ext", "png").lower()
                media_name = f"{slugify(title)}-{image_index}.{ext}"
                media_path = os.path.join(media_dir, media_name)
                try:
                    with open(media_path, 'wb') as f:
                        f.write(node.get("bytes"))
                    node_copy = dict(node)
                    node_copy.pop("bytes", None)
                    node_copy["href"] = f"../media/{media_name}"
                    rewritten.append(node_copy)
                    print(f"  Saved media: {media_name}")
                    image_index += 1
                except Exception as e:
                    print(f"  Error saving media: {e}")
                    continue
            else:
                rewritten.append(node)
        return rewritten

    def _write_image_topic(title: str, href: str, caption: str = None, parent_slug: str = None, index: int = 1) -> str:
        """Create a separate topic file for an image"""
        img_title = f"Figure: {title} {index}"
        slug_base = slugify(img_title)
        slug = slug_base if not parent_slug else f"{parent_slug}-{slug_base}"
        filename = f"{slug}.dita"
        # Build a minimal topic with a fig linking to the image
        topic = etree.Element("topic", nsmap=NSMAP)
        t_el = etree.SubElement(topic, "title")
        t_el.text = img_title
        body = etree.SubElement(topic, "body")
        fig = etree.SubElement(body, "fig")
        if caption:
            cap_el = etree.SubElement(fig, "title")
            cap_el.text = caption
        image = etree.SubElement(fig, "image")
        image.set("href", href)
        filepath = os.path.join(topic_dir, filename)
        etree.ElementTree(topic).write(filepath, pretty_print=True, xml_declaration=True, encoding="utf-8")
        print(f"  Created image topic: {filename}")
        return filename

    def save_node_recursive(node: dict, parent_slug: str = None) -> str:
        """
        Recursively save each node as a separate DITA file.
        This is KEY - each node becomes its own .dita file.
        """
        title = node.get("title", "Untitled")
        slug_base = slugify(title)
        slug = slug_base if not parent_slug else f"{parent_slug}-{slug_base}"
        filename = f"{slug}.dita"
        
        print(f"  Creating topic: {filename} (title: {title[:50]})")
        
        # Save current topic
        content = rewrite_and_save_media(title, node.get("content", []))
        tree = make_topic(title, content)
        filepath = os.path.join(topic_dir, filename)
        tree.write(filepath, pretty_print=True, xml_declaration=True, encoding="utf-8")
        
        # Additionally, for each image in content, create a standalone image topic
        img_index = 1
        for c in content:
            if c.get("type") == "image" and c.get("href"):
                img_topic_fname = _write_image_topic(title, c.get("href"), c.get("caption"), parent_slug=slug, index=img_index)
                image_topics_by_node.setdefault(id(node), []).append(img_topic_fname)
                img_index += 1
        
        # Recurse children - IMPORTANT: each child also gets its own file
        for child in node.get("children", []):
            save_node_recursive(child, slug)
        
        written.append((node, filename))
        return filename

    # Write all top-level nodes and their descendants
    # This is where the magic happens - each node in doc_struct gets processed
    top_level_files = []
    for node in doc_struct:
        if not isinstance(node, dict):
            continue
        if node.get("level") == 1:
            top_level_files.append(save_node_recursive(node))

    print(f"\nCreated {len(written)} topic files")

    # Build DITAMAP with nested topicrefs
    print("\n=== Creating DITAMAP ===")
    map_root = etree.Element("map", nsmap=NSMAP)
    title_el = etree.SubElement(map_root, "title")
    title_el.text = root_title

    def build_topicref(el_parent, node: dict, parent_slug: str = None):
        """Build nested topicref structure matching the document hierarchy"""
        title = node.get("title", "Untitled")
        slug_base = slugify(title)
        slug = slug_base if not parent_slug else f"{parent_slug}-{slug_base}"
        href = f"topics/{slug}.dita"
        tr = etree.SubElement(el_parent, "topicref")
        tr.set("href", href)
        
        # Add image-only topics under the node
        for img_fname in image_topics_by_node.get(id(node), []):
            img_tr = etree.SubElement(tr, "topicref")
            img_tr.set("href", f"topics/{img_fname}")
        
        # Recursively add child topics
        for child in node.get("children", []):
            build_topicref(tr, child, slug)

    for node in doc_struct:
        if not isinstance(node, dict):
            continue
        if node.get("level") == 1:
            build_topicref(map_root, node)

    # Write the ditamap file
    ditamap_path = os.path.join(out_dir, f"{slugify(root_title)}.ditamap")
    from lxml import etree as ET
    ET.ElementTree(map_root).write(ditamap_path, pretty_print=True, xml_declaration=True, encoding="utf-8")
    print(f"Created ditamap: {ditamap_path}")