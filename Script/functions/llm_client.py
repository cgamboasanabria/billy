"""LLM client for the study tutor, using the OpenCode Zen endpoint.

The model is an OpenAI-compatible API. The API key is stored in the OS secure
store (keyring) with an environment-variable fallback, so it never lives in a
deliverable file and a curious child cannot read it from source.
"""

from __future__ import annotations

import os

from openai import OpenAI

from Script.functions.config import (
    DEFAULT_LLM_BASE_URL,
    DEFAULT_LLM_MODEL,
    ENV_VAR_LLM_KEY,
    TUTOR_TEMPERATURE,
)

_KEYRING_SERVICE = "billy"
_KEYRING_USER = "llm_key"


def _plain_key() -> str:
    return os.environ.get(ENV_VAR_LLM_KEY, "").strip()


def store_api_key(key: str) -> None:
    """Persist the key in the OS secure store if available."""
    try:
        import keyring

        keyring.set_password(_KEYRING_SERVICE, _KEYRING_USER, key)
    except Exception:
        os.environ[ENV_VAR_LLM_KEY] = key


def get_api_key() -> str:
    """Return the LLM key, preferring the secure store over the env var."""
    try:
        import keyring

        stored = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USER)
        if stored:
            return stored
    except Exception:
        pass
    return _plain_key()


def get_llm_client() -> OpenAI:
    """Return an OpenAI-compatible client for OpenCode Zen."""
    api_key = get_api_key()
    if not api_key:
        raise ValueError(
            "No hay API key configurada. Guardala con store_api_key() o la variable "
            f"de entorno {ENV_VAR_LLM_KEY}."
        )
    return OpenAI(base_url=DEFAULT_LLM_BASE_URL, api_key=api_key)


def tutor_answer(
    system: str,
    user: str,
    temperature: float = TUTOR_TEMPERATURE,
    max_tokens: int = 2000,
) -> str:
    """Single-turn chat completion with the tutor model at near-zero temp."""
    client = get_llm_client()
    response = client.chat.completions.create(
        model=DEFAULT_LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (response.choices[0].message.content or "").strip()
