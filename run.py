#!/usr/bin/env python
"""
Cargo - Bulk Content & PDF Generator
Startup script
"""

import sys
import os

# Add project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║         Cargo — Bulk Content & PDF Generator             ║
    ║                                                           ║
    ║  🚀 Starting application...                              ║
    ║  🌐 Open http://localhost:5000 in your browser           ║
    ║                                                           ║
    ║  Press CTRL+C to stop                                    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
