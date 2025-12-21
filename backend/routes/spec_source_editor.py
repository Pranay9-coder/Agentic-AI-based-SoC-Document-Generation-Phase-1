"""
Spec Source Editor Routes - NEW
File: backend/routes/spec_source_editor.py

Provides endpoints for editing spec_source files and regenerating PDFs
"""
import os
import json
from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import traceback

spec_editor_bp = Blueprint('spec_editor', __name__)


@spec_editor_bp.route('/structure/<session_id>', methods=['GET'])
def get_spec_source_structure(session_id):
    """
    Get the folder structure of all spec_source folders
    Returns a tree structure of all IPs and their files
    """
    try:
        backend_dir = Path(__file__).parent.parent
        session_dir = backend_dir / "spec_outputs" / session_id
        
        if not session_dir.exists():
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        structure = []
        
        # Find all IP folders
        for ip_folder in sorted(session_dir.glob('IP_*')):
            if not ip_folder.is_dir():
                continue
            
            spec_source = ip_folder / "spec_source"
            if not spec_source.exists():
                continue
            
            ip_name = ip_folder.name
            ip_structure = {
                'ip_name': ip_name,
                'folders': {}
            }
            
            # Scan each folder type
            for folder_name in ['dita_topics', 'dita_map', 'regs', 'images']:
                folder_path = spec_source / folder_name
                if folder_path.exists():
                    files = []
                    for file_path in sorted(folder_path.glob('*.*')):
                        if file_path.is_file():
                            files.append({
                                'name': file_path.name,
                                'size': file_path.stat().st_size,
                                'extension': file_path.suffix,
                                'path': str(file_path.relative_to(session_dir))
                            })
                    ip_structure['folders'][folder_name] = files
            
            structure.append(ip_structure)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'ips': structure
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting structure: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@spec_editor_bp.route('/file/<session_id>', methods=['GET'])
def get_file_content(session_id):
    """
    Get content of a specific file
    Query param: path (relative path within session_dir)
    """
    try:
        file_path_param = request.args.get('path')
        if not file_path_param:
            return jsonify({
                'success': False,
                'error': 'Missing path parameter'
            }), 400
        
        backend_dir = Path(__file__).parent.parent
        session_dir = backend_dir / "spec_outputs" / session_id
        full_path = session_dir / file_path_param
        
        # Security check: ensure path is within session_dir
        try:
            full_path.resolve().relative_to(session_dir.resolve())
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 403
        
        if not full_path.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        # For text files (XML, DITA, REGS, ditamap)
        text_extensions = ['.dita', '.ditamap', '.regs', '.xml', '.txt']
        if full_path.suffix.lower() in text_extensions:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return jsonify({
                'success': True,
                'filename': full_path.name,
                'content': content,
                'type': 'text',
                'extension': full_path.suffix
            }), 200
        
        # For images, return file info (content served via download endpoint)
        elif full_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.svg', '.bmp']:
            return jsonify({
                'success': True,
                'filename': full_path.name,
                'type': 'image',
                'extension': full_path.suffix,
                'size': full_path.stat().st_size,
                'download_url': f'/api/spec-editor/download/{session_id}?path={file_path_param}'
            }), 200
        
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported file type'
            }), 400
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@spec_editor_bp.route('/file/<session_id>', methods=['PUT'])
def update_file_content(session_id):
    """
    Update content of a specific file
    Body: { path: str, content: str }
    """
    try:
        data = request.get_json()
        file_path_param = data.get('path')
        new_content = data.get('content')
        
        if not file_path_param or new_content is None:
            return jsonify({
                'success': False,
                'error': 'Missing path or content'
            }), 400
        
        backend_dir = Path(__file__).parent.parent
        session_dir = backend_dir / "spec_outputs" / session_id
        full_path = session_dir / file_path_param
        
        # Security check
        try:
            full_path.resolve().relative_to(session_dir.resolve())
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 403
        
        if not full_path.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        # Only allow editing text files
        text_extensions = ['.dita', '.ditamap', '.regs', '.xml', '.txt']
        if full_path.suffix.lower() not in text_extensions:
            return jsonify({
                'success': False,
                'error': 'Can only edit text files'
            }), 400
        
        # Create backup
        backup_path = full_path.with_suffix(full_path.suffix + '.backup')
        if not backup_path.exists():
            import shutil
            shutil.copy2(str(full_path), str(backup_path))
        
        # Write new content
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Updated: {full_path.name}")
        
        return jsonify({
            'success': True,
            'message': f'File {full_path.name} updated successfully',
            'backup_created': backup_path.exists()
        }), 200
        
    except Exception as e:
        print(f"❌ Error updating file: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@spec_editor_bp.route('/download/<session_id>', methods=['GET'])
def download_file(session_id):
    """
    Download a file (mainly for images)
    Query param: path (relative path within session_dir)
    """
    try:
        file_path_param = request.args.get('path')
        if not file_path_param:
            return jsonify({
                'success': False,
                'error': 'Missing path parameter'
            }), 400
        
        backend_dir = Path(__file__).parent.parent
        session_dir = backend_dir / "spec_outputs" / session_id
        full_path = session_dir / file_path_param
        
        # Security check
        try:
            full_path.resolve().relative_to(session_dir.resolve())
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 403
        
        if not full_path.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        return send_file(
            str(full_path),
            as_attachment=False,
            download_name=full_path.name
        )
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@spec_editor_bp.route('/regenerate-pdf/<session_id>', methods=['POST'])
def regenerate_pdf(session_id):
    """
    Regenerate PDF AND ZIP from edited spec_source files
    """
    try:
        print(f"\n{'='*60}")
        print(f"🔄 Regenerating PDF and ZIP from edited spec_source")
        print(f"{'='*60}")
        
        backend_dir = Path(__file__).parent.parent
        session_dir = backend_dir / "spec_outputs" / session_id
        
        if not session_dir.exists():
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        # Import converter
        from services.multi_ip_converter import MultiIpConverter
        
        api_key = os.getenv('GEMINI_API_KEY')
        converter = MultiIpConverter(gemini_api_key=api_key)
        
        # Regenerate PDF from existing spec_source
        print("📄 Regenerating PDF...")
        result = converter.regenerate_pdf_from_spec_source(session_id)
        
        if result['success']:
            # ✅ ALSO regenerate the ZIP file with edited content
            print(f"\n📦 Regenerating ZIP archive with edited files...")
            try:
                zip_path = converter._create_zip_archive(session_dir)
                print(f"✅ ZIP regenerated: {zip_path.name}")
            except Exception as zip_error:
                print(f"⚠️  ZIP regeneration failed: {zip_error}")
                # Don't fail the whole request if ZIP fails
            
            print(f"\n✅ PDF and ZIP regenerated successfully")
            
            return jsonify({
                'success': True,
                'message': 'PDF and ZIP regenerated successfully',
                'pdf_path': result['pdf_path'],
                'download_pdf_url': f'/api/multi-ip/download-pdf/{session_id}',
                'download_zip_url': f'/api/multi-ip/download-zip/{session_id}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'PDF regeneration failed')
            }), 500
        
    except Exception as e:
        print(f"❌ Regeneration error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@spec_editor_bp.route('/upload-image/<session_id>', methods=['POST'])
def upload_replacement_image(session_id):
    """
    Upload a replacement image for spec_source
    Form data: file, ip_folder (e.g., "IP_1_soc"), filename
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        ip_folder = request.form.get('ip_folder')
        target_filename = request.form.get('filename')
        
        if not ip_folder or not target_filename:
            return jsonify({
                'success': False,
                'error': 'Missing ip_folder or filename'
            }), 400
        
        backend_dir = Path(__file__).parent.parent
        session_dir = backend_dir / "spec_outputs" / session_id
        images_dir = session_dir / ip_folder / "spec_source" / "images"
        
        if not images_dir.exists():
            return jsonify({
                'success': False,
                'error': 'Images directory not found'
            }), 404
        
        # Create backup
        target_path = images_dir / target_filename
        if target_path.exists():
            backup_path = target_path.with_suffix(target_path.suffix + '.backup')
            import shutil
            shutil.copy2(str(target_path), str(backup_path))
        
        # Save new image
        file.save(str(target_path))
        
        print(f"✅ Replaced image: {target_filename}")
        
        return jsonify({
            'success': True,
            'message': f'Image {target_filename} replaced successfully'
        }), 200
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500