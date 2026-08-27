"""Tests for the existing-material importer."""

import json

from Script.functions.import_existing import import_material


def test_import_quiz_html(tmp_path, monkeypatch):
    html = tmp_path / "Ciencias.html"
    questions = [
        {
            "tema": "Madurez sexual",
            "pregunta": "Que es la madurez sexual?",
            "opciones": ["A", "B"],
            "respuesta_correcta": "A",
            "explicacion": "definicion",
            "cita_textual": "una cita",
            "imagen_referencia": "noexiste_1.jpeg",
        }
    ]
    html.write_text(
        "const allQuestions = " + json.dumps(questions) + ";\n",
        encoding="utf-8",
    )
    bundle = import_material(
        quiz_html_dir=tmp_path, mapeo_txt=tmp_path / "no_existe.txt", include_curation=False
    )
    assert len(bundle.subjects) == 1
    assert bundle.subjects[0].name == "Ciencias"
    q = bundle.all_questions()[0]
    assert q.question == "Que es la madurez sexual?"
    assert q.options == ["A", "B"]
    assert q.answer == "A"
    assert q.cita_textual == "una cita"
    assert q.topic == "Madurez sexual"
    assert not q.image_path  # imagen no resuelvable -> vacio


def test_import_mapeo_txt(tmp_path):
    mapeo = tmp_path / "mapeo.txt"
    mapeo.write_text(
        "**Archivo de Imagen:** `Ciencias/M1/1.jpeg`\n"
        "**Descripcion:** algo\n"
        "**Pregunta:** Que es X?\n"
        "**Respuesta:** Es X.\n"
        '**Cita Textual:** "cita de X"\n'
        "---\n",
        encoding="utf-8",
    )
    bundle = import_material(
        quiz_html_dir=tmp_path / "vacio", mapeo_txt=mapeo, include_curation=False
    )
    q = bundle.all_questions()[0]
    assert q.question == "Que es X?"
    assert q.answer == "Es X."
    assert q.cita_textual == "cita de X"
    assert q.imagen_referencia == "1.jpeg"


_ES_FORMAT = """const questions = [
  // TEXTOS (1-20)
  { cat: "Textos", q: "Cual es el objetivo de un texto narrativo?", a: ["Contar una historia", "Dormir"], correct: 0, p: 21, frag: "Contar una historia" },
];
"""


def test_import_espanol_format(tmp_path):
    html = tmp_path / "Espanol.html"
    html.write_text(_ES_FORMAT, encoding="utf-8")
    bundle = import_material(
        quiz_html_dir=tmp_path, mapeo_txt=tmp_path / "no.txt", include_curation=False
    )
    assert bundle.subjects[0].name == "Espanol"
    q = bundle.all_questions()[0]
    assert q.question == "Cual es el objetivo de un texto narrativo?"
    assert q.options == ["Contar una historia", "Dormir"]
    assert q.answer == "Contar una historia"
    assert q.cita_textual == "Contar una historia"
    assert q.topic == "Textos"
    assert q.page == "21"


_SOCIALES_FORMAT = """const rawQuestions = [
  // HISTORIA ANTIGUA
  { topic: 'historia', q: 'Hace cuanto tiempo fue ocupado el continente?', opts: ['10 mil anos', '40 mil anos'], a: '40 mil anos', cite: 'Hace 40 mil', p: '9' },
];
"""


def test_import_sociales_format(tmp_path):
    html = tmp_path / "Estudios_Sociales.html"
    html.write_text(_SOCIALES_FORMAT, encoding="utf-8")
    bundle = import_material(
        quiz_html_dir=tmp_path, mapeo_txt=tmp_path / "no.txt", include_curation=False
    )
    assert bundle.subjects[0].name == "Estudios Sociales"
    q = bundle.all_questions()[0]
    assert q.question == "Hace cuanto tiempo fue ocupado el continente?"
    assert q.options == ["10 mil anos", "40 mil anos"]
    assert q.answer == "40 mil anos"
    assert q.topic == "historia"
    assert q.cita_textual == "Hace 40 mil"
    assert q.page == "9"


def test_import_applies_default_round(tmp_path):
    """Questions without an explicit round fall back to the default round."""
    html = tmp_path / "Ciencias.html"
    html.write_text(
        "const allQuestions = "
        + json.dumps(
            [
                {
                    "tema": "T",
                    "pregunta": "P?",
                    "opciones": ["A", "B"],
                    "respuesta_correcta": "A",
                }
            ]
        )
        + ";\n",
        encoding="utf-8",
    )
    bundle = import_material(
        quiz_html_dir=tmp_path, mapeo_txt=tmp_path / "no.txt", include_curation=False
    )
    q = bundle.all_questions()[0]
    assert q.round == "marzo 2026"


