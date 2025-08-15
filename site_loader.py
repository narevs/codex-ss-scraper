import json
from pathlib import Path
from typing import Any, Dict

def load_site_rules() -> Dict[str, Any]:
    """Load site rules from the sites.json file."""
    rules_path = Path(__file__).resolve().parent / "rules" / "sites.json"
    with rules_path.open(encoding="utf-8") as f:
        return json.load(f)


__all__ = ["load_site_rules"]
