"""
Django settings for trading_platform project.
"""

import os
from pathlib import Path
import warnings

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
try:
    from config.secrets import DJANGO_SECRET_KEY
    SECRET_KEY = DJANGO_SECRET_KEY
except ImportError:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-your-secret-key-here-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '*.ngrok.io', '.ngrok-free.app']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'core',
    'angel_api',
    'portfolio',
    'trading',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'trading_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'trading_platform.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow unauthenticated access for development
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Angel One API settings
try:
    from config.secrets import API_KEY, CLIENT_CODE, TOTP_SECRET, SECRET_KEY as ANGEL_SECRET_KEY
    ANGEL_CLIENT_ID = CLIENT_CODE
    ANGEL_CLIENT_SECRET = ANGEL_SECRET_KEY
    ANGEL_TOTP_SECRET = TOTP_SECRET
    ANGEL_API_KEY = API_KEY
except ImportError:
    ANGEL_CLIENT_ID = os.environ.get('ANGEL_CLIENT_ID', 'xhMChjlS')
    ANGEL_CLIENT_SECRET = os.environ.get('ANGEL_CLIENT_SECRET', '78e4798a-f35b-481f-9804-ff78557f99ed')
    ANGEL_TOTP_SECRET = os.environ.get('ANGEL_TOTP_SECRET', '')
    ANGEL_API_KEY = os.environ.get('ANGEL_API_KEY', '')

ANGEL_PASSWORD = os.environ.get('ANGEL_PASSWORD', '')

# Angel One OAuth Configuration
ANGEL_ONE_CONFIG = {
    'CLIENT_ID': ANGEL_CLIENT_ID,
    'CLIENT_SECRET': ANGEL_CLIENT_SECRET,
    'PASSWORD': ANGEL_PASSWORD,
    'TOTP_SECRET': ANGEL_TOTP_SECRET,
    'REDIRECT_URI': 'http://localhost:8000/api/angel/auth/callback/',
    'BASE_URL': 'https://apiconnect.angelbroking.com',
    'AUTH_URL': 'https://smartapi.angelbroking.com/publisher-login',
}

# Ngrok Configuration 
try:
    from config.secrets import NGROK_AUTH_TOKEN as CONFIG_NGROK_TOKEN
    NGROK_AUTH_TOKEN = CONFIG_NGROK_TOKEN
except ImportError:
    NGROK_AUTH_TOKEN = os.environ.get('NGROK_AUTH_TOKEN', '')

NGROK_ENABLED = os.environ.get('NGROK_ENABLED', 'False').lower() == 'true'

# Ngrok Auto-Start Configuration
NGROK_AUTO_START = os.environ.get('NGROK_AUTO_START', 'True').lower() == 'true'

# Auto-start ngrok for development
if DEBUG and NGROK_AUTO_START:
    try:
        import ngrok_auto  # This will auto-start ngrok
    except ImportError:
        pass

# Together AI API settings
try:
    from config.secrets import TOGETHER_API_KEY as CONFIG_TOGETHER_KEY
    TOGETHER_API_KEY = CONFIG_TOGETHER_KEY
except ImportError:
    TOGETHER_API_KEY = os.environ.get('TOGETHER_API_KEY', '9c31ba668fcab4996d94aec803f87bab9d7056ade551995dc9e986a6a77e7bee')

# LLM Configuration for trading analysis
LLM_CONFIG = {
    'API_KEY': TOGETHER_API_KEY,
    'MODEL': 'deepseek-ai/DeepSeek-V3',
    'MAX_TOKENS': 500,
    'TEMPERATURE': 0.3
}

# Trading settings
DEFAULT_RISK_PERCENTAGE = 2.0  # 2% risk per trade
MAX_POSITIONS_PER_STRATEGY = 10
TRADING_ENABLED = True

# Small Cap Trading Strategy Settings
SMALL_CAP_CONFIG = {
    'MIN_PRICE': 75,  # Updated to 75 INR as per requirement
    'MAX_PRICE': 150,  # Updated to 150 INR as per requirement
    'MAX_MARKET_CAP': 5000_000_000_000,  # 5000 crores
    'MIN_VOLUME': 50000,
    'PRICE_CHANGE_THRESHOLD': 2.0,  # ±2 rupees
    'MAX_INVESTMENT_PER_STOCK': 5000,
    'MIN_AI_CONFIDENCE': 60,
    'TRADING_INTERVAL_MINUTES': 30,
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'trading.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
}

# Suppress harmless third-party warnings

# Filter out specific warnings that don't affect functionality
warnings.filterwarnings('ignore', message='Field "model_id" in BatchJob has conflict with protected namespace "model_"')
warnings.filterwarnings('ignore', message='max_value should be an integer or Decimal instance')
warnings.filterwarnings('ignore', message='min_value should be an integer or Decimal instance')
warnings.filterwarnings('ignore', message='This is a development server')  # Suppress dev server warning
