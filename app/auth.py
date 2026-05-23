"""
app/auth.py
-----------
Handles first-run setup and all subsequent login checks.

Security choices
~~~~~~~~~~~~~~~~
* Passwords are hashed with Argon2id (via the `argon2-cffi` package).
  If argon2-cffi is unavailable, falls back to bcrypt.
* The raw password is NEVER stored anywhere on disk.
* The Argon2id / bcrypt hash is stored in  APP_DATA_DIR/credentials.json.
* The same password is also used to derive a 32-byte key for the
  encrypted SQLite database (see sqlite_storage.py).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Optional

# ── Password hashing backend (Argon2id preferred, bcrypt fallback) ──────────
try:
    from argon2 import PasswordHasher as _Argon2PasswordHasher
    from argon2.exceptions import VerifyMismatchError as _VerifyMismatchError

    _HASHER = _Argon2PasswordHasher()

    def hash_password(password: str) -> str:
        return _HASHER.hash(password)

    def verify_password(stored_hash: str, password: str) -> bool:
        try:
            return _HASHER.verify(stored_hash, password)
        except _VerifyMismatchError:
            return False

    HASH_BACKEND = "argon2id"

except ImportError:
    try:
        import bcrypt as _bcrypt

        def hash_password(password: str) -> str:  # type: ignore[misc]
            return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()

        def verify_password(stored_hash: str, password: str) -> bool:  # type: ignore[misc]
            return _bcrypt.checkpw(password.encode(), stored_hash.encode())

        HASH_BACKEND = "bcrypt"

    except ImportError:
        raise RuntimeError(
            "Neither argon2-cffi nor bcrypt is installed. "
            "Install one: pip install argon2-cffi   or   pip install bcrypt"
        )


def derive_db_key(password: str, salt_hex: str) -> str:
    """
    Derive a 32-byte hex key from the user's password + a stored salt.
    Used as the SQLCipher PRAGMA key.
    The salt is stored in credentials.json; it is NOT secret by itself.
    """
    salt = bytes.fromhex(salt_hex)
    key = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
    return key.hex()


# ── Credentials file helpers ────────────────────────────────────────────────

class AuthManager:
    """
    Manages reading/writing the credentials.json stored in APP_DATA_DIR.
    """

    def __init__(self, credentials_file: Path, setup_marker: Path):
        self._creds_file = credentials_file
        self._setup_marker = setup_marker

    # ── Public API ──────────────────────────────────────────────────────────

    def is_first_run(self) -> bool:
        """Returns True if no setup has been completed at this install location."""
        return not self._setup_marker.exists() or not self._creds_file.exists()

    def setup(self, username: str, password: str) -> str:
        """
        Called once during the first-run wizard.
        Creates credentials.json and the setup marker.
        Returns the derived DB key (hex string) to open / create the encrypted DB.
        """
        if not username or not password:
            raise ValueError("Username and password must not be empty.")

        salt_hex = os.urandom(32).hex()
        creds = {
            "username": username,
            "password_hash": hash_password(password),
            "salt_hex": salt_hex,
            "hash_backend": HASH_BACKEND,
        }
        self._creds_file.write_text(json.dumps(creds, indent=2))
        self._setup_marker.touch()
        return derive_db_key(password, salt_hex)

    def login(self, password: str) -> Optional[str]:
        """
        Verify password against stored hash.
        Returns the derived DB key (hex string) on success, None on failure.
        """
        creds = self._load_creds()
        if not verify_password(creds["password_hash"], password):
            return None
        return derive_db_key(password, creds["salt_hex"])

    def get_username(self) -> str:
        """Return the stored username (safe to display)."""
        return self._load_creds().get("username", "")

    def wipe(self) -> None:
        """
        Delete all credential and marker files.
        Called during uninstall or stale-data cleanup on reinstall.
        """
        for path in (self._creds_file, self._setup_marker):
            if path.exists():
                path.unlink()

    # ── Private helpers ─────────────────────────────────────────────────────

    def _load_creds(self) -> dict:
        if not self._creds_file.exists():
            raise FileNotFoundError("Credentials file not found. Is this a first run?")
        return json.loads(self._creds_file.read_text())
