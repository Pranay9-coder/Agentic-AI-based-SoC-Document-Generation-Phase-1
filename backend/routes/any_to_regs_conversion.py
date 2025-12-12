"""
API routes for ANY format to .regs conversion
File: backend/routes/any_to_regs_conversion.py
"""
import os
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from services.any_to_regs_converter import AnyToRegsConverter
import uuid
from pathlib import Path
import traceback

any_to_regs_bp = Blueprint('any_to_regs', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'xlsx', 'xls'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@any_to_regs_bp.route('/convert', methods=['POST'])
def convert_to_regs():
    """
    Convert PDF/Word/Excel file to .regs format
    
    Expects:
        - file: Document file upload (PDF, DOCX, DOC, XLSX, XLS)
        - device_name: Optional device name
        
    Returns:
        JSON with conversion status and download URL
    """
    try:
        print("\n" + "="*60)
        print("🔄 Starting ANY to REGS conversion")
        print("="*60)
        
        # Check if file is present
        if 'file' not in request.files:
            print("❌ Error: No file uploaded")
            return jsonify({
                'status': 'error',
                'message': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            print("❌ Error: No file selected")
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            print(f"❌ Error: Invalid file type: {file.filename}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid file type. Only PDF, Word (DOCX/DOC), and Excel (XLSX/XLS) files are allowed'
            }), 400
        
        print(f"📄 File received: {file.filename}")
        
        # Get optional device name from form data
        device_name = request.form.get('device_name', None)
        
        # Get config folders
        upload_base = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        output_base = current_app.config.get('OUTPUT_FOLDER', 'outputs')
        
        # Ensure base folders exist
        os.makedirs(upload_base, exist_ok=True)
        os.makedirs(output_base, exist_ok=True)
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        original_name = secure_filename(file.filename)
        name_without_ext = original_name.rsplit('.', 1)[0]
        file_ext = original_name.rsplit('.', 1)[1]
        
        print(f"🆔 Unique ID: {unique_id}")
        
        # Save uploaded file
        input_filename = f"{name_without_ext}_{unique_id}.{file_ext}"
        input_path = os.path.join(upload_base, input_filename)
        
        print(f"💾 Saving file to: {input_path}")
        file.save(input_path)
        
        if not os.path.exists(input_path):
            raise Exception(f"Failed to save file: {input_path}")
        
        print(f"✅ File saved successfully")
        
        # Generate output filename
        output_filename = f"{name_without_ext}_{unique_id}.regs"
        output_path = os.path.join(output_base, output_filename)
        
        print(f"📝 Output will be: {output_path}")
        
        # Get Gemini API key from environment
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        # Convert document to .regs
        print("🔄 Starting conversion...")
        converter = AnyToRegsConverter(gemini_api_key=gemini_api_key)
        result = converter.convert(input_path, output_path, device_name)
        
        print(f"📊 Conversion result: {result}")
        
        # Clean up input file
        try:
            os.remove(input_path)
            print(f"🗑️ Cleaned up input file: {input_path}")
        except Exception as e:
            print(f"⚠️ Could not clean up input file: {e}")
        
        if result['status'] == 'error':
            print("="*60)
            print(f"❌ Conversion failed: {result['message']}")
            print("="*60 + "\n")
            return jsonify(result), 500
        
        # Verify output file exists
        if not os.path.exists(output_path):
            raise Exception(f"Output file not created: {output_path}")
        
        print("="*60)
        print("✅ ANY to REGS conversion completed successfully")
        print(f"📄 Output file: {output_filename}")
        print("="*60 + "\n")
        
        return jsonify({
            'status': 'success',
            'message': result['message'],
            'device_name': result.get('device_name', 'Unknown'),
            'register_count': result.get('register_count', 0),
            'field_count': result.get('field_count', 0),
            'output_filename': output_filename,
            'download_url': f'/api/any-to-regs/download/{output_filename}'
        }), 200
        
    except Exception as e:
        print("="*60)
        print(f"❌ Exception in convert_to_regs:")
        print(traceback.format_exc())
        print("="*60 + "\n")
        
        return jsonify({
            'status': 'error',
            'message': f'Conversion failed: {str(e)}'
        }), 500


@any_to_regs_bp.route('/download/<filename>', methods=['GET'])
def download_regs(filename):
    """
    Download converted .regs file
    
    Args:
        filename: Name of the .regs file to download
        
    Returns:
        .regs file download
    """
    try:
        print(f"\n📦 Download request for: {filename}")
        
        # Use app config
        output_base = current_app.config.get('OUTPUT_FOLDER', 'outputs')
        file_path = os.path.join(output_base, filename)
        
        print(f"📁 Looking for file: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return jsonify({
                'status': 'error',
                'message': 'File not found'
            }), 404
        
        print(f"✅ Sending file: {filename}")
        
        # Send file
        response = send_file(
            file_path,
            mimetype='application/xml',
            as_attachment=True,
            download_name=filename
        )
        
        # Optional: Schedule cleanup after download
        # @response.call_on_close
        # def cleanup():
        #     try:
        #         os.remove(file_path)
        #         print(f"🗑️ Cleaned up .regs file: {file_path}")
        #     except:
        #         pass
        
        return response
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        print(traceback.format_exc())
        
        return jsonify({
            'status': 'error',
            'message': f'Download failed: {str(e)}'
        }), 500


@any_to_regs_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'any-to-regs',
        'supported_formats': ['pdf', 'docx', 'doc', 'xlsx', 'xls']
    }), 200


@any_to_regs_bp.route('/supported-formats', methods=['GET'])
def supported_formats():
    """Get list of supported file formats"""
    return jsonify({
        'formats': [
            {'extension': 'pdf', 'description': 'PDF Document'},
            {'extension': 'docx', 'description': 'Word Document (DOCX)'},
            {'extension': 'doc', 'description': 'Word Document (DOC)'},
            {'extension': 'xlsx', 'description': 'Excel Spreadsheet (XLSX)'},
            {'extension': 'xls', 'description': 'Excel Spreadsheet (XLS)'}
        ]
    }), 200