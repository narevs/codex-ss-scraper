import base64
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

CONFIG_DIRNAME = "SSScraper"
CONFIG_FILENAME = "config.json"


class LicenseError(Exception):
    """Raised when license verification fails."""


@dataclass
class LicenseInfo:
    email: str
    expires_at: datetime
    raw: str

    def to_dict(self) -> dict:
        return {
            "email": self.email,
            "license": self.raw,
            "expires_at": self.expires_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LicenseInfo":
        return cls(
            email=data["email"],
            raw=data.get("license", ""),
            expires_at=datetime.fromisoformat(data["expires_at"]),
        )


def _default_config_path() -> Path:
    appdata = os.getenv("APPDATA") or os.path.join(Path.home(), ".config")
    return Path(appdata) / CONFIG_DIRNAME / CONFIG_FILENAME


def should_show_license_modal(config_path: Path) -> bool:
    """Return True when the license dialog should be shown.

    The modal is required on first run or when the persisted license has
    expired.  A missing or malformed config file is treated as needing the
    modal as well.
    """
    lm = LicenseManager(config_path)
    return not lm.is_license_valid()


def load_public_key(pem: Optional[str] = None) -> Tuple[int, int]:
    """Load RSA public key numbers (n, e).

    The key is expected to be provided as JSON {"n": int, "e": int} either via
    the `PUBLIC_KEY_PEM` environment variable or a file at `keys/public_key.pem`.
    """
    if pem is None:
        pem = os.getenv("PUBLIC_KEY_PEM")
    if pem:
        data = json.loads(pem)
        return int(data["n"]), int(data["e"])
    path = Path("keys/public_key.pem")
    if path.exists():
        data = json.loads(path.read_text())
        return int(data["n"]), int(data["e"])
    raise FileNotFoundError("Public key not found")


def _rsa_verify(message: bytes, signature: bytes, n: int, e: int) -> bool:
    h = int.from_bytes(hashlib.sha256(message).digest(), "big")
    sig = int.from_bytes(signature, "big")
    return pow(sig, e, n) == h % n


def verify_license(email: str, license_key: str, public_key_pem: Optional[str] = None) -> LicenseInfo:
    """Verify a license key and return LicenseInfo if valid."""
    try:
        payload_b64, sig_b64 = license_key.split(".")
    except ValueError as exc:
        raise LicenseError("Invalid license format") from exc

    payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode()
    payload = json.loads(payload_json)

    if payload.get("email") != email:
        raise LicenseError("License email mismatch")

    expires_at = datetime.fromisoformat(payload["exp"])
    if datetime.utcnow() > expires_at:
        raise LicenseError("License expired")

    n, e = load_public_key(public_key_pem)
    signature = base64.urlsafe_b64decode(sig_b64.encode())
    if not _rsa_verify(payload_b64.encode(), signature, n, e):
        raise LicenseError("Bad signature")

    return LicenseInfo(email=email, expires_at=expires_at, raw=license_key)


class LicenseManager:
    """Handles storing and validating license information."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or _default_config_path()

    def is_license_valid(self) -> bool:
        info = self.load()
        if not info:
            return False
        return info.expires_at >= datetime.utcnow()

    def load(self) -> Optional[LicenseInfo]:
        if not self.config_path.exists():
            return None
        try:
            data = json.loads(self.config_path.read_text())
            return LicenseInfo.from_dict(data)
        except Exception:
            return None

    def save(self, info: LicenseInfo) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(info.to_dict()))

    def register(self, email: str, license_key: str, public_key_pem: Optional[str] = None) -> LicenseInfo:
        info = verify_license(email, license_key, public_key_pem=public_key_pem)
        self.save(info)
        return info
