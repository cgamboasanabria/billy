"""Diagnostico del tutor LLM con una llamada real.

Uso:

    python Script/diagnostico_llm.py

Imprime en una linea si el tutor responde o el error exacto (codigo HTTP y
detalle), para que el padre pueda diagnosticar sin ver la maquina de Billy.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Script.functions.config import DEFAULT_LLM_BASE_URL, DEFAULT_LLM_MODEL
from Script.functions.llm_client import get_api_key, get_llm_client


def main() -> None:
    key = get_api_key()
    if not key:
        print("TUTOR ERROR: no hay API key configurada.")
        return
    print(f"TUTOR key presente (largo {len(key)})")
    print(f"TUTOR endpoint {DEFAULT_LLM_BASE_URL} modelo {DEFAULT_LLM_MODEL}")
    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model=DEFAULT_LLM_MODEL,
            messages=[{"role": "user", "content": "Responde con una sola palabra: hola"}],
            temperature=0.0,
            max_tokens=16,
        )
        answer = (response.choices[0].message.content or "").strip()
        print(f"TUTOR OK: {answer}")
    except Exception as exc:  # noqa: BLE001
        print(f"TUTOR ERROR: {exc}")


if __name__ == "__main__":
    main()
