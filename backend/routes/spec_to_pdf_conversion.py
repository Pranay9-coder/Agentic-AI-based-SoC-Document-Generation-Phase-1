"""
API routes for Spec Source to PDF Conversion
File: backend/routes/spec_to_pdf_conversion.py

Accepts ZIP containing spec_source folder(s) and generates organized PDF
"""
import os
import time
import zipfile
import shutil
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from services.multi_ip_converter import MultiIpConverter
import uuid
from pathlib import Path
import traceback

spec_to_pdf_bp = Blueprint('spec_to_pdf', __name__)


@spec_to_pdf_bp.route('/convert', methods=['POST'])
def convert_spec_to_pdf():
    """Convert spec_source ZIP to PDF"""
    try:
        print("\n" + "="*60)
        print("🔄 Starting Spec Source to PDF Conversion")
        print("="*60)
        
        # Check file
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Validate ZIP file
        if not file.filename.lower().endswith('.zip'):
            return jsonify({
                'success': False,
                'error': 'Only ZIP files are accepted'
            }), 400
        
        print(f"📦 Received ZIP: {file.filename}")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        print(f"🆔 Session ID: {session_id}")
        
        backend_dir = Path(__file__).parent.parent
        upload_dir = backend_dir / 'uploads' / session_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save ZIP file
        zip_filename = secure_filename(file.filename)
        zip_path = upload_dir / zip_filename
        
        print(f"💾 Saving ZIP...")
        file.save(str(zip_path))
        
        if not zip_path.exists():
            raise Exception(f"Failed to save ZIP file")
        
        print(f"✅ ZIP saved: {zip_path}")
        
        # Extract ZIP
        print(f"📂 Extracting ZIP...")
        extract_dir = upload_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(str(zip_path), 'r') as zip_ref:
            zip_ref.extractall(str(extract_dir))
        
        print(f"✓ ZIP extracted to: {extract_dir}")
        
        # Find spec_source folders
        print(f"🔍 Scanning for spec_source folders...")
        spec_source_folders = find_spec_source_folders(extract_dir)
        
        if not spec_source_folders:
            return jsonify({
                'success': False,
                'error': 'No valid spec_source folders found in ZIP. Expected structure: spec_source/dita_map, spec_source/dita_topics, spec_source/images, spec_source/regs'
            }), 400
        
        print(f"✓ Found {len(spec_source_folders)} spec_source folder(s)")
        for folder in spec_source_folders:
            print(f"  - {folder}")
        
        # Copy spec_source folders to spec_outputs directory
        spec_outputs_base = backend_dir / "spec_outputs"
        session_dir = spec_outputs_base / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Copying spec_source folders to session directory...")
        
        for idx, spec_source_path in enumerate(spec_source_folders, 1):
            # Determine IP name from parent folder or use index
            parent_name = spec_source_path.parent.name
            if parent_name == "extracted" or parent_name == session_id:
                ip_name = f"IP_{idx}"
            else:
                ip_name = parent_name
            
            # Create IP folder structure
            ip_folder = session_dir / ip_name
            dest_spec_source = ip_folder / "spec_source"
            dest_spec_source.mkdir(parents=True, exist_ok=True)
            
            # Copy contents
            for item in spec_source_path.iterdir():
                if item.is_dir():
                    shutil.copytree(str(item), str(dest_spec_source / item.name), dirs_exist_ok=True)
                else:
                    shutil.copy2(str(item), str(dest_spec_source / item.name))
            
            print(f"  ✓ Copied: {ip_name}/spec_source")
        
        # Initialize converter
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        converter = MultiIpConverter(gemini_api_key=gemini_api_key)
        
        # Generate PDF from spec_source
        print(f"📄 Generating PDF from spec_source...")
        result = converter.regenerate_pdf_from_spec_source(session_id)
        
        # Clean up uploads
        try:
            shutil.rmtree(upload_dir)
            print(f"🗑️ Cleaned up uploads")
        except Exception as e:
            print(f"⚠️ Could not clean uploads: {e}")
        
        if result['success']:
            print("="*60)
            print("✅ Conversion completed successfully")
            print("="*60 + "\n")
            
            # Calculate stats
            stats = calculate_stats(session_dir)
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'ip_count': result.get('ip_count', len(spec_source_folders)),
                'stats': stats,
                'message': f'Successfully generated PDF from {len(spec_source_folders)} spec_source folder(s)',
                'download_pdf_url': f'/api/spec-to-pdf/download-pdf/{session_id}'
            }), 200
        else:
            print("="*60)
            print(f"❌ Conversion failed: {result.get('error')}")
            print("="*60 + "\n")
            
            return jsonify({
                'success': False,
                'error': result.get('error', 'PDF generation failed')
            }), 500
        
    except Exception as e:
        print("="*60)
        print(f"❌ Exception in convert_spec_to_pdf:")
        print(traceback.format_exc())
        print("="*60 + "\n")
        
        return jsonify({
            'success': False,
            'error': f'Conversion failed: {str(e)}'
        }), 500


