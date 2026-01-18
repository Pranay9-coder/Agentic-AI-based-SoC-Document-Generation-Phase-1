"""
Flask application for document conversion services
File: backend/app.py - UPDATED WITH SPEC-TO-PDF
"""
from flask import Flask, jsonify
from flask_cors import CORS
from routes.conversion import conversion_bp
from routes.regs_conversion import regs_bp
from routes.image_conversion import image_bp
from routes.history import history_bp
from routes.any_to_regs_conversion import any_to_regs_bp
from routes.multi_ip_conversion import multi_ip_bp
from routes.spec_source_editor import spec_editor_bp
from routes.spec_to_pdf_conversion import spec_to_pdf_bp  # ✅ NEW
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ===== CRITICAL: Configure folders =====
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BACKEND_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BACKEND_DIR, 'outputs')
SPEC_OUTPUTS_FOLDER = os.path.join(BACKEND_DIR, 'spec_outputs')

# ===== Configure for handling longer requests =====
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching

# Set Flask config
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['SPEC_OUTPUTS_FOLDER'] = SPEC_OUTPUTS_FOLDER

# Create required directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(SPEC_OUTPUTS_FOLDER, exist_ok=True)

print(f"📁 Upload folder: {UPLOAD_FOLDER}")
print(f"📁 Output folder: {OUTPUT_FOLDER}")
print(f"📁 Spec outputs folder: {SPEC_OUTPUTS_FOLDER}")

# ===== Configure CORS =====
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000", "*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

# Register blueprints
app.register_blueprint(conversion_bp, url_prefix='/api/convert')
app.register_blueprint(image_bp, url_prefix='/api/convert')
app.register_blueprint(regs_bp, url_prefix='/api/regs')
app.register_blueprint(history_bp, url_prefix='/api/history')
app.register_blueprint(any_to_regs_bp, url_prefix='/api/any-to-regs')
app.register_blueprint(multi_ip_bp, url_prefix='/api/multi-ip')
app.register_blueprint(spec_editor_bp, url_prefix='/api/spec-editor')
app.register_blueprint(spec_to_pdf_bp, url_prefix='/api/spec-to-pdf')  # ✅ NEW

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Transform AI Suite Backend API',
        'version': '1.0',
        'endpoints': {
            'dita_conversion': '/api/convert',
            'regs_to_pdf': '/api/regs',
            'any_to_regs': '/api/any-to-regs',
            'multi_ip_doc_gen': '/api/multi-ip',
            'spec_to_pdf': '/api/spec-to-pdf',  # ✅ NEW
            'image_to_svg': '/api/convert/image-to-svg',
            'history': '/api/history'
        },
        'config': {
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'output_folder': app.config['OUTPUT_FOLDER'],
            'spec_outputs_folder': app.config['SPEC_OUTPUTS_FOLDER'],
            'max_content_length': f"{app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024):.0f}MB"
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    upload_exists = os.path.exists(app.config['UPLOAD_FOLDER'])
    output_exists = os.path.exists(app.config['OUTPUT_FOLDER'])
    spec_exists = os.path.exists(app.config['SPEC_OUTPUTS_FOLDER'])
    
    return jsonify({
        'status': 'healthy',
        'services': {
            'dita_conversion': 'available',
            'regs_to_pdf': 'available',
            'any_to_regs': 'available',
            'multi_ip_doc_gen': 'available',
            'spec_to_pdf': 'available',  # ✅ NEW
            'image_to_svg': 'available',
            'history': 'available'
        },
        'folders': {
            'uploads': 'ok' if upload_exists else 'missing',
            'outputs': 'ok' if output_exists else 'missing',
            'spec_outputs': 'ok' if spec_exists else 'missing'
        }
    }), 200

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"\n{'='*60}")
    print(f"🚀 Transform AI Suite Backend Starting...")
    print(f"{'='*60}")
    print(f"📡 Server: http://localhost:{port}")
    print(f"🔧 Debug: {debug}")
    print(f"\n📂 Directories:")
    print(f"  • Uploads: {UPLOAD_FOLDER}")
    print(f"  • Outputs: {OUTPUT_FOLDER}")
    print(f"  • Spec Outputs: {SPEC_OUTPUTS_FOLDER}")
    print(f"\n🔌 Services:")
    print(f"  • DITA: /api/convert")
    print(f"  • REGS→PDF: /api/regs")
    print(f"  • ANY→REGS: /api/any-to-regs")
    print(f"  • Multi-IP: /api/multi-ip")
    print(f"  • Spec→PDF: /api/spec-to-pdf")  # ✅ NEW
    print(f"  • Image→SVG: /api/convert/image-to-svg")
    print(f"  • History: /api/history")
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)