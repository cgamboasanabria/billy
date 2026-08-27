"""Curation workflow: vision-proposed questions pending parent approval.

Each subject has a JSON file at ``assets/mapeos/nuevas/<subject>.json`` that
lists the proposed questions for that subject. When the parent approves a
proposal (in the Profe panel), the question moves into the live bundle via
``import_material()``. Until then it lives here for editing and review.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from Script.functions.config import MAPEOS_DIR

_NUEVAS_DIR = MAPEOS_DIR / "nuevas"


def _slug(name: str) -> str:
    return name.replace(" ", "_")


def _path_for(subject: str) -> Path:
    _NUEVAS_DIR.mkdir(parents=True, exist_ok=True)
    return _NUEVAS_DIR / f"{_slug(subject)}.json"


def load_pending_proposals(subject: str) -> dict[str, dict[str, Any]]:
    """Return {image_name: proposal_dict} for the subject, or {} if none."""
    path = _path_for(subject)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_proposal(subject: str, image_name: str, proposal: dict[str, Any]) -> Path:
    """Persist a vision-proposed question to the subject's curation file."""
    path = _path_for(subject)
    data = load_pending_proposals(subject)
    data[image_name] = proposal
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def approve_proposal(subject: str, image_name: str) -> dict[str, Any] | None:
    """Remove and return a proposal so it can be merged into the live bundle."""
    data = load_pending_proposals(subject)
    if image_name not in data:
        return None
    proposal = data.pop(image_name)
    path = _path_for(subject)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return proposal
