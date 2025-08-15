import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from auth.license import should_show_license_modal


def test_should_show_license_modal_first_run(tmp_path):
    config = tmp_path / "config.json"
    assert should_show_license_modal(config)

    # expired config
    past = datetime.utcnow() - timedelta(days=1)
    config.write_text(json.dumps({
        "email": "a", "license": "b", "expires_at": past.isoformat()
    }))
    assert should_show_license_modal(config)


def test_should_show_license_modal_valid_config(tmp_path):
    config = tmp_path / "config.json"
    future = datetime.utcnow() + timedelta(days=1)
    config.write_text(json.dumps({
        "email": "a", "license": "b", "expires_at": future.isoformat()
    }))
    assert not should_show_license_modal(config)

