from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import os
import uuid
import shutil
from pathlib import Path
import traceback

from services.dita_converter import DITAConverter

conversion_bp = Blueprint('conversion', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# CRITICAL FIX: Changed from '/convert' to '/' because blueprint already has prefix '/api/convert'
@conversion_bp.route('/', methods=['POST'])
def convert_file():
    """
    Main conversion endpoint
    URL: /api/convert (blueprint prefix + this route)
    Accepts: multipart/form-data with 'file' and optional 'doc_title'
    Returns: JSON with session_id and conversion stats
    """
    try:
        print("\n" + "="*60)
        print("🔄 Starting DITA conversion request")
        print("="*60)
        
        # Validate file presence
        if 'file' not in request.files:
            print("❌ Error: No file provided")
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            print("❌ Error: No file selected")
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            print(f"❌ Error: Invalid file type: {file.filename}")
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        print(f"📄 File received: {file.filename}")
        
        # Get optional document title
        doc_title = request.form.get('doc_title', '')
        if not doc_title:
            doc_title = file.filename.rsplit('.', 1)[0]
        
        print(f"📝 Document title: {doc_title}")
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        print(f"🆔 Session ID: {session_id}")
        
        # Get config folders
        upload_base = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        output_base = current_app.config.get('OUTPUT_FOLDER', 'outputs')
        
        print(f"📁 Upload base: {upload_base}")
        print(f"📁 Output base: {output_base}")
        
        # Create session directories
        upload_dir = Path(upload_base) / session_id
        output_dir = Path(output_base) / session_id
        
        print(f"📁 Creating upload dir: {upload_dir}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Creating output dir: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify directories were created
        if not upload_dir.exists():
            raise Exception(f"Failed to create upload directory: {upload_dir}")
        if not output_dir.exists():
            raise Exception(f"Failed to create output directory: {output_dir}")
        
        print(f"✅ Directories created successfully")
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = upload_dir / filename
        
        print(f"💾 Saving file to: {file_path}")
        file.save(str(file_path))
        
        if not file_path.exists():
            raise Exception(f"Failed to save file: {file_path}")
        
        print(f"✅ File saved successfully")
        
        # Determine file type
        file_ext = filename.rsplit('.', 1)[1].lower()
        print(f"📋 File type: {file_ext}")
        
        # Initialize converter
        print("🔧 Initializing DITA converter...")
        converter = DITAConverter()
        
        # Perform conversion
        print("🔄 Starting conversion process...")
        result = converter.convert(
            file_path=str(file_path),
            file_type=file_ext,
            output_dir=str(output_dir),
            doc_title=doc_title
        )
        
        print(f"📊 Conversion result: {result}")
        
        if result['success']:
            # Verify output structure
            topics_dir = output_dir / 'topics'
            media_dir = output_dir / 'media'
            
            print(f"🔍 Checking output structure:")
            print(f"  • Topics dir exists: {topics_dir.exists()}")
            print(f"  • Media dir exists: {media_dir.exists()}")
            
            if topics_dir.exists():
                topic_files = list(topics_dir.glob('*.dita'))
                print(f"  • Topic files: {len(topic_files)}")
            
            if media_dir.exists():
                media_files = list(media_dir.glob('*'))
                print(f"  • Media files: {len(media_files)}")
            
            print("="*60)
            print("✅ DITA conversion completed successfully")
            print("="*60 + "\n")
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'stats': result['stats'],
                'message': 'Conversion completed successfully'
            }), 200
        else:
            print("="*60)
            print(f"❌ DITA conversion failed: {result.get('error')}")
            print("="*60 + "\n")
            
            return jsonify({
                'success': False,
                'error': result.get('error', 'Conversion failed')
            }), 500
            
    except Exception as e:
        print("="*60)
        print(f"❌ Exception in convert_file:")
        print(traceback.format_exc())
        print("="*60 + "\n")
        
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@conversion_bp.route('/download/<session_id>', methods=['GET'])
def download_output(session_id):
    """
    Download converted DITA package as ZIP
    URL: /api/convert/download/<session_id>
    """
    try:
        print(f"\n📦 Download request for session: {session_id}")
        
        output_base = current_app.config.get('OUTPUT_FOLDER', 'outputs')
        output_dir = Path(output_base) / session_id
        
        print(f"📁 Looking in: {output_dir}")
        
        if not output_dir.exists():
            print(f"❌ Session directory not found: {output_dir}")
            return jsonify({
                'success': False,
                'error': 'Session not found or expired'
            }), 404
        
        # Create ZIP file
        zip_path = output_dir / 'dita-package.zip'
        
        print(f"📦 Creating ZIP at: {zip_path}")
        
        # Import here to avoid circular imports
        import zipfile
        
        with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from output directory
            file_count = 0
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    if file == 'dita-package.zip':
                        continue
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(output_dir)
                    zipf.write(str(file_path), str(arcname))
                    file_count += 1
            
            print(f"✅ Added {file_count} files to ZIP")
        
        print(f"✅ Sending ZIP file: {zip_path}")
        
        # Send file
        return send_file(
            str(zip_path),
            mimetype='application/zip',
            as_attachment=True,
            download_name='dita-package.zip'
        )
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'Download failed: {str(e)}'
        }), 500

@conversion_bp.route('/cleanup/<session_id>', methods=['DELETE'])
def cleanup_session(session_id):
    """
    Clean up session files after download
    URL: /api/convert/cleanup/<session_id>
    """
    try:
        print(f"\n🗑️ Cleanup request for session: {session_id}")
        
        upload_base = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        output_base = current_app.config.get('OUTPUT_FOLDER', 'outputs')
        
        upload_dir = Path(upload_base) / session_id
        output_dir = Path(output_base) / session_id
        
        # Remove directories
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
            print(f"✅ Removed upload directory: {upload_dir}")
        
        if output_dir.exists():
            shutil.rmtree(output_dir)
            print(f"✅ Removed output directory: {output_dir}")
        
        return jsonify({
            'success': True,
            'message': 'Session cleaned up successfully'
        }), 200
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        
        return jsonify({
            'success': False,
            'error': f'Cleanup failed: {str(e)}'
        }), 500