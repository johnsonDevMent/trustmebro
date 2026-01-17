#!/usr/bin/env python3
"""
TRUSTMEBRO - Parody Research Paper Generator
Run with: python run.py (development)
Production: gunicorn run:app (via Procfile)
"""

import os
import sys

# Add the project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Create app instance (used by gunicorn in production)
# This is the WSGI application
app = create_app()

# Only run dev server if this file is executed directly (not imported by gunicorn)
if __name__ == '__main__':
    # Get port from environment (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    
    # In production (when PORT is set by Render), bind to 0.0.0.0
    # Otherwise use 127.0.0.1 for local development
    if os.environ.get('PORT'):
        host = '0.0.0.0'  # Required for Render/external access
        debug = False  # Never use debug mode when PORT is set (production)
    else:
        host = os.environ.get('HOST', '127.0.0.1')
        debug = os.environ.get('FLASK_ENV') != 'production'
    
    print("\n" + "="*60)
    print("🎓 TRUSTMEBRO - Journal of Unverified Claims")
    print("="*60)
    print("PARODY / FICTIONAL RESEARCH — DO NOT CITE AS REAL")
    print("="*60)
    print(f"\n🌐 Server running at: http://{host}:{port}")
    print(f"📁 Database: instance/trustmebro.db")
    if debug:
        print("⚠️  Running in DEBUG mode (development only)")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(debug=debug, host=host, port=port, use_reloader=False)
