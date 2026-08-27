"""Cross-check the coherence of each Question.

The verifier flags questions whose content is inconsistent with the original
requirement: answer must belong to the options, a textual citation must exist,
a reference image must be present and resolvable, and a topic must be set so the
quiz can retry the same theme on failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from Script.functions.data_model import Bundle, Question

ALLOWED_DIFFICULTY = {"baja", "media", "alta"}


@dataclass
class Issue:
    level: str
    message: str
    question: str = ""


@dataclass
class VerificationReport:
    total: int = 0
    ok: int = 0
    issues: list[Issue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.level == "error" for i in self.issues)

    def summary(self) -> str:
        errors = sum(1 for i in self.issues if i.level == "error")
        warnings = sum(1 for i in self.issues if i.level == "warn")
        return f"total={self.total} ok={self.ok} errors={errors} warnings={warnings}"


def _check_question(q: Question, index: int, subject: str = "") -> list[Issue]:
    issues: list[Issue] = []
    label = f"[{index}] {q.question[:60]}"

    if not q.question.strip():
        issues.append(Issue("error", "pregunta vacia", label))

    if not q.options or len(q.options) < 2:
        issues.append(Issue("error", "requiere al menos 2 opciones", label))
    elif not q.answer or q.answer not in q.options:
        issues.append(Issue("error", "la respuesta no esta en las opciones", label))
    elif q.options.count(q.answer) > 1:
        issues.append(Issue("error", "respuesta duplicada en las opciones", label))

    if not q.cita_textual.strip():
        issues.append(Issue("warn", "sin cita textual", label))
    if not q.topic.strip():
        issues.append(Issue("warn", "sin tema", label))
    if q.difficulty not in ALLOWED_DIFFICULTY:
        issues.append(Issue("warn", f"dificultad invalida: {q.difficulty}", label))

    if not q.imagen_referencia:
        issues.append(Issue("warn", "sin imagen de referencia", label))
    elif not q.image_path:
        issues.append(Issue("error", "imagen de referencia no resuelta", label))
    elif not Path(q.image_path).exists():
        issues.append(Issue("error", "el archivo de la imagen no existe", label))
    elif subject and _subject_slug(subject) not in Path(q.image_path).parts:
        issues.append(
            Issue(
                "error",
                f"imagen de otra materia (esperada '{_subject_slug(subject)}')",
                label,
            )
        )

    return issues


def _subject_slug(name: str) -> str:
    """Map a canonical subject name to its slug for image-path checks."""
    from Script.functions.import_existing import _subject_slug as _slug

    return _slug(name)


def verify_bundle(bundle: Bundle) -> VerificationReport:
    report = VerificationReport()
    for matter in bundle.subjects:
        for question in matter.all_questions():
            report.total += 1
            issues = _check_question(question, report.total, matter.name)
            if issues:
                report.issues.extend(issues)
            else:
                report.ok += 1
    return report


def filter_ready(questions: list[Question]) -> list[Question]:
    """Keep only questions with no error-level issues (warnings are ok)."""
    ready: list[Question] = []
    for i, q in enumerate(questions, start=1):
        if not any(issue.level == "error" for issue in _check_question(q, i)):
            ready.append(q)
    return ready
