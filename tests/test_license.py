import sys
from pathlib import Path
import base64
import json
import hashlib
from datetime import datetime, timedelta

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from auth.license import LicenseManager, LicenseError

# Small RSA key pair (for test only)
N = 3233
E = 17
D = 2753


def _create_license(email: str, exp: datetime) -> str:
    payload = {"email": email, "exp": exp.isoformat()}
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    h = int.from_bytes(hashlib.sha256(payload_b64.encode()).digest(), "big")
    sig = pow(h, D, N)
    signature = base64.urlsafe_b64encode(sig.to_bytes((N.bit_length() + 7) // 8, "big")).decode()
    return f"{payload_b64}.{signature}"


def test_license_verify_and_persist(tmp_path, monkeypatch):
    monkeypatch.setenv("PUBLIC_KEY_PEM", json.dumps({"n": N, "e": E}))
    monkeypatch.setenv("APPDATA", str(tmp_path))

    lm = LicenseManager()
    assert not lm.is_license_valid()

    license_key = _create_license("user@example.com", datetime.utcnow() + timedelta(days=1))
    lm.register("user@example.com", license_key)
    assert lm.is_license_valid()

    # simulate restart
    lm2 = LicenseManager()
    assert lm2.is_license_valid()

    # expired license rejected
    expired_key = _create_license("user@example.com", datetime.utcnow() - timedelta(days=1))
    with pytest.raises(LicenseError):
        lm2.register("user@example.com", expired_key)
