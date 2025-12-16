"""
Production server runner with Waitress - FIXES TIMEOUT ISSUES
File: backend/run_server.py

This fixes ERR_CONNECTION_RESET errors for long-running requests
by using Waitress with extended timeouts instead of Flask dev server.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import app AFTER loading env vars
from app import app

def main():
    """Run Flask app with Waitress for production-grade handling"""
    try:
        from waitress import serve
        
        port = int(os.getenv('PORT', 5000))
        host = os.getenv('HOST', '0.0.0.0')
        
        print("\n" + "="*60)
        print("🚀 Transform AI Suite - Production Server")
        print("="*60)
        print(f"📡 Server: http://{host}:{port}")
        print(f"🔧 Mode: Production (Waitress)")
        print(f"⏱️  Timeout: 600 seconds (10 minutes)")
        print(f"🧵 Threads: 8")
        print("\n📂 Directories:")
        print(f"  • Uploads: {app.config['UPLOAD_FOLDER']}")
        print(f"  • Outputs: {app.config['OUTPUT_FOLDER']}")
        print(f"  • Spec Outputs: {app.config['SPEC_OUTPUTS_FOLDER']}")
        print("\n🔌 Services:")
        print(f"  • DITA: /api/convert")
        print(f"  • REGS→PDF: /api/regs")
        print(f"  • ANY→REGS: /api/any-to-regs")
        print(f"  • Multi-IP: /api/multi-ip")
        print(f"  • Image→SVG: /api/convert/image-to-svg")
        print(f"  • History: /api/history")
        print("="*60 + "\n")
        print("✅ Server ready - Press Ctrl+C to stop\n")
        
        # Run with Waitress
        serve(
            app,
            host=host,
            port=port,
            threads=8,                      # 8 worker threads
            channel_timeout=600,            # 10 minutes for long conversions
            connection_limit=1000,          # Max connections
            recv_bytes=8192,                # Socket receive buffer
            send_bytes=18000,               # Socket send buffer (multiple of 9000)
            max_request_body_size=104857600,  # 100MB max request
            expose_tracebacks=False,        # Don't expose errors to clients
            clear_untrusted_proxy_headers=True,  # Security
            url_scheme='http'
        )
        
    except ImportError:
        print("\n❌ ERROR: Waitress not installed!")
        print("📦 Install it with: pip install waitress")
        print("\nAlternatively, you can still run with Flask dev server:")
        print("  python app.py")
        print("\nBut dev server may timeout on long requests.\n")
        return 1
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())