def find_spec_source_folders(root_dir: Path) -> list:
    """
    Recursively find all spec_source folders that contain required subdirectories
    
    Returns list of Path objects pointing to valid spec_source folders
    """
    spec_source_folders = []
    
    # Required subdirectories for a valid spec_source
    required_dirs = {'dita_map', 'dita_topics'}
    
    def scan_directory(directory: Path):
        """Recursively scan directory"""
        for item in directory.iterdir():
            if item.is_dir():
                # Check if this is a spec_source folder
                if item.name == 'spec_source':
                    # Verify it has required subdirectories
                    subdirs = {d.name for d in item.iterdir() if d.is_dir()}
                    if required_dirs.issubset(subdirs):
                        spec_source_folders.append(item)
                        print(f"  ✓ Valid spec_source found: {item.relative_to(root_dir)}")
                    else:
                        print(f"  ⚠️  Invalid spec_source (missing dirs): {item.relative_to(root_dir)}")
                else:
                    # Continue scanning subdirectories
                    scan_directory(item)
    
    scan_directory(root_dir)
    return spec_source_folders


def calculate_stats(session_dir: Path) -> dict:
    """Calculate statistics from spec_source folders"""
    total_topics = 0
    total_regs = 0
    total_images = 0
    
    for ip_folder in session_dir.glob('IP_*'):
        if not ip_folder.is_dir():
            continue
        
        spec_source = ip_folder / 'spec_source'
        if not spec_source.exists():
            continue
        
        # Count DITA topics
        dita_topics_dir = spec_source / 'dita_topics'
        if dita_topics_dir.exists():
            total_topics += len(list(dita_topics_dir.glob('*.dita')))
        
        # Count REGS files
        regs_dir = spec_source / 'regs'
        if regs_dir.exists():
            total_regs += len(list(regs_dir.glob('*.regs')))
        
        # Count images
        images_dir = spec_source / 'images'
        if images_dir.exists():
            total_images += len(list(images_dir.glob('*.*')))
    
    return {
        'total_topics': total_topics,
        'total_regs': total_regs,
        'total_images': total_images
    }


@spec_to_pdf_bp.route('/download-pdf/<session_id>', methods=['GET'])
def download_pdf(session_id):
    """Download generated PDF"""
    try:
        print(f"\n📄 PDF download request: {session_id}")
        
        backend_dir = Path(__file__).parent.parent
        spec_outputs_base = backend_dir / "spec_outputs"
        session_dir = spec_outputs_base / session_id
        pdf_path = session_dir / "organized_soc_documentation.pdf"
        
        print(f"📁 Looking for: {pdf_path}")
        
        if not pdf_path.exists():
            print(f"❌ PDF not found: {pdf_path}")
            return jsonify({
                'success': False,
                'error': 'PDF file not found'
            }), 404
        
        print(f"✅ Sending PDF: {pdf_path.name}")
        
        return send_file(
            str(pdf_path),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='organized_documentation.pdf'
        )
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'Download failed: {str(e)}'
        }), 500


@spec_to_pdf_bp.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'spec-to-pdf',
        'supported_formats': ['zip']
    }), 200


@spec_to_pdf_bp.route('/cleanup/<session_id>', methods=['DELETE'])
def cleanup_session(session_id):
    """Clean up session files"""
    try:
        import shutil
        
        print(f"\n🗑️ Cleanup request: {session_id}")
        
        backend_dir = Path(__file__).parent.parent
        spec_outputs_base = backend_dir / "spec_outputs"
        session_dir = spec_outputs_base / session_id
        
        if session_dir.exists():
            shutil.rmtree(session_dir)
            print(f"✅ Removed: {session_dir}")
        
        return jsonify({
            'success': True,
            'message': 'Session cleaned up'
        }), 200
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        
        return jsonify({
            'success': False,
            'error': f'Cleanup failed: {str(e)}'
        }), 500