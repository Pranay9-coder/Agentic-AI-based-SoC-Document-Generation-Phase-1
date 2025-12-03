import re, unicodedata
import os

def slugify(text: str) -> str:
    """Create very short, meaningful slugs for DITA filenames"""
    if not text or not text.strip():
        return "topic"
    
    # Normalize and clean
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9\-\_\s]", "", text)
    text = text.strip().lower()
    
    # Define key terms that should be prioritized
    key_terms = {
        'abstract': 'abstract',
        'introduction': 'intro', 
        'background': 'background',
        'summary': 'summary',
        'conclusion': 'conclusion',
        'method': 'method',
        'result': 'results',
        'discussion': 'discussion',
        'claim': 'claims',
        'patent': 'patent',
        'invention': 'invention',
        'technical': 'technical',
        'field': 'field',
        'prior': 'prior-art',
        'art': 'art',
        'description': 'description',
        'figure': 'figure',
        'table': 'table',
        'example': 'example',
        'embodiment': 'embodiment',
        'implementation': 'impl',
        'specification': 'spec',
        'requirements': 'req',
        'design': 'design',
        'architecture': 'arch',
        'overview': 'overview',
        'details': 'details',
        'procedure': 'procedure',
        'process': 'process',
        'system': 'system',
        'apparatus': 'apparatus',
        'device': 'device',
        'component': 'component',
        'element': 'element',
        'configuration': 'config',
        'setup': 'setup',
        'installation': 'install',
        'operation': 'operation',
        'usage': 'usage',
        'reference': 'ref',
        'appendix': 'appendix'
    }
    
    # Look for key terms first
    words = text.split()
    for word in words:
        if word in key_terms:
            return key_terms[word]
    
    # If no key terms found, try partial matches
    for word in words:
        for key, short in key_terms.items():
            if key in word or word in key:
                return short
    
    # Fallback: use first meaningful word(s), max 8 chars
    stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
    
    meaningful_words = [w for w in words if w and w not in stop_words and len(w) > 2]
    
    if meaningful_words:
        # Use first word, truncated to 8 chars max
        first_word = meaningful_words[0][:8]
        return first_word
    
    # Last resort: use first non-stop word
    for word in words:
        if word and word not in stop_words:
            return word[:8]
    
    return "topic"


def make_safe_filename(text: str, max_length: int = 50) -> str:
    """Create filesystem-safe directory/filenames while preserving meaning"""
    if not text or not text.strip():
        return "document"
    
    # Remove/replace problematic characters
    safe_text = re.sub(r'[<>:"/\\|?*]', '-', text.strip())
    safe_text = re.sub(r'\s+', '-', safe_text)  # Replace spaces with hyphens
    safe_text = re.sub(r'-+', '-', safe_text)   # Collapse multiple hyphens
    safe_text = safe_text.strip('-')            # Remove leading/trailing hyphens
    
    # Limit length but try to preserve words
    if len(safe_text) > max_length:
        # Try to cut at word boundary
        truncated = safe_text[:max_length]
        last_hyphen = truncated.rfind('-')
        if last_hyphen > max_length // 2:  # Only if we keep at least half
            safe_text = safe_text[:last_hyphen]
        else:
            safe_text = truncated
    
    return safe_text or "document"

def is_bullet(text: str) -> bool:
    return bool(re.match(r"^(\s*[\u2022\-\–\*]|\s*\d+[\.)]|\s*[a-zA-Z][\.)])\s+.+", text.strip()))

def split_numbered(text: str):
    m = re.match(r"^(\s*(\d+|[a-zA-Z])[\.)])\s+(.*)$", text.strip())
    if m:
        return m.group(1), m.group(3)
    return None, text.strip()


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path

