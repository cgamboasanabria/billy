"""Central configuration for the Billy project.

Defines project root and the standard directories used by the pipeline:
assets (source material), Output/Results (generated artifacts) and
Deliverables (bundles shared with Billy).

Uses pathlib so paths render with forward slashes on every platform.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR: Path = PROJECT_ROOT / "assets"
ORIGINALES_DIR: Path = ASSETS_DIR / "originales"
MAPEOS_DIR: Path = ASSETS_DIR / "mapeos"
LIBROS_DIR: Path = ASSETS_DIR / "libros"
TEMPLATES_DIR: Path = ASSETS_DIR / "templates"
OUTPUT_DIR: Path = PROJECT_ROOT / "Output" / "Results"
DELIVERABLES_DIR: Path = PROJECT_ROOT / "Deliverables"

ENV_VAR_LLM_KEY: str = "BILLY_LLM_API_KEY"
DEFAULT_LLM_BASE_URL: str = "https://opencode.ai/zen/v1"
DEFAULT_LLM_MODEL: str = "deepseek-v4-flash"
VISION_MODEL: str = "minimax-m3"
TUTOR_TEMPERATURE: float = 0.0

DEFAULT_EXAM_ROUND: str = "marzo 2026"
EXAM_ROUNDS: list[str] = ["marzo 2026", "septiembre 2026"]

for _d in (ORIGINALES_DIR, MAPEOS_DIR, LIBROS_DIR, TEMPLATES_DIR, OUTPUT_DIR, DELIVERABLES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

LLM_API_KEY: str = os.environ.get(ENV_VAR_LLM_KEY, "")
