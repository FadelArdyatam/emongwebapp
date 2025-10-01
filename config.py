import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USERNAME = os.getenv('DB_USERNAME', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'emotion_detection_db')
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24 hours
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-super-secret-flask-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # API Configuration
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
    
    # Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Model paths (can be overridden via env)
    MODELS_BASE_DIR = os.getenv('MODELS_BASE_DIR', os.path.join(os.path.dirname(__file__), 'models'))
    MODELS_CONVERTED_DIR = os.getenv('MODELS_CONVERTED_DIR', os.path.join(MODELS_BASE_DIR, 'convertedmodels'))
    ARCFACE_MODEL_PATH = os.getenv('ARCFACE_MODEL_PATH', os.path.join(MODELS_CONVERTED_DIR, 'arcface.onnx'))
    EMOTION_MODEL_PATH = os.getenv('EMOTION_MODEL_PATH', os.path.join(MODELS_CONVERTED_DIR, 'emotion.onnx'))
    RETINAFACE_MNV2_PATH = os.getenv('RETINAFACE_MNV2_PATH', os.path.join(MODELS_CONVERTED_DIR, 'retinaface_mobilenet25.onnx'))
    RETINAFACE_RES50_PATH = os.getenv('RETINAFACE_RES50_PATH', os.path.join(MODELS_CONVERTED_DIR, 'retinaface_resnet50.onnx'))