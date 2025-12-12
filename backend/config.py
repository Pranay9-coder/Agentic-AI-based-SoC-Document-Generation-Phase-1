"""
Configuration settings for Transform AI Suite
File: backend/config.py
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Use stable model with better free tier quotas
# gemini-1.5-flash: 15 RPM, 1M TPM, 1500 RPD (free tier)
# gemini-1.5-pro: 2 RPM, 32k TPM, 50 RPD (free tier)
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')

# AI Processing Settings
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
TEMPERATURE = float(os.getenv('TEMPERATURE', 0.1))
TOP_P = float(os.getenv('TOP_P', 0.95))
MAX_OUTPUT_TOKENS = int(os.getenv('MAX_OUTPUT_TOKENS', 8192))

# Safety Settings for Gemini
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# File Upload Settings
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    'pdf': ['.pdf'],
    'word': ['.docx', '.doc'],
    'excel': ['.xlsx', '.xls'],
    'regs': ['.regs', '.xml'],
    'image': ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
}

# Folder Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')

# Flask Settings
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
PORT = int(os.getenv('PORT', 5000))
DEBUG = FLASK_ENV == 'development'

# CORS Settings
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')