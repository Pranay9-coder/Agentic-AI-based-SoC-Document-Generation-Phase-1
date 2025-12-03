from typing import List, Dict


def enrich_with_gemini(doc_struct: List[Dict], gemini_client) -> List[Dict]:
    for item in doc_struct:
        if not isinstance(item, dict):
            continue
        if item.get("level") != 1:
            continue
        content = item.get("content", [])
        for node in content:
            t = node.get("type")
            if t == "image" and not node.get("caption") and node.get("bytes"):
                cap = gemini_client.caption_image(node.get("bytes"))
                if cap:
                    node["caption"] = cap
            elif t == "table" and not node.get("title"):
                rows = node.get("rows") or []
                if rows:
                    title = gemini_client.title_table(rows)
                    if title:
                        node["title"] = title
        # Optionally simplify body paragraphs (disabled by default)
        # for node in content:
        #     if node.get("type") == "p":
        #         simp = gemini_client.simplify_text(node.get("text",""))
        #         if simp:
        #             node["text"] = simp
    return doc_struct


