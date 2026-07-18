from dotenv import load_dotenv
load_dotenv()

import os

basedir = os.path.abspath(os.path.dirname(__file__))

# All the settings in this place, read from .env so my real keys never get commited to GitHub.
# The 'or' fallbacks keep the app running on a clone with no .env.
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'studyboard-dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'studyboard.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = 1800
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')