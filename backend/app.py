"""
Flask application for document conversion services
File: backend/app.py
"""
from flask import Flask, jsonify
from flask_cors import CORS
from routes.conversion import conversion_bp
from routes.regs_conversion import regs_bp
from routes.image_conversion import image_bp
from routes.history import history_bp
from routes.any_to_regs_conversion import any_to_regs_bp  # NEW: Import any-to-regs blueprint
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ===== CRITICAL: Configure upload/output folders =====
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')

# Set Flask config
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Create required directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

print(f"📁 Upload folder: {UPLOAD_FOLDER}")
print(f"📁 Output folder: {OUTPUT_FOLDER}")

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Register blueprints
app.register_blueprint(conversion_bp, url_prefix='/api/convert')
app.register_blueprint(image_bp, url_prefix='/api/convert')
app.register_blueprint(regs_bp, url_prefix='/api/regs')
app.register_blueprint(history_bp, url_prefix='/api/history')
app.register_blueprint(any_to_regs_bp, url_prefix='/api/any-to-regs')  # NEW: Register any-to-regs blueprint

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
            'any_to_regs': '/api/any-to-regs',  # NEW
            'image_to_svg': '/api/convert/image-to-svg',
            'history': '/api/history'
        },
        'config': {
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'output_folder': app.config['OUTPUT_FOLDER']
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    # Check if folders exist
    upload_exists = os.path.exists(app.config['UPLOAD_FOLDER'])
    output_exists = os.path.exists(app.config['OUTPUT_FOLDER'])
    
    return jsonify({
        'status': 'healthy',
        'services': {
            'dita_conversion': 'available',
            'regs_to_pdf': 'available',
            'any_to_regs': 'available',  # NEW
            'image_to_svg': 'available',
            'history': 'available'
        },
        'folders': {
            'uploads': 'ok' if upload_exists else 'missing',
            'outputs': 'ok' if output_exists else 'missing'
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
    print(f"📡 Server running on: http://localhost:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"\n📂 Directories:")
    print(f"  • Uploads: {UPLOAD_FOLDER}")
    print(f"  • Outputs: {OUTPUT_FOLDER}")
    print(f"\n🔌 Available Services:")
    print(f"  • DITA Conversion: http://localhost:{port}/api/convert")
    print(f"  • REGS to PDF: http://localhost:{port}/api/regs")
    print(f"  • ANY to REGS: http://localhost:{port}/api/any-to-regs")  # NEW
    print(f"  • Image to SVG: http://localhost:{port}/api/convert/image-to-svg")
    print(f"  • History: http://localhost:{port}/api/history")
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)