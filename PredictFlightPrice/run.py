#!/usr/bin/env python
"""
Flight Price Prediction - Flask App Launcher
Supports HTTP and HTTPS modes
"""

import sys
import os
from app import app

def run_https():
    """Run Flask app with HTTPS (SSL/TLS)"""
    print("\n" + "="*70)
    print("🔒 FLIGHT PRICE PREDICTION - HTTPS MODE")
    print("="*70)
    print()
    print("✓ SSL/TLS Security Enabled")
    print("✓ Certificates:      cert.pem, key.pem")
    print("✓ Server:            https://0.0.0.0:8000")
    print("✓ Local Access:      https://localhost:8000")
    print()
    print("⚠️  Browser Warning: You may see a certificate warning.")
    print("   This is expected because it's a self-signed certificate.")
    print("   Proceed anyway to access the application.")
    print()
    print("="*70 + "\n")
    
    ssl_context = ('cert.pem', 'key.pem')
    app.run(debug=True, host="0.0.0.0", port=8000, ssl_context=ssl_context)

def run_http():
    """Run Flask app with HTTP (unencrypted)"""
    print("\n" + "="*70)
    print("🌐 FLIGHT PRICE PREDICTION - HTTP MODE (Unencrypted)")
    print("="*70)
    print()
    print("⚠️  WARNING: Running without SSL/TLS encryption!")
    print()
    print("✓ Server:            http://0.0.0.0:8000")
    print("✓ Local Access:      http://localhost:8000")
    print()
    print("="*70 + "\n")
    
    app.run(debug=True, host="0.0.0.0", port=8000)

def run_production_https():
    """Run Flask app with Gunicorn and HTTPS"""
    print("\n" + "="*70)
    print("🚀 FLIGHT PRICE PREDICTION - PRODUCTION (Gunicorn + HTTPS)")
    print("="*70)
    print()
    print("Starting production server with Gunicorn...")
    print()
    print("✓ Server:            https://0.0.0.0:8000")
    print("✓ Workers:           4")
    print("✓ Encryption:        SSL/TLS")
    print()
    print("Run this command:")
    print("gunicorn --certfile=cert.pem --keyfile=key.pem --workers 4 --bind 0.0.0.0:8000 app:app")
    print()
    print("="*70 + "\n")
    
    os.system("gunicorn --certfile=cert.pem --keyfile=key.pem --workers 4 --bind 0.0.0.0:8000 app:app")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == 'http':
            run_http()
        elif mode == 'https':
            run_https()
        elif mode == 'prod':
            run_production_https()
        else:
            print("Usage: python run.py [mode]")
            print("\nModes:")
            print("  https      - Run with HTTPS/SSL (recommended)")
            print("  http       - Run with HTTP (unencrypted)")
            print("  prod       - Run with Gunicorn + HTTPS (production)")
            print("\nDefault: HTTPS mode")
            run_https()
    else:
        # Default to HTTPS
        run_https()
