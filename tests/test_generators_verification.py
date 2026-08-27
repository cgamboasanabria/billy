"""Tests for the generators (HTML + MD) and the verifier."""

from Script.functions.data_model import Bundle, Matter, Module, Question
from Script.functions.html_generator import generate_subject_html, render_subject_html
from Script.functions.md_generator import generate_subject_md
from Script.functions.verification import filter_ready, verify_bundle


def _matter() -> Matter:
    q1 = Question(
        question="Que es la madurez sexual?",
        options=["A", "B", "C"],
        answer="A",
        explanation="es A",
        cita_textual="cita oficial",
        topic="Madurez sexual",
        difficulty="media",
        imagen_referencia="",
    )
    q2 = Question(
        question="Sin opciones ni cita",
        options=[],
        answer="",
        explanation="",
        cita_textual="",
        topic="",
        difficulty="rara",
        imagen_referencia="",
    )
    return Matter(name="Ciencias", modules=[Module(name="M1", topics=[], questions=[q1, q2])])


def test_generate_html_self_contained(tmp_path):
    out = generate_subject_html(_matter(), tmp_path / "Ciencias.html")
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "Estudio de Ciencias" in text
    assert "Madurez sexual" in text
    assert "const allQuestions" in text


def test_render_subject_html_returns_string():
    html = render_subject_html(_matter())
    assert isinstance(html, str)
    assert "Estudio de Ciencias" in html
    assert "const allQuestions" in html


def test_generate_html_renders_citation_page(tmp_path):
    """The citation page, when present, is rendered next to the citation."""
    q = Question(
        question="Hace cuanto tiempo fue ocupado el continente?",
        options=["10 mil anos", "40 mil anos"],
        answer="40 mil anos",
        cita_textual="Hace 40 mil",
        topic="historia",
        page="9",
    )
    matter = Matter(name="Estudios Sociales", modules=[Module(name="M1", questions=[q])])
    out = generate_subject_html(matter, tmp_path / "ES.html")
    text = out.read_text(encoding="utf-8")
    assert '"p": "9"' in text
    assert "(pagina " in text


def test_generate_md(tmp_path):
    out = generate_subject_md(_matter(), tmp_path / "Ciencias.md")
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "Guia de Estudio: Ciencias" in text
    assert "Que es la madurez sexual?" in text
    assert "cita oficial" in text


def test_verify_bundle_flags_errors():
    report = verify_bundle(Bundle(matter="x", subjects=[_matter()]))
    assert report.total == 2
    assert report.ok == 0
    assert report.has_errors
    assert "requiere al menos 2 opciones" in " ".join(i.message for i in report.issues)
    assert "cita oficial" not in " ".join(i.message for i in report.issues)


def test_filter_ready_keeps_valid_only():
    matter = _matter()
    ready = filter_ready(matter.all_questions())
    assert len(ready) == 1
    assert ready[0].question == "Que es la madurez sexual?"


def test_verify_flags_image_from_wrong_subject(tmp_path):
    """An image_path that lives under a different subject folder must be flagged."""
    fake_img = tmp_path / "matematicas" / "4.jpeg"
    fake_img.parent.mkdir(parents=True)
    fake_img.write_bytes(b"x")
    q = Question(
        question="Como se llama el gameto femenino?",
        options=["Espermatozoide", "Ovulo", "Hormona"],
        answer="Ovulo",
        cita_textual="el gameto femenino se llama ovulo",
        topic="Organos reproductivos",
        imagen_referencia="4.jpeg",
        image_path=str(fake_img),
    )
    matter = Matter(name="Ciencias", modules=[Module(name="M1", questions=[q])])
    report = verify_bundle(Bundle(matter="x", subjects=[matter]))
    assert report.has_errors
    assert any("imagen de otra materia" in i.message for i in report.issues)
