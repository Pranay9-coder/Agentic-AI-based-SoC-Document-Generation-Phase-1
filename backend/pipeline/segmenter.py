from typing import List, Dict
from utils.helpers import is_bullet

def block_to_level(block: Dict) -> int:
    """
    Determine heading level from block style or size.
    Returns 1-6 for headings, 0 for body text.
    """
    # DOCX: use style name
    style = block.get("style", "").lower()
    if "heading" in style:
        try:
            # Extract number from "Heading 1", "Heading 2", etc.
            n = int(style.split()[-1])
            return max(1, min(6, n))
        except:
            return 2
    
    # PDF: guess from font size
    if "size" in block and block["size"]:
        sz = block["size"]
        if sz >= 16: 
            return 1
        if sz >= 14: 
            return 2
        if sz >= 12.5: 
            return 3
    
    return 0  # body text

def segment(blocks: List[Dict]) -> List[Dict]:
    """
    Build a hierarchical topic tree where each heading becomes a separate node.
    Each node will be written as a separate DITA file.
    """
    topics: List[Dict] = []
    stack: List[Dict] = []  # stack of topic nodes by increasing level

    def start_new_node(title: str, level: int) -> Dict:
        return {
            "title": title or "Untitled", 
            "level": level, 
            "content": [], 
            "children": []
        }

    # Ensure at least one H1 exists
    has_h1 = any(block_to_level(b) == 1 for b in blocks)
    if not has_h1:
        root = start_new_node("Untitled", 1)
        topics.append(root)
        stack = [root]

    for b in blocks:
        kind = b.get("type")
        level = block_to_level(b)
        text = b.get("text", "")

        # Start new nodes on headings
        if level in (1, 2, 3, 4, 5, 6) and text:
            node = start_new_node(text, level)
            
            # Pop stack to the appropriate parent level
            while stack and stack[-1]["level"] >= level:
                stack.pop()
            
            # Add to appropriate parent
            if not stack:
                topics.append(node)
            else:
                stack[-1]["children"].append(node)
            
            stack.append(node)
            continue

        # If there is no current node yet, create a default H1
        if not stack:
            root = start_new_node("Untitled", 1)
            topics.append(root)
            stack = [root]

        current = stack[-1]

        # Content nodes
        if kind == "table":
            current["content"].append({
                "type": "table",
                "rows": b.get("rows", []),
                "spans": b.get("spans"),  # list of (r,c,rowspan,colspan)
            })
        elif kind == "image":
            current["content"].append({
                "type": "image",
                "bytes": b.get("bytes"),
                "ext": b.get("ext", "png"),
                "caption": b.get("caption"),
            })
        else:
            # paragraph or list item based on bullet detection
            if text and is_bullet(text):
                current["content"].append({"type": "list_item", "text": text})
            elif text:
                current["content"].append({"type": "p", "text": text})

    return topics