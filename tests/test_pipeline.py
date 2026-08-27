"""Tests for the end-to-end pipeline driver."""

from Script.functions.data_model import Bundle, Matter, Module, Question
from Script.functions.pipeline import run_pipeline


def _small_bundle() -> Bundle:
    q = Question(
        question="Que es X?",
        options=["A", "B"],
        answer="A",
        cita_textual="cita",
        topic="Tema",
        difficulty="media",
    )
    return Bundle(
        matter="Cuarto grado",
        subjects=[Matter(name="Ciencias", modules=[Module(name="M", questions=[q])])],
    )


def test_run_pipeline_generates_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr("Script.functions.pipeline.import_material", lambda: _small_bundle())
    out = tmp_path / "out"
    deliv = tmp_path / "deliv"
    result = run_pipeline(output_dir=out, deliverables_dir=deliv)

    assert result["total_questions"] == 1
    assert result["subjects"] == ["Ciencias"]
    assert (out / "Ciencias.html").exists()
    assert (out / "Ciencias.md").exists()
    assert (deliv / "Ciencias.bundle.json").exists()

    zips = list(deliv.glob("*_deliverable.zip"))
    assert len(zips) == 1
    assert "report" in result
    assert "generated" in result


def test_run_pipeline_empty_bundle(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "Script.functions.pipeline.import_material",
        lambda: Bundle(matter="x", subjects=[]),
    )
    result = run_pipeline(output_dir=tmp_path / "o", deliverables_dir=tmp_path / "d")
    assert result["total_questions"] == 0
    assert result["subjects"] == []
