import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def save(key: str, payload) -> None:
    record = {
        "guncellenme_zamani": datetime.now(timezone.utc).isoformat(),
        "veri": payload,
    }
    path = DATA_DIR / f"{key}.json"
    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def load(key: str):
    path = DATA_DIR / f"{key}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
