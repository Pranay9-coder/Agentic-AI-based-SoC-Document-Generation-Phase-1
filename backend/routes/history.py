"""
API routes for conversion history management
"""
from flask import Blueprint, request, jsonify, current_app
import os
from pathlib import Path
from datetime import datetime
import shutil
import traceback

history_bp = Blueprint('history', __name__)

def get_file_metadata(file_path):
    """Get file metadata including size and modification time"""
    stat = os.stat(file_path)
    return {
        'size': stat.st_size,
        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    }

def scan_dita_conversions(output_base):
    """Scan for DITA conversion outputs (session-based folders)"""
    conversions = []
    
    if not os.path.exists(output_base):
        return conversions
    
    for item in os.listdir(output_base):
        item_path = os.path.join(output_base, item)
        
        # Check if it's a directory (DITA conversions use session IDs as folders)
        if os.path.isdir(item_path):
            # Check if it has DITA structure (topics folder)
            topics_dir = os.path.join(item_path, 'topics')
            if os.path.exists(topics_dir):
                # Find the original file name from topics
                dita_files = list(Path(item_path).rglob('*.dita'))
                ditamap_files = list(Path(item_path).rglob('*.ditamap'))
                
                # Try to get original filename from ditamap or first topic
                filename = "document"
                if ditamap_files:
                    filename = ditamap_files[0].stem
                elif dita_files:
                    filename = dita_files[0].stem
                
                metadata = get_file_metadata(item_path)
                
                conversions.append({
                    'id': item,  # session_id
                    'filename': f"{filename}.dita",
                    'original_name': filename,
                    'type': 'PDF/DOCX → DITA',
                    'conversion_type': 'dita',
                    'date': metadata['modified'],
                    'status': 'Completed',
                    'download_url': f'/api/convert/download/{item}',
                    'topic_count': len(dita_files)
                })
    
    return conversions

def scan_regs_conversions(output_base):
    """Scan for REGS to PDF conversions"""
    conversions = []
    
    if not os.path.exists(output_base):
        return conversions
    
    for item in os.listdir(output_base):
        item_path = os.path.join(output_base, item)
        
        # Check if it's a PDF file (REGS conversions)
        if os.path.isfile(item_path) and item.endswith('.pdf'):
            metadata = get_file_metadata(item_path)
            
            conversions.append({
                'id': item,  # filename
                'filename': item,
                'original_name': item.replace('.pdf', ''),
                'type': 'REGS → PDF',
                'conversion_type': 'regs',
                'date': metadata['modified'],
                'status': 'Completed',
                'size': metadata['size'],
                'download_url': f'/api/regs/download/{item}'
            })
    
    return conversions

def scan_svg_conversions(output_base):
    """Scan for Image to SVG conversions"""
    conversions = []
    
    if not os.path.exists(output_base):
        return conversions
    
    for item in os.listdir(output_base):
        item_path = os.path.join(output_base, item)
        
        # Check if it's an SVG file
        if os.path.isfile(item_path) and item.endswith('.svg'):
            metadata = get_file_metadata(item_path)
            
            conversions.append({
                'id': item,  # filename
                'filename': item,
                'original_name': item.replace('_converted.svg', ''),
                'type': 'Image → SVG',
                'conversion_type': 'svg',
                'date': metadata['modified'],
                'status': 'Completed',
                'size': metadata['size'],
                'download_url': f'/api/history/download-svg/{item}'
            })
    
    return conversions

@history_bp.route('/list', methods=['GET'])
def list_history():
    """
    List all conversion history
    URL: /api/history/list
    Returns: JSON array of all conversions
    """
    try:
        print("\n📋 Fetching conversion history...")
        
        output_base = current_app.config.get('OUTPUT_FOLDER', 'outputs')
        
        # Gather all conversions
        all_conversions = []
        
        # Scan for each type
        dita_conversions = scan_dita_conversions(output_base)
        regs_conversions = scan_regs_conversions(output_base)
        svg_conversions = scan_svg_conversions(output_base)
        
        all_conversions.extend(dita_conversions)
        all_conversions.extend(regs_conversions)
        all_conversions.extend(svg_conversions)
        
        # Sort by date (most recent first)
        all_conversions.sort(key=lambda x: x['date'], reverse=True)
        
        print(f"✅ Found {len(all_conversions)} conversions:")
        print(f"   • DITA: {len(dita_conversions)}")
        print(f"   • REGS: {len(regs_conversions)}")
        print(f"   • SVG: {len(svg_conversions)}")
        
        return jsonify({
            'success': True,
            'count': len(all_conversions),
            'conversions': all_conversions
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching history: {e}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@history_bp.route('/delete/<conversion_type>/<identifier>', methods=['DELETE'])
def delete_conversion(conversion_type, identifier):
    """
    Delete a conversion from history
    URL: /api/history/delete/<conversion_type>/<identifier>
    
    Args:
        conversion_type: 'dita', 'regs', or 'svg'
        identifier: session_id for DITA, filename for others
    """
    try:
        print(f"\n🗑️ Delete request: {conversion_type} / {identifier}")
        
        output_base = current_app.config.get('OUTPUT_FOLDER', 'outputs')
        
        if conversion_type == 'dita':
            # Delete session folder
            folder_path = os.path.join(output_base, identifier)
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                shutil.rmtree(folder_path)
                print(f"✅ Deleted DITA folder: {folder_path}")
            else:
                return jsonify({
                    'success': False,
                    'error': 'Conversion not found'
                }), 404
        
        elif conversion_type == 'regs':
            # Delete PDF file
            file_path = os.path.join(output_base, identifier)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                os.remove(file_path)
                print(f"✅ Deleted REGS PDF: {file_path}")
            else:
                return jsonify({
                    'success': False,
                    'error': 'File not found'
                }), 404
        
        elif conversion_type == 'svg':
            # Delete SVG file
            file_path = os.path.join(output_base, identifier)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                os.remove(file_path)
                print(f"✅ Deleted SVG file: {file_path}")
            else:
                return jsonify({
                    'success': False,
                    'error': 'File not found'
                }), 404
        
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid conversion type'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Conversion deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"❌ Delete error: {e}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@history_bp.route('/download-svg/<filename>', methods=['GET'])
def download_svg(filename):
    """
    Download SVG file
    URL: /api/history/download-svg/<filename>
    """
    try:
        from flask import send_file
        
        print(f"\n📦 SVG download request: {filename}")
        
        output_base = current_app.config.get('OUTPUT_FOLDER', 'outputs')
        file_path = os.path.join(output_base, filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        print(f"✅ Sending SVG file: {filename}")
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='image/svg+xml'
        )
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@history_bp.route('/clear-all', methods=['DELETE'])
def clear_all_history():
    """
    Clear all conversion history (use with caution!)
    URL: /api/history/clear-all
    """
    try:
        print("\n🗑️ Clearing ALL history...")
        
        output_base = current_app.config.get('OUTPUT_FOLDER', 'outputs')
        
        if os.path.exists(output_base):
            # Remove all contents
            for item in os.listdir(output_base):
                item_path = os.path.join(output_base, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            
            print("✅ All history cleared")
        
        return jsonify({
            'success': True,
            'message': 'All history cleared'
        }), 200
        
    except Exception as e:
        print(f"❌ Clear error: {e}")
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500