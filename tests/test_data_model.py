"""Tests for the data model and JSON persistence."""

from Script.functions.data_model import Bundle, Matter, Module, Question, load_bundle, save_bundle


def _sample_bundle() -> Bundle:
    q = Question(
        question="Pregunta de prueba",
        options=["A", "B"],
        answer="A",
        explanation="Explicacion",
        cita_textual="cita",
        topic="Tema 1",
        difficulty="alta",
        imagen_referencia="1.jpeg",
        image_path="noexiste.jpg",
    )
    module = Module(name="M1", topics=["Tema 1"], questions=[q])
    matter = Matter(name="Ciencias", modules=[module])
    return Bundle(matter="Cuarto grado", subjects=[matter])


def test_roundtrip_json(tmp_path):
    bundle = _sample_bundle()
    path = save_bundle(bundle, tmp_path / "b.json")
    loaded = load_bundle(path)
    assert path.exists()
    assert loaded.matter == "Cuarto grado"
    assert len(loaded.subjects) == 1
    assert loaded.subjects[0].name == "Ciencias"
    q = loaded.all_questions()[0]
    assert q.question == "Pregunta de prueba"
    assert q.options == ["A", "B"]
    assert q.answer == "A"
    assert q.topic == "Tema 1"
    assert q.difficulty == "alta"


def test_all_questions_flattens():
    bundle = _sample_bundle()
    assert len(bundle.all_questions()) == 1


def test_from_dict_defaults():
    q = Question.from_dict({})
    assert q.question == ""
    assert q.difficulty == "media"
    b = Bundle.from_dict({})
    assert b.subjects == []


def test_round_roundtrip_and_filter():
    q1 = Question(question="q1", options=["A", "B"], answer="A", round="marzo 2026")
    q2 = Question(question="q2", options=["A", "B"], answer="A", round="septiembre 2026")
    matter = Matter(name="Ciencias", modules=[Module(name="M1", questions=[q1, q2])])
    bundle = Bundle(matter="x", subjects=[matter])

    assert bundle.available_rounds() == ["marzo 2026", "septiembre 2026"]

    marzo = bundle.filter_by_round("marzo 2026")
    assert [q.question for q in marzo.all_questions()] == ["q1"]

    sept = matter.filter_by_round("septiembre 2026")
    assert [q.question for q in sept.all_questions()] == ["q2"]

    empty = bundle.filter_by_round("diciembre 2026")
    assert empty.subjects == []


def test_round_serialization_roundtrip(tmp_path):
    q = Question(
        question="q1",
        options=["A", "B"],
        answer="A",
        round="septiembre 2026",
    )
    bundle = Bundle(
        matter="x", subjects=[Matter(name="C", modules=[Module(name="M", questions=[q])])]
    )
    path = save_bundle(bundle, tmp_path / "r.json")
    loaded = load_bundle(path)
    assert loaded.all_questions()[0].round == "septiembre 2026"
