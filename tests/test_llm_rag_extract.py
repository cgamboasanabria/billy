"""Tests for the LLM client, RAG tutor and extract helpers (mocked)."""

import pytest

from Script.functions.data_model import Bundle, Matter, Module, Question
from Script.functions.extract import extract_pdf_text, ocr_image
from Script.functions.llm_client import (
    describe_llm_error,
    get_api_key,
    get_llm_client,
    store_api_key,
)
from Script.functions.rag import (
    build_corpus,
    grounded_answer,
    proactive_question,
    retrieve,
)


def _bundle() -> Bundle:
    q = Question(
        question="Que era la capital?",
        options=["A", "B"],
        answer="A",
        explanation="explica",
        cita_textual="La capital era A.",
        topic="Capitales",
    )
    return Bundle(
        matter="x", subjects=[Matter(name="Ciencias", modules=[Module(name="M", questions=[q])])]
    )


def test_api_key_env_fallback(monkeypatch):
    store = {}

    monkeypatch.setattr("keyring.get_password", lambda s, u: store.get(u), raising=False)
    monkeypatch.setenv("BILLY_LLM_API_KEY", "k123")
    assert get_api_key() == "k123"


def test_store_api_key_round_trip(monkeypatch):
    store = {}

    monkeypatch.setattr(
        "keyring.set_password", lambda s, u, v: store.__setitem__(u, v), raising=False
    )
    monkeypatch.setattr("keyring.get_password", lambda s, u: store.get(u), raising=False)
    monkeypatch.delenv("BILLY_LLM_API_KEY", raising=False)

    store_api_key("k456")
    assert store.get("llm_key") == "k456"
    assert get_api_key() == "k456"


def test_get_llm_client_raises_without_key(monkeypatch):
    monkeypatch.setattr("Script.functions.llm_client.get_api_key", lambda: "")
    with pytest.raises(ValueError):
        get_llm_client()


