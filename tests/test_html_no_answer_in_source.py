"""Tests for the anti-bloq-de-notas guarantee.

The HTML delivered to Billy must NOT contain the answer in source as plain
text. The answer is encoded as an option index in the embedded JSON and is
revealed only via JavaScript when the user clicks an option.
"""

from pathlib import Path

from Script.functions.data_model import Matter, Module, Question
from Script.functions.html_generator import generate_subject_html


def _sample_matter() -> Matter:
    return Matter(
        name="Ciencias",
        modules=[
            Module(
                name="M1",
                questions=[
                    Question(
                        question="Como se llama el gameto femenino?",
                        options=["Espermatozoide", "Ovulo", "Hormona"],
                        answer="Ovulo",
                        explanation="es la celula sexual femenina",
                        cita_textual="el gameto femenino se llama ovulo",
                        topic="Organos reproductivos",
                        imagen_referencia="",
                    )
                ],
            )
        ],
    )


def test_html_does_not_contain_answer_label(tmp_path):
    """The source must not contain 'Respuesta:' or 'Correcto:' markers."""
    out = generate_subject_html(_sample_matter(), tmp_path / "C.html")
    text = out.read_text(encoding="utf-8")
    assert "Respuesta:" not in text
    assert "respuesta_correcta" not in text
    assert '"a": "Ovulo"' not in text
    assert '"answer": "Ovulo"' not in text


def test_html_embeds_answer_as_index(tmp_path):
    """The JSON must carry the answer as a numeric index, not the text."""
    out = generate_subject_html(_sample_matter(), tmp_path / "C.html")
    text = out.read_text(encoding="utf-8")
    assert '"a":1' in text or '"a": 1' in text


def test_html_renders_study_and_quiz_panels(tmp_path):
    out = generate_subject_html(_sample_matter(), tmp_path / "C.html")
    text = out.read_text(encoding="utf-8")
    assert 'id="estudio"' in text
    assert 'id="quiz"' in text
    assert "Mostrar opciones" in text or "mostrar opciones" in text.lower()


def test_html_image_data_uri_dedup(tmp_path):
    """Images are still embedded as base64 data URIs (offline guarantee)."""
    img = tmp_path / "ciencias" / "m1" / "1.jpeg"
    img.parent.mkdir(parents=True)
    img.write_bytes(b"\xff\xd8\xff\xe0fakejpeg")
    matter = Matter(
        name="Ciencias",
        modules=[
            Module(
                name="M1",
                questions=[
                    Question(
                        question="Pregunta con imagen",
                        options=["A", "B"],
                        answer="A",
                        cita_textual="cita",
                        topic="T1",
                        imagen_referencia="1.jpeg",
                        image_path=str(img),
                    )
                ],
            )
        ],
    )
    out = generate_subject_html(matter, tmp_path / "C.html")
    text = out.read_text(encoding="utf-8")
    assert "data:image/jpeg;base64," in text


def test_answer_not_tagged_as_answer_in_source(tmp_path):
    """The literal answer text must not appear adjacent to 'answer' markers in source."""
    matter = _sample_matter()
    out = generate_subject_html(matter, tmp_path / "C.html")
    text = Path(out).read_text(encoding="utf-8")
    import re

    # The JSON should have a numeric a, not the answer text in a:"..." form.
    assert not re.search(r'"a"\s*:\s*"Ovulo"', text)
    assert not re.search(r"answer\s*[:=]\s*['\"]?Ovulo", text)
    assert not re.search(r'respuesta_correcta\s*[:=]\s*["\']?Ovulo', text)
