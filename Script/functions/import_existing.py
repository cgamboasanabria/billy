"""Import existing study material into the data model.

Two source formats are supported:

* ``assets/mapeos/quiz_html/*.html`` -- the self-contained quiz HTML produced
  previously. It embeds a ``const allQuestions = [ ... ]`` array of JSON
  objects with keys: tema, pregunta, opciones, respuesta_correcta, explicacion,
  cita_textual, imagen_referencia. This is the richest source (real multiple
  choice options + citations).

* ``assets/mapeos/mapeo_ciencias_definitivo.txt`` -- a per-image mapping with
  Archivo de Imagen / Pregunta / Respuesta / Cita Textual fields.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

from Script.functions.config import DEFAULT_EXAM_ROUND, MAPEOS_DIR, ORIGINALES_DIR
from Script.functions.data_model import Bundle, Matter, Module, Question

_MATERIA_ALIASES: dict[str, str] = {
    "ciencias": "Ciencias",
    "espanol": "Espanol",
    "estudios_sociales_y_civica": "Estudios Sociales",
    "estudios_sociales": "Estudios Sociales",
    "matematicas": "Matematicas",
}


def _subject_name(filename: str) -> str:
    stem = Path(filename).stem
    for key, name in _MATERIA_ALIASES.items():
        if key in stem.lower():
            return name
    return stem.replace("_", " ").title()


def _subject_slug(name: str) -> str:
    """Normalize a subject name to its folder slug.

    The originals tree uses folder names like ``ciencias``, ``matematicas``,
    ``espanol`` and ``estudios_sociales``; the bundle uses canonical display
    names. This maps the canonical to the slug so we can scope image lookup.
    """
    normalized = name.strip().lower()
    aliases = {
        "ciencias": "ciencias",
        "espanol": "espanol",
        "estudios sociales": "estudios_sociales",
        "matematicas": "matematicas",
    }
    return aliases.get(normalized, normalized.replace(" ", "_"))


def _find_image(reference: str, subject: str | None = None) -> str:
    """Resolve a reference image by searching the originales tree for its name.

    When ``subject`` is provided, candidate paths whose location contains the
    subject slug (anywhere in the path) are preferred so duplicate filenames
    across subjects (such as ``4.jpeg`` in both ciencias and matematicas
    exams) resolve to the pedagogically correct image. Falls back to a global
    first-match search when no scoped match is found.
    """
    candidate = Path(reference).name
    if not candidate or candidate == "None":
        return ""
    slug = _subject_slug(subject) if subject else ""
    fallback = ""
    for path in ORIGINALES_DIR.rglob(candidate):
        if slug and slug in path.parts:
            return str(path)
        if not fallback:
            fallback = str(path)
    return fallback


def _load_quiz_html(path: Path) -> list[Question]:
    """Parse a quiz HTML into a list of Questions.

    Supports the three historic formats: ``allQuestions`` (JSON-like, the one
    with images), ``questions`` (Espanol: options + correct index) and
    ``rawQuestions`` (Estudios Sociales: opts + answer string).
    """
    text = path.read_text(encoding="utf-8")
    array_text = _quiz_array(text)
    if not array_text:
        return []
    items = _parse_items(array_text)
    questions: list[Question] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if "respuesta_correcta" in item:
            item_with_subject = {**item, "_subject": _subject_name(path.name)}
            questions.append(_from_standard(item_with_subject))
        elif "correct" in item and "cat" in item:
            item_with_subject = {**item, "_subject": _subject_name(path.name)}
            questions.append(_from_espanol(item_with_subject))
        elif "opts" in item and "a" in item:
            item_with_subject = {**item, "_subject": _subject_name(path.name)}
            questions.append(_from_sociales(item_with_subject))
    return questions


def _from_standard(item: dict) -> Question:
    image_ref = str(item.get("imagen_referencia", ""))
    return Question(
        question=str(item.get("pregunta", "")),
        options=[str(o) for o in item.get("opciones", [])],
        answer=str(item.get("respuesta_correcta", "")),
        explanation=str(item.get("explicacion", "")),
        cita_textual=str(item.get("cita_textual", "")),
        topic=str(item.get("tema", "")),
        difficulty="media",
        imagen_referencia=image_ref,
        image_path=_find_image(image_ref, item.get("_subject")),
    )


def _from_espanol(item: dict) -> Question:
    options = [str(o) for o in item.get("a", [])]
    correct = item.get("correct", 0)
    answer = options[correct] if isinstance(correct, int) and 0 <= correct < len(options) else ""
    return Question(
        question=str(item.get("q", "")),
        options=options,
        answer=answer,
        explanation="",
        cita_textual=str(item.get("frag", "")),
        topic=str(item.get("cat", "")),
        difficulty="media",
        page=str(item.get("p", "")),
    )


def _from_sociales(item: dict) -> Question:
    return Question(
        question=str(item.get("q", "")),
        options=[str(o) for o in item.get("opts", [])],
        answer=str(item.get("a", "")),
        explanation="",
        cita_textual=str(item.get("cite", "")),
        topic=str(item.get("topic", "")),
        difficulty="media",
        page=str(item.get("p", "")),
    )


def _quiz_array(text: str) -> str:
    """Extract the quiz array literal for whichever variable holds it."""
    m = re.search(r"const\s+(?:allQuestions|questions|rawQuestions)\s*=\s*(\[)", text)
    if not m:
        return ""
    start = m.start(1)
    return _balanced(text, start)


def _balanced(text: str, start: int) -> str:
    """Return the substring from ``[`` (at start) to its matching ``]``."""
    depth = 0
    in_string = False
    quote = ""
    i = start
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == quote:
                in_string = False
        elif ch in "'\"":
            in_string = True
            quote = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
        i += 1
    return text[start:]


def _parse_items(text: str) -> list[dict]:
    """Parse a JS quiz array into a list of dicts, tolerating both formats.

    Valid JSON (``allQuestions``) is parsed with json.loads. The historic
    formats with unquoted keys, line comments and nested quotes (``questions``,
    ``rawQuestions``) are handled by a quote-aware scanner.
    """
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    return _scan_items(text)


def _read_string(text: str, i: int, quote: str) -> tuple[str, int]:
    """Read a quoted string starting at text[i] == quote; return (value, next_i)."""
    i += 1
    parts: list[str] = []
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            parts.append(text[i + 1])
            i += 2
            continue
        if ch == quote:
            return "".join(parts), i + 1
        parts.append(ch)
        i += 1
    return "".join(parts), i


def _read_value(text: str, i: int) -> tuple[object, int]:
    """Read a value (string, number or array) starting at i; return (value, next_i)."""
    while i < len(text) and text[i] in " \t\n,":
        i += 1
    if i >= len(text):
        return None, i
    ch = text[i]
    if ch in "'\"":
        return _read_string(text, i, ch)
    if ch == "[":
        arr: list[object] = []
        i += 1
        while i < len(text):
            val, i = _read_value(text, i)
            if val is not None or i < len(text):
                arr.append(val)
            if i < len(text) and text[i] == "]":
                return arr, i + 1
        return arr, i
    if ch.isdigit() or ch == "-":
        j = i
        while j < len(text) and (text[j].isdigit() or text[j] == "-"):
            j += 1
        return int(text[i:j]), j
    return None, i


def _scan_items(text: str) -> list[dict]:
    """Scan a JS array of object literals into a list of dicts.

    Keys and string values are read with a quote-aware scanner so nested quotes
    (as found in the Espanol and Estudios Sociales sources) do not break it.
    """
    items: list[dict] = []
    i = 0
    while i < len(text):
        if text[i] == "{":
            item, i = _scan_object(text, i)
            items.append(item)
        else:
            i += 1
    return items


def _scan_object(text: str, i: int) -> tuple[dict, int]:
    """Read one object literal starting at text[i] == '{'; return (dict, next_i)."""
    obj: dict[str, object] = {}
    i += 1
    while i < len(text):
        while i < len(text) and text[i] in " \t\n,":
            i += 1
        if i >= len(text) or text[i] == "}":
            i = i + 1 if i < len(text) else i
            break
        if text[i] in "'\"":
            key, i = _read_string(text, i, text[i])
        else:
            j = i
            while j < len(text) and (text[j].isalnum() or text[j] == "_"):
                j += 1
            key = text[i:j]
            i = j
        while i < len(text) and text[i] in " \t\n":
            i += 1
        if i < len(text) and text[i] == ":":
            i += 1
        value, i = _read_value(text, i)
        obj[key] = value
    return obj, i


def _load_mapeo_txt(path: Path) -> list[Question]:
    """Parse the per-image mapping txt into a list of Questions (no options)."""
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"\n---+\n", text)
    questions: list[Question] = []
    for block in blocks:
        image = ""
        question = ""
        answer = ""
        cita = ""
        for line in block.splitlines():
            if line.startswith("**Archivo de Imagen:**"):
                m = re.search(r"`(.+?)`", line)
                if m:
                    image = Path(m.group(1)).name
            elif line.startswith("**Pregunta:**"):
                question = line.split("**Pregunta:**", 1)[1].strip()
            elif line.startswith("**Respuesta:**"):
                answer = line.split("**Respuesta:**", 1)[1].strip()
            elif line.startswith("**Cita Textual:**"):
                cita = line.split("**Cita Textual:**", 1)[1].strip().strip('"')
        if question and answer:
            questions.append(
                Question(
                    question=question,
                    options=[],
                    answer=answer,
                    explanation="",
                    cita_textual=cita,
                    topic="",
                    difficulty="media",
                    imagen_referencia=image,
                    image_path=_find_image(image, "Ciencias"),
                )
            )
    return questions


def import_material(
    quiz_html_dir: str | Path | None = None,
    mapeo_txt: str | Path | None = None,
    include_curation: bool = True,
) -> Bundle:
    """Build a Bundle from the available source files.

    When ``include_curation`` is True (default), approved vision-curated
    questions stored at ``assets/mapeos/nuevas/<subject>.json`` are also
    merged into the returned Bundle.
    """
    quiz_dir = Path(quiz_html_dir) if quiz_html_dir else MAPEOS_DIR / "quiz_html"
    bundle = Bundle(matter="Cuarto grado", meta={"source": "import_existing"})

    if quiz_dir.exists():
        for html in sorted(quiz_dir.glob("*.html")):
            questions = _load_quiz_html(html)
            if questions:
                module = Module(name="Prueba 1", topics=sorted({q.topic for q in questions}))
                module.questions = questions
                _append_subject(bundle.subjects, _subject_name(html.name), module)

    if mapeo_txt is not None:
        path = Path(mapeo_txt)
    else:
        candidate = MAPEOS_DIR / "mapeo_ciencias_definitivo.txt"
        path = candidate if candidate.exists() else Path("")
    if path and path.exists():
        questions = _load_mapeo_txt(path)
        if questions:
            module = Module(name="Modulo 1", topics=sorted({q.topic for q in questions}))
            module.questions = questions
            _append_subject(bundle.subjects, "Ciencias", module)

    if include_curation:
        _merge_curation(bundle)

    _apply_default_round(bundle)

    return bundle


def _apply_default_round(bundle: Bundle) -> None:
    """Tag any question without an exam round with the default round."""
    for q in bundle.all_questions():
        if not q.round:
            q.round = DEFAULT_EXAM_ROUND


def _merge_curation(bundle: Bundle) -> None:
    """Append approved vision-curated questions from nuevas/*.json to the Bundle."""
    import json as _json

    nuevas_dir = MAPEOS_DIR / "nuevas"
    if not nuevas_dir.exists():
        return
    for path in sorted(nuevas_dir.glob("*.json")):
        subject_name = path.stem.replace("_", " ")
        try:
            proposals = _json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(proposals, dict) or not proposals:
            continue
        module = Module(name="Curado", topics=[])
        for image_name, prop in proposals.items():
            if not isinstance(prop, dict):
                continue
            pregunta = str(prop.get("pregunta", "")).strip()
            opciones = [str(o) for o in prop.get("opciones", [])]
            respuesta = str(prop.get("respuesta_correcta", "")).strip()
            if not pregunta or len(opciones) < 2 or respuesta not in opciones:
                continue
            ref = str(prop.get("imagen_referencia", image_name))
            resolved_image = _find_image(ref, subject_name)
            module.questions.append(
                Question(
                    question=pregunta,
                    options=opciones,
                    answer=respuesta,
                    explanation=str(prop.get("explicacion", "")),
                    cita_textual=str(prop.get("cita_textual", "")),
                    topic=str(prop.get("tema", "")),
                    difficulty="media",
                    imagen_referencia=ref if resolved_image else "",
                    image_path=resolved_image,
                    page=str(prop.get("pagina", "")),
                    round=str(prop.get("ronda", "")),
                )
            )
        if module.questions:
            module.topics = sorted({q.topic for q in module.questions if q.topic})
            _append_subject(bundle.subjects, subject_name, module)


def _append_subject(subjects: list[Matter], name: str, module: Module) -> None:
    """Add a module to an existing subject or create a new subject."""
    for matter in subjects:
        if matter.name == name:
            matter.modules.append(module)
            return
    subjects.append(Matter(name=name, modules=[module]))


def iter_questions(bundle: Bundle) -> Iterable[Question]:
    return bundle.all_questions()