def test_store_api_key_raises_when_keyring_fails(monkeypatch):
    def boom(s, u, v):
        raise OSError("no backend")

    monkeypatch.setattr("keyring.set_password", boom, raising=False)
    monkeypatch.delenv("BILLY_LLM_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        store_api_key("k789")


def test_store_api_key_raises_when_round_trip_fails(monkeypatch):
    monkeypatch.setattr("keyring.set_password", lambda s, u, v: None, raising=False)
    monkeypatch.setattr("keyring.get_password", lambda s, u: "otra-cosa", raising=False)
    monkeypatch.delenv("BILLY_LLM_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        store_api_key("k789")


def test_describe_llm_error_maps_401():
    assert "401" in describe_llm_error(Exception("Error code: 401 - invalid api key"))


def test_describe_llm_error_maps_404():
    assert "404" in describe_llm_error(Exception("Error code: 404 - model not found"))


def test_describe_llm_error_maps_auth():
    assert "autenticacion" in describe_llm_error(Exception("authentication failed"))


def test_describe_llm_error_fallback():
    assert "Ocurrio un error" in describe_llm_error(Exception("boom"))


def test_tutor_answer_passes_history(monkeypatch):
    """tutor_answer inserts prior turns between system and the current user."""
    from Script.functions.llm_client import tutor_answer

    captured = {}

    class FakeChoice:
        class Msg:
            content = "respuesta"

        def __init__(self):
            self.message = self.Msg()

    class FakeResp:
        def __init__(self):
            self.choices = [FakeChoice()]

    class _Completions:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return FakeResp()

    class _Chat:
        completions = _Completions()

    class FakeClient:
        chat = _Chat()

    monkeypatch.setattr("Script.functions.llm_client.get_llm_client", lambda: FakeClient())
    history = [
        {"role": "user", "content": "hola"},
        {"role": "assistant", "content": "hola!"},
    ]
    result = tutor_answer("sys", "que tal", history=history)
    assert result == "respuesta"
    messages = captured["kwargs"]["messages"]
    assert messages[0] == {"role": "system", "content": "sys"}
    assert messages[1:3] == history
    assert messages[-1] == {"role": "user", "content": "que tal"}


def test_build_corpus_and_retrieve():
    corpus = build_corpus(_bundle())
    assert len(corpus) == 1
    assert corpus[0].topic == "Capitales"
    hits = retrieve("que capital", corpus, top_k=1)
    assert len(hits) == 1
    assert hits[0].answer == "A"


def test_grounded_answer_answers_from_context(monkeypatch):
    captured = {}

    def fake_tutor(system, user, temperature=0.0, max_tokens=2000, history=None):
        captured["system"] = system
        captured["user"] = user
        return "La capital era A."

    monkeypatch.setattr("Script.functions.llm_client.tutor_answer", fake_tutor)
    answer = grounded_answer("capital", _bundle())
    assert answer == "La capital era A."
    assert "Capitales" in captured["user"]
    assert "nunca inventes" in captured["system"].lower()


def test_grounded_answer_overview_when_no_overlap(monkeypatch):
    """Sin solapamiento responde con un resumen de temas, no una pregunta."""
    captured = {}

    def fake_tutor(system, user, temperature=0.0, max_tokens=2000, history=None):
        captured["user"] = user
        return "Estos son los temas de la materia."

    monkeypatch.setattr("Script.functions.llm_client.tutor_answer", fake_tutor)
    answer = grounded_answer("explicame los temas", _bundle())
    assert answer == "Estos son los temas de la materia."
    assert "Tema: Capitales" in captured["user"]


def test_grounded_answer_proactive_when_abstain(monkeypatch):
    """Cuando el modelo se abstiene, lanza una pregunta reformulada."""

    def fake_tutor(system, user, temperature=0.0, max_tokens=2000, history=None):
        return "Eso no esta en tus apuntes todavia."

    monkeypatch.setattr("Script.functions.llm_client.tutor_answer", fake_tutor)
    asked: set[str] = set()
    answer = grounded_answer("dinosaurios", _bundle(), asked=asked)
    assert "Mejor te pregunto" in answer
    assert len(asked) == 1


def test_grounded_answer_uses_history_for_followup(monkeypatch):
    """Un 'no me acuerdo' usa el turno previo para recuperar el tema."""
    captured = {}

    def fake_tutor(system, user, temperature=0.0, max_tokens=2000, history=None):
        captured["user"] = user
        captured["history"] = history
        return "La capital era A."

    monkeypatch.setattr("Script.functions.llm_client.tutor_answer", fake_tutor)
    history = [
        {"role": "user", "content": "explicame los temas"},
        {"role": "assistant", "content": "Mejor te pregunto: Que era la capital?"},
    ]
    answer = grounded_answer("no me acuerdo de eso", _bundle(), history=history)
    assert answer == "La capital era A."
    assert captured["history"] == history
    assert "Capitales" in captured["user"]


def test_proactive_question_rotates_without_repeat(monkeypatch):
    """Dos preguntas seguidas usan preguntas distintas de la ronda."""
    bundle = _two_question_bundle()
    asked: set[str] = set()
    calls: list[str] = []

    def fake_tutor(system, user, temperature=0.0, max_tokens=2000):
        calls.append(user)
        return user

    monkeypatch.setattr("Script.functions.llm_client.tutor_answer", fake_tutor)
    first = proactive_question(bundle, asked)
    second = proactive_question(bundle, asked)
    assert first == "Eso no esta en tus apuntes todavia. Mejor te pregunto: " + calls[0]
    assert second == "Eso no esta en tus apuntes todavia. Mejor te pregunto: " + calls[1]
    assert calls[0] != calls[1]
    assert len(asked) == 2


def test_proactive_question_resets_when_exhausted(monkeypatch):
    """Al agotar la ronda, vuelve a empezar sin repetir."""
    bundle = _bundle()
    asked: set[str] = set()

    def fake_tutor(system, user, temperature=0.0, max_tokens=2000):
        return user

    monkeypatch.setattr("Script.functions.llm_client.tutor_answer", fake_tutor)
    first = proactive_question(bundle, asked)
    second = proactive_question(bundle, asked)
    assert first != ""
    assert first == second


def _two_question_bundle() -> Bundle:
    q1 = Question(question="Pregunta uno?", options=["A", "B"], answer="A", topic="T1")
    q2 = Question(question="Pregunta dos?", options=["C", "D"], answer="C", topic="T2")
    return Bundle(
        matter="x",
        subjects=[Matter(name="Ciencias", modules=[Module(name="M", questions=[q1, q2])])],
    )


def test_extract_pdf_text(monkeypatch, tmp_path):
    class FakePage:
        def extract_text(self):
            return "Contenido de la pagina"

    class FakeReader:
        def __init__(self, path):
            self.pages = [FakePage()]

    monkeypatch.setattr("pypdf.PdfReader", FakeReader)
    result = extract_pdf_text(tmp_path / "x.pdf")
    assert "Contenido de la pagina" in result


def test_ocr_without_tesseract(tmp_path):
    result = ocr_image(tmp_path / "x.jpg")
    assert result == ""


def test_answer_from_image_mock(monkeypatch, tmp_path):
    from Script.functions.vision import answer_from_image

    img = tmp_path / "page.jpg"
    img.write_bytes(b"\xff\xd8\xff")  # bytes suficientes para data uri

    captured = {}

    class FakeChoice:
        class Msg:
            content = "Respuesta desde la imagen"

        def __init__(self):
            self.message = self.Msg()

    class FakeResp:
        def __init__(self):
            self.choices = [FakeChoice()]

    class _Completions:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return FakeResp()

    class _Chat:
        completions = _Completions()

    class FakeClient:
        chat = _Chat()

    monkeypatch.setattr("Script.functions.vision.get_llm_client", lambda: FakeClient())
    answer = answer_from_image(str(img), "Pregunta?")
    assert answer == "Respuesta desde la imagen"
    parts = captured["kwargs"]["messages"][1]["content"]
    assert parts[0]["type"] == "text"
    assert parts[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
