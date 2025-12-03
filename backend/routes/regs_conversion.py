"""
API routes for .regs to PDF conversion
"""
import os
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from services.regs_pdf_converter import RegsToPDFConverter
import uuid
from pathlib import Path
import traceback

regs_bp = Blueprint('regs', __name__)

ALLOWED_EXTENSIONS = {'regs', 'xml'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@regs_bp.route('/convert', methods=['POST'])
def convert_regs_to_pdf():
    """
    Convert .regs file to PDF
    
    Expects:
        - file: .regs file upload
        
    Returns:
        JSON with conversion status and download URL
    """
    try:
        print("\n" + "="*60)
        print("🔄 Starting REGS to PDF conversion")
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
                'message': 'Invalid file type. Only .regs and .xml files are allowed'
            }), 400
        
        print(f"📄 File received: {file.filename}")
        
        # Get config folders (use app config for consistency)
        upload_base = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        output_base = current_app.config.get('OUTPUT_FOLDER', 'outputs')
        
        # Ensure base folders exist
        os.makedirs(upload_base, exist_ok=True)
        os.makedirs(output_base, exist_ok=True)
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        original_name = secure_filename(file.filename)
        name_without_ext = original_name.rsplit('.', 1)[0]
        
        print(f"🆔 Unique ID: {unique_id}")
        
        # Save uploaded file
        input_filename = f"{name_without_ext}_{unique_id}.{original_name.rsplit('.', 1)[1]}"
        input_path = os.path.join(upload_base, input_filename)
        
        print(f"💾 Saving file to: {input_path}")
        file.save(input_path)
        
        if not os.path.exists(input_path):
            raise Exception(f"Failed to save file: {input_path}")
        
        print(f"✅ File saved successfully")
        
        # Generate output filename
        output_filename = f"{name_without_ext}_{unique_id}.pdf"
        output_path = os.path.join(output_base, output_filename)
        
        print(f"📝 Output will be: {output_path}")
        
        # Convert .regs to PDF
        print("🔄 Starting conversion...")
        converter = RegsToPDFConverter()
        result = converter.convert(input_path, output_path)
        
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
        print("✅ REGS to PDF conversion completed successfully")
        print(f"📄 Output file: {output_filename}")
        print("="*60 + "\n")
        
        return jsonify({
            'status': 'success',
            'message': result['message'],
            'register_count': result.get('register_count', 0),
            'output_filename': output_filename,
            'download_url': f'/api/regs/download/{output_filename}'
        }), 200
        
    except Exception as e:
        print("="*60)
        print(f"❌ Exception in convert_regs_to_pdf:")
        print(traceback.format_exc())
        print("="*60 + "\n")
        
        return jsonify({
            'status': 'error',
            'message': f'Conversion failed: {str(e)}'
        }), 500


@regs_bp.route('/download/<filename>', methods=['GET'])
def download_pdf(filename):
    """
    Download converted PDF file
    
    Args:
        filename: Name of the PDF file to download
        
    Returns:
        PDF file download
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
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
        # Optional: Schedule cleanup after download
        # You can uncomment this if you want to auto-delete after download
        # @response.call_on_close
        # def cleanup():
        #     try:
        #         os.remove(file_path)
        #         print(f"🗑️ Cleaned up PDF file: {file_path}")
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


@regs_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'regs-to-pdf'
    }), 200