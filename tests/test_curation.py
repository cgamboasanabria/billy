"""Tests for the curation (vision-proposed questions) workflow."""

import Script.functions.curation as cur
from Script.functions.curation import (
    approve_proposal,
    load_pending_proposals,
    save_proposal,
)


def _proposal(pregunta: str = "Como funciona X?", answer: str = "A") -> dict:
    return {
        "pregunta": pregunta,
        "opciones": ["A", "B", "C"],
        "respuesta_correcta": answer,
        "explicacion": "porque si",
        "cita_textual": "frase del libro",
        "tema": "Tema X",
    }


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(cur, "_NUEVAS_DIR", tmp_path)
    save_proposal("Ciencias", "1.jpeg", _proposal())
    loaded = load_pending_proposals("Ciencias")
    assert "1.jpeg" in loaded
    assert loaded["1.jpeg"]["pregunta"] == "Como funciona X?"


def test_approve_removes_proposal(tmp_path, monkeypatch):
    monkeypatch.setattr(cur, "_NUEVAS_DIR", tmp_path)
    save_proposal("Matematicas", "2.jpeg", _proposal(pregunta="2+2?", answer="4"))
    approved = approve_proposal("Matematicas", "2.jpeg")
    assert approved is not None
    assert approved["pregunta"] == "2+2?"
    assert load_pending_proposals("Matematicas") == {}


def test_load_returns_empty_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(cur, "_NUEVAS_DIR", tmp_path)
    assert load_pending_proposals("Estudios Sociales") == {}
