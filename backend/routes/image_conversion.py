"""
Image to SVG conversion routes - FIXED VERSION
"""
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import os
from pathlib import Path
from services.image_to_svg_converter import ImageToSVGConverter
from dotenv import load_dotenv

load_dotenv()

image_bp = Blueprint('image_conversion', __name__)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@image_bp.route('/image-to-svg', methods=['POST'])
def convert_image_to_svg():
    """
    Convert image to SVG
    Expects: multipart/form-data with 'file' and optional 'diagram_type'
    Returns: SVG file
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Get optional diagram type
        diagram_type = request.form.get('diagram_type', None)
        if diagram_type == 'auto':
            diagram_type = None  # Will trigger auto-detection
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        print(f"📁 File saved: {upload_path}")
        
        # Get Gemini API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': 'GEMINI_API_KEY not configured. Please set it in your .env file'
            }), 500
        
        # Initialize converter and process
        print("🤖 Initializing AI converter with optimized settings...")
        converter = ImageToSVGConverter(api_key)
        
        print(f"🔄 Converting image to SVG (type: {diagram_type or 'auto-detect'})...")
        
        # Inform user about quota-saving optimization
        if diagram_type:
            print(f"💡 User specified '{diagram_type}' - skipping auto-detection to save API quota")
        
        svg_content = converter.convert_to_svg(upload_path, diagram_type)
        
        # Save SVG file
        output_filename = f"{Path(filename).stem}_converted.svg"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        print(f"✅ SVG saved: {output_path}")
        
        # Clean up uploaded file
        try:
            os.remove(upload_path)
        except:
            pass
        
        # Return SVG file
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='image/svg+xml'
        )
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error: {error_msg}")
        
        # Clean up uploaded file on error
        try:
            if 'upload_path' in locals():
                os.remove(upload_path)
        except:
            pass
        
        # Handle specific error types
        if "429" in error_msg or "quota" in error_msg.lower() or "resource_exhausted" in error_msg.lower():
            return jsonify({
                'status': 'error',
                'message': 'API quota exceeded. Please try again in 1-2 minutes.',
                'error': error_msg,
                'suggestions': [
                    'Wait 1-2 minutes for quota to reset',
                    'Specify diagram type manually to reduce API calls',
                    'Create a new Google Cloud project with fresh API key',
                    'Enable billing for higher limits at https://aistudio.google.com/'
                ]
            }), 429
        
        if "timeout" in error_msg.lower():
            return jsonify({
                'status': 'error',
                'message': 'Request timed out. Please try again.',
                'error': error_msg
            }), 504
        
        # Generic error
        return jsonify({
            'status': 'error',
            'message': 'Conversion failed. Please try again.',
            'error': error_msg
        }), 500

@image_bp.route('/supported-formats', methods=['GET'])
def get_supported_formats():
    """Get list of supported image formats"""
    return jsonify({
        'status': 'success',
        'formats': list(ALLOWED_EXTENSIONS),
        'diagram_types': ['auto', 'flowchart', 'waveform', 'block_diagram', 'power_architecture'],
        'quota_tip': 'Specifying diagram type manually saves API quota by skipping auto-detection'
    })