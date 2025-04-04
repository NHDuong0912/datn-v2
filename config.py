import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = 'your-secure-secret-key'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:0912@localhost:5432/datn_v2'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'your-secure-jwt-key'
    CORS_HEADERS = 'Content-Type'
