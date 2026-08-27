"""Regression tests for image resolution with subject scope."""

import json

from Script.functions.import_existing import import_material


def test_find_image_picks_subject_scoped_match(tmp_path):
    """When two subjects have a 4.jpeg, the resolver must pick the one matching the source quiz's subject.

    Repro: gameto femenino in Ciencias.html references 4.jpeg, but a
    Matematicas/4.jpeg also exists. The Ciencias image must win.
    """
    quiz_dir = tmp_path / "quiz_html"
    quiz_dir.mkdir()
    orig_root = tmp_path / "originales"
    orig_root.mkdir()

    # Two subject folders, each with a 4.jpeg containing distinct bytes so we can verify which one wins.
    (orig_root / "ciencias" / "modulo_1").mkdir(parents=True)
    (orig_root / "matematicas" / "modulo_1").mkdir(parents=True)
    ciencias_img = orig_root / "ciencias" / "modulo_1" / "4.jpeg"
    mat_img = orig_root / "matematicas" / "modulo_1" / "4.jpeg"
    ciencias_img.write_bytes(b"CIENCIAS_IMAGE")
    mat_img.write_bytes(b"MATEMATICAS_IMAGE")

    # Provide an ORIGINALES_DIR env via monkeypatch by monkey-patching the module constant.
    from Script.functions import config as cfg
    from Script.functions import import_existing as ie

    monkey_target = orig_root
    original_dir = ie.ORIGINALES_DIR
    ie.ORIGINALES_DIR = monkey_target
    cfg.ORIGINALES_DIR = monkey_target
    try:
        ciencias_html = quiz_dir / "Ciencias.html"
        ciencias_html.write_text(
            "const allQuestions = "
            + json.dumps(
                [
                    {
                        "tema": "Organos reproductivos",
                        "pregunta": "Como se llama el gameto femenino?",
                        "opciones": ["Espermatozoide", "Ovulo", "Hormona"],
                        "respuesta_correcta": "Ovulo",
                        "explicacion": "es la celula sexual femenina",
                        "cita_textual": "El gameto femenino se llama ovulo",
                        "imagen_referencia": "4.jpeg",
                    }
                ]
            )
            + ";\n",
            encoding="utf-8",
        )
        bundle = import_material(
            quiz_html_dir=quiz_dir, mapeo_txt=tmp_path / "no.txt", include_curation=False
        )
        q = bundle.all_questions()[0]
        assert (
            q.image_path == str(ciencias_img.resolve())
            or q.image_path.endswith(str(ciencias_img))
            or "ciencias" in q.image_path
        )
        assert "matematicas" not in q.image_path
        # Bytes sanity check
        from pathlib import Path

        assert Path(q.image_path).read_bytes() == b"CIENCIAS_IMAGE"
    finally:
        ie.ORIGINALES_DIR = original_dir
        cfg.ORIGINALES_DIR = original_dir


def test_find_image_falls_back_global_when_no_scope_match(tmp_path):
    """If no subject-scoped match exists, fall back to global search (legacy behavior)."""
    quiz_dir = tmp_path / "quiz_html"
    quiz_dir.mkdir()
    orig_root = tmp_path / "originales"
    orig_root.mkdir()
    (orig_root / "ciencias" / "modulo_1").mkdir(parents=True)
    ciencias_img = orig_root / "ciencias" / "modulo_1" / "7.jpeg"
    ciencias_img.write_bytes(b"CIENCIAS_7")

    from Script.functions import config as cfg
    from Script.functions import import_existing as ie

    original_dir = ie.ORIGINALES_DIR
    ie.ORIGINALES_DIR = orig_root
    cfg.ORIGINALES_DIR = orig_root
    try:
        ciencias_html = quiz_dir / "Ciencias.html"
        ciencias_html.write_text(
            "const allQuestions = "
            + json.dumps(
                [
                    {
                        "tema": "X",
                        "pregunta": "?",
                        "opciones": ["A", "B"],
                        "respuesta_correcta": "A",
                        "imagen_referencia": "7.jpeg",
                    }
                ]
            )
            + ";\n",
            encoding="utf-8",
        )
        bundle = import_material(
            quiz_html_dir=quiz_dir, mapeo_txt=tmp_path / "no.txt", include_curation=False
        )
        assert bundle.all_questions()[0].image_path.endswith("7.jpeg")
    finally:
        ie.ORIGINALES_DIR = original_dir
        cfg.ORIGINALES_DIR = original_dir


def test_find_image_empty_when_missing(tmp_path):
    quiz_dir = tmp_path / "quiz_html"
    quiz_dir.mkdir()
    orig_root = tmp_path / "originales"
    orig_root.mkdir()

    from Script.functions import config as cfg
    from Script.functions import import_existing as ie

    original_dir = ie.ORIGINALES_DIR
    ie.ORIGINALES_DIR = orig_root
    cfg.ORIGINALES_DIR = orig_root
    try:
        ciencias_html = quiz_dir / "Ciencias.html"
        ciencias_html.write_text(
            "const allQuestions = "
            + json.dumps(
                [
                    {
                        "tema": "X",
                        "pregunta": "?",
                        "opciones": ["A", "B"],
                        "respuesta_correcta": "A",
                        "imagen_referencia": "no_existe_99.jpeg",
                    }
                ]
            )
            + ";\n",
            encoding="utf-8",
        )
        bundle = import_material(
            quiz_html_dir=quiz_dir, mapeo_txt=tmp_path / "no.txt", include_curation=False
        )
        assert bundle.all_questions()[0].image_path == ""
    finally:
        ie.ORIGINALES_DIR = original_dir
        cfg.ORIGINALES_DIR = original_dir
