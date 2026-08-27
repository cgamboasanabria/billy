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
    """Persist the key in the OS secure store, raising when it does not stick.

    If the secure store is unavailable or fails to round-trip the value, the
    key is kept only for the current process and a RuntimeError is raised so
    the caller can warn the user that it will not survive a restart.
    """
    key = key.strip()
    try:
        import keyring

        keyring.set_password(_KEYRING_SERVICE, _KEYRING_USER, key)
        persisted = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USER)
    except Exception as exc:  # noqa: BLE001
        os.environ[ENV_VAR_LLM_KEY] = key
        raise RuntimeError(
            "No se pudo guardar la API key en el almacen seguro del sistema "
            f"({exc}). Queda solo para esta sesion."
        ) from exc
    if persisted != key:
        os.environ[ENV_VAR_LLM_KEY] = key
        raise RuntimeError("El almacen seguro del sistema no devolvio la key recien guardada.")


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
    history: list[dict[str, str]] | None = None,
) -> str:
    """Chat completion with the tutor model, optionally with prior turns."""
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user})
    client = get_llm_client()
    response = client.chat.completions.create(
        model=DEFAULT_LLM_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (response.choices[0].message.content or "").strip()


def describe_llm_error(exc: Exception) -> str:
    """Return a short, actionable Spanish message for a tutor error."""
    text = str(exc)
    low = text.lower()
    if "401" in low or "unauthorized" in low or "invalid api key" in low:
        return f"Error 401: la API key no es valida o fue revocada. Detalle: {exc}"
    if "404" in low or "not found" in low or "not supported" in low:
        return f"Error 404: el modelo o la direccion no existe. Detalle: {exc}"
    if "api key" in low or "authentication" in low:
        return f"Error de autenticacion: revisa la API key. Detalle: {exc}"
    return f"Ocurrio un error al contactar al tutor: {exc}"
