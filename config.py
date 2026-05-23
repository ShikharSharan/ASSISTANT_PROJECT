from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "assistant.db"  # for later (SQLite)

# Environment configuration
ENVIRONMENT = os.getenv('ASSISTANT_ENV', 'prod').lower()
if ENVIRONMENT not in ('dev', 'prod'):
    raise ValueError(f"Invalid ASSISTANT_ENV: {ENVIRONMENT}. Must be 'dev' or 'prod'.")

# Load environment variables
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

# Initialize UI theme based on environment
from app.ui_config import ThemeManager
ThemeManager.set_theme('dev' if ENVIRONMENT == 'dev' else 'prod')