"""Card skeletons and file writing shared by the onboarding steps."""
import datetime
import json
import os

SCHEMA_VERSION = "0.1"


def now_iso(now=None):
    """An ISO-8601 UTC timestamp; `now` overrides it for reproducible runs."""
    if now:
        return now
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def date_of(iso):
    return iso[:10]


def skeleton(card, card_id, seat, created_at, status="draft", revision=1):
    """The common fields every card carries (contracts/schemas/common.schema.json)."""
    return {
        "card": card,
        "schema_version": SCHEMA_VERSION,
        "id": card_id,
        "revision": revision,
        "author": seat,
        "created_at": created_at,
        "numbers": [],
        "assumptions": [],
        "kb_refs": [],
        "kb_gaps": [],
        "case_refs": [],
        "case_gaps": [],
        "degraded": [],
        "status": status,
    }


def write_json(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_text(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
