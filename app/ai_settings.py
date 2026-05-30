from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from config import APP_DATA_DIR, GROQ_API_KEY


SUPPORTED_PROVIDERS = ("Groq",)
DEFAULT_PROVIDER = "Groq"
DEFAULT_MODEL = "llama-3.1-8b-instant"
SETTINGS_FILE: Path = APP_DATA_DIR / "ai_settings.json"


@dataclass
class AISettings:
    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL
    api_key: str = ""


def _normalize_settings(data: dict | None = None) -> AISettings:
    data = data or {}
    provider = str(data.get("provider") or DEFAULT_PROVIDER).strip()
    if provider not in SUPPORTED_PROVIDERS:
        provider = DEFAULT_PROVIDER

    model = str(data.get("model") or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    api_key = str(data.get("api_key") or GROQ_API_KEY or "").strip()
    return AISettings(provider=provider, model=model, api_key=api_key)


def load_ai_settings() -> AISettings:
    if not SETTINGS_FILE.exists():
        return _normalize_settings()

    try:
        return _normalize_settings(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return _normalize_settings()


def save_ai_settings(settings: AISettings) -> AISettings:
    normalized = _normalize_settings(asdict(settings))
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(asdict(normalized), indent=2),
        encoding="utf-8",
    )
    return normalized
