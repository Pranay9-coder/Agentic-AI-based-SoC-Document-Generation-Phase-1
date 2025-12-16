"""
API routes for Multi-IP Documentation Generation - FIXED
File: backend/routes/multi_ip_conversion.py
"""
import os
import time
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from services.multi_ip_converter import MultiIpConverter
import uuid
from pathlib import Path
import traceback

multi_ip_bp = Blueprint('multi_ip', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@multi_ip_bp.route('/convert', methods=['POST'])
def convert_multi_ip():
    """Convert multiple IP documents"""
    try:
        print("\n" + "="*60)
        print("🔄 Starting Multi-IP Documentation Generation")
        print("="*60)
        
        # Check files
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files uploaded'
            }), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400
        
        # Validate files
        invalid_files = []
        for file in files:
            if file.filename == '' or not allowed_file(file.filename):
                invalid_files.append(file.filename)
        
        if invalid_files:
            return jsonify({
                'success': False,
                'error': f'Invalid files: {", ".join(invalid_files)}'
            }), 400
        
        print(f"📄 Received {len(files)} file(s)")
        for file in files:
            print(f"  • {file.filename}")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        print(f"🆔 Session ID: {session_id}")
        
        # ✅ Use uploads folder
        backend_dir = Path(__file__).parent.parent
        upload_dir = backend_dir / 'uploads' / session_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save files
        saved_file_paths = []
        for file in files:
            filename = secure_filename(file.filename)
            file_path = upload_dir / filename
            
            print(f"💾 Saving: {filename}")
            file.save(str(file_path))
            
            if not file_path.exists():
                raise Exception(f"Failed to save: {filename}")
            
            saved_file_paths.append(str(file_path))
        
        print(f"✅ All files saved")
        
        # Get API key
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            print("⚠️  GEMINI_API_KEY not set")
        
        # Initialize converter
        print("🔧 Initializing converter...")
        converter = MultiIpConverter(gemini_api_key=gemini_api_key)
        
        # Convert (this might take time for multiple files)
        print("🔄 Starting conversion...")
        result = converter.convert_multi_ip(
            file_paths=saved_file_paths,
            session_id=session_id
        )
        
        # Clean up uploads
        try:
            import shutil
            shutil.rmtree(upload_dir)
            print(f"🗑️ Cleaned up uploads")
        except Exception as e:
            print(f"⚠️ Could not clean uploads: {e}")
        
        if result['success']:
            print("="*60)
            print("✅ Conversion completed successfully")
            print("="*60 + "\n")
            
            # ✅ Ensure files are fully written before responding
            time.sleep(1)  # Give filesystem time to flush
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'ip_count': result['ip_count'],
                'stats': result['stats'],
                'message': f'Successfully processed {result["ip_count"]} IP(s)',
                'download_zip_url': f'/api/multi-ip/download-zip/{session_id}',
                'download_pdf_url': f'/api/multi-ip/download-pdf/{session_id}'
            }), 200
        else:
            print("="*60)
            print(f"❌ Conversion failed: {result.get('error')}")
            print("="*60 + "\n")
            
            return jsonify({
                'success': False,
                'error': result.get('error', 'Conversion failed')
            }), 500
        
    except Exception as e:
        print("="*60)
        print(f"❌ Exception in convert_multi_ip:")
        print(traceback.format_exc())
        print("="*60 + "\n")
        
        return jsonify({
            'success': False,
            'error': f'Conversion failed: {str(e)}'
        }), 500


@multi_ip_bp.route('/download-zip/<session_id>', methods=['GET'])
def download_zip(session_id):
    """Download ZIP archive"""
    try:
        print(f"\n📦 ZIP download request: {session_id}")
        
        backend_dir = Path(__file__).parent.parent
        spec_outputs_base = backend_dir / "spec_outputs"
        session_dir = spec_outputs_base / session_id
        zip_path = session_dir / "spec_outputs.zip"
        
        print(f"📁 Looking for: {zip_path}")
        
        if not zip_path.exists():
            print(f"❌ ZIP not found: {zip_path}")
            return jsonify({
                'success': False,
                'error': 'ZIP file not found'
            }), 404
        
        print(f"✅ Sending ZIP: {zip_path.name}")
        
        return send_file(
            str(zip_path),
            mimetype='application/zip',
            as_attachment=True,
            download_name='spec_outputs.zip'
        )
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'Download failed: {str(e)}'
        }), 500


@multi_ip_bp.route('/download-pdf/<session_id>', methods=['GET'])
def download_pdf(session_id):
    """Download organized PDF"""
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
            download_name='organized_soc_documentation.pdf'
        )
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'Download failed: {str(e)}'
        }), 500


@multi_ip_bp.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'multi-ip-doc-gen',
        'supported_formats': ['pdf', 'docx', 'doc']
    }), 200


@multi_ip_bp.route('/cleanup/<session_id>', methods=['DELETE'])
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