#!/usr/bin/env python3
"""
TRUSTMEBRO - Parody Research Paper Generator
Run with: python run.py
"""

import os
import sys

# Add the project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Create app instance (used by gunicorn in production)
app = create_app()

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print("\n" + "="*60)
    print("🎓 TRUSTMEBRO - Journal of Unverified Claims")
    print("="*60)
    print("PARODY / FICTIONAL RESEARCH — DO NOT CITE AS REAL")
    print("="*60)
    print(f"\n🌐 Server running at: http://{host}:{port}")
    print(f"📁 Database: instance/trustmebro.db")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(debug=debug, host=host, port=port)
