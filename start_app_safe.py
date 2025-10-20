#!/usr/bin/env python3
"""
Script untuk menjalankan aplikasi Flask dengan error handling yang lebih baik
"""

import os
import sys
import logging
import traceback
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Cek environment variables yang diperlukan"""
    logger.info("🔍 Checking environment variables...")
    
    # Set default values jika tidak ada
    if not os.getenv('USE_ONNX_INFERENCE'):
        os.environ['USE_ONNX_INFERENCE'] = 'true'
        logger.info("✅ Set USE_ONNX_INFERENCE=true (default)")
    
    if not os.getenv('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'development'
        logger.info("✅ Set FLASK_ENV=development (default)")
    
    if not os.getenv('FLASK_DEBUG'):
        os.environ['FLASK_DEBUG'] = '1'
        logger.info("✅ Set FLASK_DEBUG=1 (default)")

def check_dependencies():
    """Cek dependencies yang diperlukan"""
    logger.info("📦 Checking dependencies...")
    
    try:
        import flask
        import sqlalchemy
        import onnxruntime
        import redis
        import cv2
        import numpy as np
        logger.info("✅ Core dependencies available")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.error("Please install requirements: pip install -r requirement.txt")
        return False

def check_database_connection():
    """Cek koneksi database"""
    logger.info("🗄️ Checking database connection...")
    
    try:
        from app import app, db
        with app.app_context():
            # Test database connection
            db.engine.connect()
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def check_models():
    """Cek model files"""
    logger.info("🤖 Checking AI models...")
    
    model_files = [
        'models/convertedmodels/emotion.onnx',
        'models/convertedmodels/arcface.onnx'
    ]
    
    missing_models = []
    for model_file in model_files:
        if not os.path.exists(model_file):
            missing_models.append(model_file)
    
    if missing_models:
        logger.warning(f"⚠️ Missing model files: {missing_models}")
        logger.warning("Application may not work properly without these models")
    else:
        logger.info("✅ All model files found")
    
    return len(missing_models) == 0

def run_application():
    """Jalankan aplikasi Flask"""
    logger.info("🚀 Starting Flask application...")
    
    try:
        from app import app, socketio
        
        # Check if eventlet is available for SocketIO
        try:
            import eventlet
            logger.info("✅ Eventlet available for SocketIO")
            use_eventlet = True
        except ImportError:
            logger.warning("⚠️ Eventlet not available, using polling only for SocketIO")
            use_eventlet = False
        
        if use_eventlet:
            # Run with eventlet for full SocketIO support
            logger.info("🌐 Starting with eventlet server...")
            socketio.run(
                app,
                host='0.0.0.0',
                port=5000,
                debug=True,
                use_reloader=False
            )
        else:
            # Run with polling only (no websocket upgrade)
            logger.info("🌐 Starting with polling-only SocketIO...")
            socketio.run(
                app,
                host='0.0.0.0',
                port=5000,
                debug=True,
                use_reloader=False,
                allow_unsafe_werkzeug=True
            )
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        logger.error(traceback.format_exc())
        return False
    
    return True

def main():
    """Main function"""
    logger.info("🎯 Starting EMONG Web Application (Safe Mode)")
    logger.info("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    logger.info(f"📁 Working directory: {os.getcwd()}")
    
    # Check environment
    check_environment()
    
    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Dependency check failed. Exiting.")
        sys.exit(1)
    
    # Check database
    if not check_database_connection():
        logger.error("❌ Database check failed. Exiting.")
        sys.exit(1)
    
    # Check models
    check_models()  # Non-critical, just warning
    
    # Run application
    logger.info("✅ All checks passed. Starting application...")
    logger.info("🌐 Application will be available at: http://localhost:5000")
    logger.info("🛑 Press Ctrl+C to stop the application")
    logger.info("=" * 50)
    
    if not run_application():
        logger.error("❌ Application failed to start")
        sys.exit(1)

if __name__ == "__main__":
    main()
