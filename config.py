import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def _load_env_file():
    """Load key-value pairs from .env in BASE_DIR into os.environ if not already set."""
    env_file = BASE_DIR / '.env'
    if env_file.is_file():
        try:
            for line in env_file.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                os.environ.setdefault(key, val)
        except Exception:
            pass

_load_env_file()

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    INITIAL_TEACHER_PASSWORD = os.environ.get('INITIAL_TEACHER_PASSWORD', 'Teacher@123')
    ENFORCE_INITIAL_TEACHER_PASSWORD_ROTATION = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 28800  # 8 hours

    # Database
    DATABASE_PATH = BASE_DIR / 'kitaab_bank.db'
    SQLITE_TIMEOUT = 5.0  # seconds

    # File Storage
    UPLOAD_FOLDER = BASE_DIR / 'app' / 'static' / 'uploads' / 'books'
    QR_FOLDER = BASE_DIR / 'app' / 'static' / 'uploads' / 'qr'
    BACKUP_FOLDER = BASE_DIR / 'backups'
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024  # 3 MB max upload size

    # Rate Limiting (Configurable for shared school Wi-Fi / NAT)
    # Default values permit concurrent classroom batches without false-positive blocks
    RATE_LIMIT_DONATE_PER_HOUR = int(os.environ.get('RATE_LIMIT_DONATE_PER_HOUR', 120))
    RATE_LIMIT_REQUEST_PER_HOUR = int(os.environ.get('RATE_LIMIT_REQUEST_PER_HOUR', 120))
    RATE_LIMIT_TRACK_PER_MINUTE = int(os.environ.get('RATE_LIMIT_TRACK_PER_MINUTE', 30))
    RATE_LIMIT_LOGIN_FAILURES = int(os.environ.get('RATE_LIMIT_LOGIN_FAILURES', 5))
    RATE_LIMIT_LOGIN_WINDOW_SECONDS = int(os.environ.get('RATE_LIMIT_LOGIN_WINDOW_SECONDS', 900))
    # Trust X-Forwarded-For only when the immediate peer is explicitly listed here.
    TRUSTED_PROXY_IPS = tuple(ip.strip() for ip in os.environ.get('TRUSTED_PROXY_IPS', '').split(',') if ip.strip())

    # School Info Defaults
    SCHOOL_NAME = os.environ.get('SCHOOL_NAME', 'Government High School')
    APP_NAME = 'Kitaab Bank'
    APP_TAGLINE = 'Smart School Book Exchange'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(DevelopmentConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    # Test fixtures use the public bootstrap credential for legacy route tests.
    # The dedicated security regression enables this policy explicitly.
    ENFORCE_INITIAL_TEACHER_PASSWORD_ROTATION = False

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig
}
