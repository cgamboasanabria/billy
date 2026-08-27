"""Vision grounding: answer a question using a printed source image."""

from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any

from Script.functions.config import VISION_MODEL
from Script.functions.llm_client import get_llm_client


def _image_url(image_path: str) -> str:
    mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    encoded = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _image_data_url_from_bytes(image_bytes: bytes, suffix: str = ".jpeg") -> str:
    mime = mimetypes.guess_type(f"img{suffix}")[0] or "image/jpeg"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def answer_from_image(image_path: str, question: str) -> str:
    """Ask the vision tutor about a printed page image."""
    client = get_llm_client()
    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un tutor para un nino de cuarto grado. Responde SOLO con la "
                    "informacion que aparece en la imagen. Si no esta en la imagen, "
                    "di: 'Eso no esta en tus apuntes.'. Respuestas cortas en espanol."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": _image_url(image_path)}},
                ],
            },
        ],
        temperature=0.0,
        max_tokens=1500,
    )
    return (response.choices[0].message.content or "").strip()


def propose_question_from_bytes(
    image_bytes: bytes, subject: str = "", suffix: str = ".jpeg"
) -> dict[str, Any]:
    """Ask the vision model to extract a multiple-choice question from an image.

    Returns a dict with keys: pregunta, opciones (list[str]), respuesta_correcta,
    explicacion, cita_textual, tema. The parent then edits and approves the
    proposal before it is saved as a real question.
    """
    client = get_llm_client()
    system = (
        "Eres un asistente que crea preguntas de opcion multiple para un nino de "
        "cuarto grado de Costa Rica, basadas en una pagina de libro que te "
        "muestran. Debes responder EXCLUSIVAMENTE con JSON valido (sin texto "
        "antes ni despues), con esta forma exacta: "
        '{"pregunta": str, "opciones": [str, str, str, str], '
        '"respuesta_correcta": str, "explicacion": str, "cita_textual": str, '
        '"tema": str}. La pregunta y la respuesta deben basarse solo en la '
        "imagen; la cita textual debe ser una frase corta tomada del texto "
        "visible en la imagen. Si la imagen no contiene suficiente informacion, "
        "responde con el mismo JSON pero con el campo pregunta vacio."
    )
    user_text = f"Materia: {subject}. Genera la pregunta en espanol."
    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": _image_data_url_from_bytes(image_bytes, suffix)},
                    },
                ],
            },
        ],
        temperature=0.0,
        max_tokens=1200,
    )
    text = (response.choices[0].message.content or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {
            "pregunta": "",
            "opciones": [],
            "respuesta_correcta": "",
            "explicacion": "",
            "cita_textual": "",
            "tema": "",
            "error": "JSON invalido devuelto por el modelo",
            "raw": text[:500],
        }
    return {
        "pregunta": str(data.get("pregunta", "")),
        "opciones": [str(o) for o in data.get("opciones", [])],
        "respuesta_correcta": str(data.get("respuesta_correcta", "")),
        "explicacion": str(data.get("explicacion", "")),
        "cita_textual": str(data.get("cita_textual", "")),
        "tema": str(data.get("tema", "")),
    }
