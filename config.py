from pathlib import Path
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file (only used for API keys in dev)
load_dotenv()

# ── Source / Repo root (never store data here) ─────────────────────────────
BASE_DIR = Path(__file__).parent

# ── App-owned data directory (outside the repo on real installs) ───────────
# On macOS/Linux: ~/Library/Application Support/AssistantApp  or  ~/.local/share/AssistantApp
# On Windows    : %APPDATA%\AssistantApp
# During dev    : PROJECT_ROOT/app_data  (override with APP_DATA_DIR env var)
def _resolve_app_data_dir() -> Path:
    override = os.getenv("APP_DATA_DIR")
    if override:
        return Path(override)
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "AssistantApp"
    if sys.platform == "win32":
        appdata = os.getenv("APPDATA", str(Path.home()))
        return Path(appdata) / "AssistantApp"
    return Path.home() / ".local" / "share" / "AssistantApp"

APP_DATA_DIR: Path = _resolve_app_data_dir()
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Encrypted database lives inside the app data dir
DB_PATH = APP_DATA_DIR / "assistant.db"

# Setup marker — written after first-run wizard completes
SETUP_MARKER = APP_DATA_DIR / ".setup_complete"

# Credential store (stores username + Argon2id hash of password)
CREDENTIALS_FILE = APP_DATA_DIR / "credentials.json"

# ── Environment / API config ────────────────────────────────────────────────
ENVIRONMENT = os.getenv("ASSISTANT_ENV", "prod").lower()
if ENVIRONMENT not in ("dev", "prod"):
    raise ValueError(f"Invalid ASSISTANT_ENV: {ENVIRONMENT}. Must be 'dev' or 'prod'.")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── UI theme ─────────────────────────────────────────────────────────────────
from app.ui_config import ThemeManager
ThemeManager.set_theme("dev" if ENVIRONMENT == "dev" else "prod")
