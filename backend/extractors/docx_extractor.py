from docx import Document
from docx.oxml.ns import qn


def _get_paragraph_text(p_el) -> str:
    texts = []
    for t in p_el.xpath('.//w:t'):
        if t.text:
            texts.append(t.text)
    return ("".join(texts)).strip()


def _extract_images_from_element(doc: Document, el) -> list:
    # Finds images referenced in the element via Drawing/Blip relationships
    images = []
    for blip in el.xpath('.//a:blip'):
        r_id = blip.get(qn('r:embed'))
        if not r_id:
            continue
        part = doc.part.related_parts.get(r_id)
        if not part:
            continue
        blob = getattr(part, 'blob', None)
        filename = getattr(part, 'filename', None) or ''
        ext = ''
        if filename and '.' in filename:
            ext = filename.split('.')[-1].lower()
        images.append({
            'type': 'image',
            'bytes': blob,
            'ext': ext or 'png',
            'caption': None,
        })
    return images


def _extract_table_rows(tbl_el) -> tuple[list, list]:
    # First pass: get cells with gridSpan and vMerge flags per row
    raw_rows: list[list[dict]] = []
    for tr in tbl_el.xpath('./w:tr'):
        row_cells = []
        for tc in tr.xpath('./w:tc'):
            texts = [t.text for t in tc.xpath('.//w:t') if t.text]
            cell_text = (" ".join(texts)).strip()
            # gridSpan (horizontal merge)
            gs_el = tc.xpath('./w:tcPr/w:gridSpan')
            colspan = 1
            if gs_el:
                try:
                    val = gs_el[0].get(qn('w:val')) or gs_el[0].get('w:val')
                    if val:
                        colspan = int(val)
                except Exception:
                    colspan = 1
            # vMerge (vertical merge)
            vm_el = tc.xpath('./w:tcPr/w:vMerge')
            vmerge = None
            if vm_el:
                vval = vm_el[0].get(qn('w:val')) or vm_el[0].get('w:val')
                if vval == 'restart' or vval is None:  # None means restart in DOCX
                    vmerge = 'restart'
                else:
                    vmerge = 'continue'
            row_cells.append({'text': cell_text, 'colspan': colspan, 'vmerge': vmerge})
        raw_rows.append(row_cells)

    if not raw_rows:
        return [], []

    # Build a proper grid by processing merges correctly
    # First, determine table dimensions
    max_physical_cols = max(len(row) for row in raw_rows)
    
    # Create a grid to track cell placements
    grid = []
    spans = []
    
    # Track active vertical merges: col -> {'start_row': int, 'text': str}
    active_vmerges = {}
    
    for r_idx, raw_row in enumerate(raw_rows):
        grid_row = [''] * max_physical_cols
        physical_col = 0
        
        for cell in raw_row:
            # Find next available position (skip columns occupied by vertical merges)
            while physical_col < max_physical_cols:
                if physical_col not in active_vmerges:
                    break
                # This column is occupied by a vertical merge from previous row
                grid_row[physical_col] = active_vmerges[physical_col]['text']
                physical_col += 1
            
            if physical_col >= max_physical_cols:
                break
                
            text = cell['text']
            colspan = cell.get('colspan', 1)
            vmerge = cell.get('vmerge')
            
            # Place the cell text
            grid_row[physical_col] = text
            
            # Handle horizontal spans
            if colspan > 1:
                spans.append((r_idx, physical_col, 1, colspan))
                # Fill merged columns with empty string
                for i in range(1, colspan):
                    if physical_col + i < max_physical_cols:
                        grid_row[physical_col + i] = ''
            
            # Handle vertical merges
            if vmerge == 'restart':
                # Start a new vertical merge
                active_vmerges[physical_col] = {
                    'start_row': r_idx,
                    'text': text,
                    'rowspan': 1
                }
            elif vmerge == 'continue':
                # Continue existing vertical merge
                if physical_col in active_vmerges:
                    active_vmerges[physical_col]['rowspan'] += 1
                    grid_row[physical_col] = active_vmerges[physical_col]['text']
            else:
                # End any active vertical merge in this column
                if physical_col in active_vmerges:
                    merge_info = active_vmerges[physical_col]
                    if merge_info['rowspan'] > 1:
                        spans.append((merge_info['start_row'], physical_col, merge_info['rowspan'], 1))
                    del active_vmerges[physical_col]
            
            physical_col += colspan
        
        # Check for ending vertical merges at row boundary
        to_remove = []
        for col, merge_info in active_vmerges.items():
            # If next row doesn't continue this merge, end it
            next_row_continues = False
            if r_idx + 1 < len(raw_rows):
                # Look ahead to see if next row continues this merge
                next_raw_row = raw_rows[r_idx + 1]
                cell_idx = 0
                check_col = 0
                for next_cell in next_raw_row:
                    if check_col == col and next_cell.get('vmerge') == 'continue':
                        next_row_continues = True
                        break
                    check_col += next_cell.get('colspan', 1)
                    cell_idx += 1
            
            if not next_row_continues:
                if merge_info['rowspan'] > 1:
                    spans.append((merge_info['start_row'], col, merge_info['rowspan'], 1))
                to_remove.append(col)
        
        for col in to_remove:
            del active_vmerges[col]
        
        grid.append(grid_row)
    
    # Handle any remaining active vertical merges
    for col, merge_info in active_vmerges.items():
        if merge_info['rowspan'] > 1:
            spans.append((merge_info['start_row'], col, merge_info['rowspan'], 1))
    
    return grid, spans


def extract_docx(path: str):
    doc = Document(path)
    blocks = []

    # Iterate body children to preserve order of paragraphs, tables, and images
    body = doc.element.body
    for child in body.iterchildren():
        if child.tag == qn('w:p'):
            # paragraph text
            text = _get_paragraph_text(child)
            style = ''
            try:
                # Derive style if present
                p_style = child.xpath('./w:pPr/w:pStyle')
                if p_style:
                    style_val = p_style[0].get(qn('w:val')) or ''
                    style = style_val
            except Exception:
                style = ''
            if text:
                blocks.append({
                    'type': 'paragraph',
                    'style': style,
                    'text': text,
                })
            # inline images within this paragraph
            images = _extract_images_from_element(doc, child)
            blocks.extend(images)

        elif child.tag == qn('w:tbl'):
            rows, spans = _extract_table_rows(child)
            blocks.append({
                'type': 'table',
                'rows': rows,
                'spans': spans,
            })
            # images possibly inside table
            images = _extract_images_from_element(doc, child)
            blocks.extend(images)

    return {'blocks': blocks}
