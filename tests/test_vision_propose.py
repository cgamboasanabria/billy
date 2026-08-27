"""Tests for the vision-based question proposer."""

from __future__ import annotations

import json
from types import SimpleNamespace


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = SimpleNamespace(content=content)


class _FakeCompletions:
    def __init__(self, content: str) -> None:
        self._content = content
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(choices=[_FakeChoice(self._content)])


class _FakeChat:
    def __init__(self, content: str) -> None:
        self.completions = _FakeCompletions(content)


class _FakeClient:
    def __init__(self, content: str) -> None:
        self.chat = _FakeChat(content)


def test_propose_parses_clean_json(monkeypatch):
    payload = json.dumps(
        {
            "pregunta": "Que es X?",
            "opciones": ["A", "B", "C"],
            "respuesta_correcta": "B",
            "explicacion": "es B",
            "cita_textual": "frase del libro",
            "tema": "Tema X",
        }
    )
    from Script.functions import vision

    monkeypatch.setattr(vision, "get_llm_client", lambda: _FakeClient(payload))
    result = vision.propose_question_from_bytes(b"fake-image-bytes", subject="Ciencias")
    assert result["pregunta"] == "Que es X?"
    assert result["opciones"] == ["A", "B", "C"]
    assert result["respuesta_correcta"] == "B"
    assert result["tema"] == "Tema X"


def test_propose_strips_markdown_fence(monkeypatch):
    payload = (
        "```json\n"
        + json.dumps(
            {
                "pregunta": "Y?",
                "opciones": ["1", "2"],
                "respuesta_correcta": "1",
                "explicacion": "ok",
                "cita_textual": "c",
                "tema": "T",
            }
        )
        + "\n```"
    )
    from Script.functions import vision

    monkeypatch.setattr(vision, "get_llm_client", lambda: _FakeClient(payload))
    result = vision.propose_question_from_bytes(b"x")
    assert result["pregunta"] == "Y?"
    assert result["opciones"] == ["1", "2"]


def test_propose_handles_invalid_json(monkeypatch):
    from Script.functions import vision

    monkeypatch.setattr(vision, "get_llm_client", lambda: _FakeClient("not json at all"))
    result = vision.propose_question_from_bytes(b"x")
    assert result["pregunta"] == ""
    assert "error" in result


def test_answer_from_image_sends_image(monkeypatch, tmp_path):
    img = tmp_path / "p.jpeg"
    img.write_bytes(b"\xff\xd8\xff\xe0jpeg")
    fake = _FakeClient("Respuesta de la imagen.")
    from Script.functions import vision

    monkeypatch.setattr(vision, "get_llm_client", lambda: fake)
    out = vision.answer_from_image(str(img), "Que dice la imagen?")
    assert out == "Respuesta de la imagen."
    assert len(fake.chat.completions.calls) == 1
    call = fake.chat.completions.calls[0]
    user_content = call["messages"][1]["content"]
    has_image = any(
        isinstance(item, dict) and item.get("type") == "image_url" for item in user_content
    )
    assert has_image
