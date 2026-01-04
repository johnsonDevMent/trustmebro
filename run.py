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

if __name__ == '__main__':
    app = create_app()
    
    print("\n" + "="*60)
    print("🎓 TRUSTMEBRO - Journal of Unverified Claims")
    print("="*60)
    print("PARODY / FICTIONAL RESEARCH — DO NOT CITE AS REAL")
    print("="*60)
    print(f"\n🌐 Server running at: http://127.0.0.1:5000")
    print(f"📁 Database: instance/trustmebro.db")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