def test_import_curation_reads_ronda(tmp_path, monkeypatch):
    """A curated proposal tagged with a ronda keeps that round."""
    import Script.functions.config as cfg
    import Script.functions.curation as cur
    import Script.functions.import_existing as ie

    monkeypatch.setattr(cfg, "MAPEOS_DIR", tmp_path)
    monkeypatch.setattr(cur, "MAPEOS_DIR", tmp_path)
    monkeypatch.setattr(ie, "MAPEOS_DIR", tmp_path)
    monkeypatch.setattr(ie, "ORIGINALES_DIR", tmp_path)
    monkeypatch.setattr(cfg, "ORIGINALES_DIR", tmp_path)

    nuevas = tmp_path / "nuevas"
    nuevas.mkdir()
    (nuevas / "Ciencias.json").write_text(
        json.dumps(
            {
                "1.jpeg": {
                    "pregunta": "Pregunta nueva?",
                    "opciones": ["A", "B"],
                    "respuesta_correcta": "A",
                    "ronda": "septiembre 2026",
                    "pagina": "93",
                }
            }
        ),
        encoding="utf-8",
    )
    bundle = import_material(quiz_html_dir=tmp_path / "vacio", mapeo_txt=tmp_path / "no.txt")
    curated = [q for q in bundle.all_questions() if q.question == "Pregunta nueva?"]
    assert len(curated) == 1
    assert curated[0].round == "septiembre 2026"
    assert curated[0].page == "93"


def test_import_merges_same_subject(tmp_path):
    quiz = tmp_path / "Ciencias.html"
    quiz.write_text(
        "const allQuestions = "
        + json.dumps(
            [
                {
                    "tema": "Madurez sexual",
                    "pregunta": "Que es la madurez sexual?",
                    "opciones": ["A", "B"],
                    "respuesta_correcta": "A",
                    "cita_textual": "cita quiz",
                }
            ]
        )
        + ";\n",
        encoding="utf-8",
    )
    mapeo = tmp_path / "mapeo.txt"
    mapeo.write_text(
        "**Archivo de Imagen:** `x/1.jpeg`\n"
        "**Pregunta:** Que es la biodiversidad?\n"
        "**Respuesta:** Variedad de vida.\n"
        '**Cita Textual:** "cita"\n',
        encoding="utf-8",
    )
    # two sources, both Ciencias -> import_material appends modules to one subject
    bundle = import_material(quiz_html_dir=tmp_path, mapeo_txt=mapeo, include_curation=False)
    ciencias = [s for s in bundle.subjects if s.name == "Ciencias"]
    assert len(ciencias) == 1
    assert len(ciencias[0].modules) == 2


def test_import_merges_curation_proposals(tmp_path, monkeypatch):
    """Approved vision-curated proposals in nuevas/*.json land in the Bundle."""
    # Set up a private MAPEOS_DIR pointing to tmp_path so we don't touch the real repo.
    import Script.functions.config as cfg
    import Script.functions.curation as cur
    import Script.functions.import_existing as ie

    monkeypatch.setattr(cfg, "MAPEOS_DIR", tmp_path)
    monkeypatch.setattr(cur, "MAPEOS_DIR", tmp_path)
    ie.MAPEOS_DIR = tmp_path

    nuevas = tmp_path / "nuevas"
    nuevas.mkdir()
    payload = {
        "1.jpeg": {
            "pregunta": "Pregunta curada 1?",
            "opciones": ["A", "B", "C"],
            "respuesta_correcta": "B",
            "explicacion": "porque B",
            "cita_textual": "frase del libro",
            "tema": "Tema curado",
        }
    }
    (nuevas / "Ciencias.json").write_text(json.dumps(payload), encoding="utf-8")

    # Also place an actual image so the resolver can find it.
    img_dir = tmp_path / "ciencias" / "modulo_1"
    img_dir.mkdir(parents=True)
    (img_dir / "1.jpeg").write_bytes(b"CIENCIAS_1")
    ie.ORIGINALES_DIR = tmp_path
    monkeypatch.setattr(cfg, "ORIGINALES_DIR", tmp_path)

    bundle = import_material(quiz_html_dir=tmp_path / "vacio", mapeo_txt=tmp_path / "no.txt")
    ciencias = [s for s in bundle.subjects if s.name == "Ciencias"]
    assert len(ciencias) == 1
    curated = [q for q in ciencias[0].all_questions() if q.question == "Pregunta curada 1?"]
    assert len(curated) == 1
    assert curated[0].answer == "B"
    assert curated[0].image_path.endswith("ciencias" + chr(92) + "modulo_1" + chr(92) + "1.jpeg")


def test_import_curation_skips_invalid_proposals(tmp_path, monkeypatch):
    """Proposals with no valid answer/options are silently skipped."""
    import Script.functions.config as cfg
    import Script.functions.curation as cur
    import Script.functions.import_existing as ie

    monkeypatch.setattr(cfg, "MAPEOS_DIR", tmp_path)
    monkeypatch.setattr(cur, "MAPEOS_DIR", tmp_path)
    ie.MAPEOS_DIR = tmp_path
    ie.ORIGINALES_DIR = tmp_path
    monkeypatch.setattr(cfg, "ORIGINALES_DIR", tmp_path)

    nuevas = tmp_path / "nuevas"
    nuevas.mkdir()
    (nuevas / "Matematicas.json").write_text(
        json.dumps(
            {
                "bad.jpeg": {"pregunta": "", "opciones": [], "respuesta_correcta": ""},
                "wrong-answer.jpeg": {
                    "pregunta": "ok",
                    "opciones": ["A", "B"],
                    "respuesta_correcta": "Z",
                },
            }
        ),
        encoding="utf-8",
    )
    bundle = import_material(quiz_html_dir=tmp_path / "vacio", mapeo_txt=tmp_path / "no.txt")
    mats = [s for s in bundle.subjects if s.name == "Matematicas"]
    assert mats == []
