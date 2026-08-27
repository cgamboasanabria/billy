"""Data model for Billy study content.

A document tree of Bundle (a shareable update unit) -> Matter -> Module ->
Question. Each question carries the answer, an explanation, the textual
citation, the reference image, and a topic used for the retry-on-fail quiz
logic and for grounding the tutor.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Question:
    """A single study question."""

    question: str
    options: list[str]
    answer: str
    explanation: str = ""
    cita_textual: str = ""
    topic: str = ""
    difficulty: str = "media"
    imagen_referencia: str = ""
    image_path: str = ""
    page: str = ""
    round: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Question:
        return cls(
            question=str(data.get("question", "")),
            options=list(data.get("options", [])),
            answer=str(data.get("answer", "")),
            explanation=str(data.get("explanation", "")),
            cita_textual=str(data.get("cita_textual", "")),
            topic=str(data.get("topic", "")),
            difficulty=str(data.get("difficulty", "media")),
            imagen_referencia=str(data.get("imagen_referencia", "")),
            image_path=str(data.get("image_path", "")),
            page=str(data.get("page", "")),
            round=str(data.get("round", "")),
        )


@dataclass
class Module:
    """A group of questions (a chapter or a set of topics)."""

    name: str
    topics: list[str] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "topics": list(self.topics),
            "questions": [q.to_dict() for q in self.questions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Module:
        return cls(
            name=str(data.get("name", "")),
            topics=list(data.get("topics", [])),
            questions=[Question.from_dict(q) for q in data.get("questions", [])],
        )

    def all_questions(self) -> list[Question]:
        return list(self.questions)


@dataclass
class Matter:
    """A school subject (Ciencias, Espanol, ...)."""

    name: str
    modules: list[Module] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "modules": [m.to_dict() for m in self.modules]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Matter:
        return cls(
            name=str(data.get("name", "")),
            modules=[Module.from_dict(m) for m in data.get("modules", [])],
        )

    def all_questions(self) -> list[Question]:
        return [q for m in self.modules for q in m.all_questions()]

    def filter_by_round(self, round: str) -> Matter:
        """Return a copy of this subject with only the questions of one round."""
        modules: list[Module] = []
        for m in self.modules:
            questions = [q for q in m.all_questions() if q.round == round]
            if questions:
                modules.append(
                    Module(
                        name=m.name,
                        topics=sorted({q.topic for q in questions if q.topic}),
                        questions=questions,
                    )
                )
        return Matter(name=self.name, modules=modules)


@dataclass
class Bundle:
    """The shareable update unit delivered to Billy.

    ``meta`` holds arbitrary metadata (source folder, generated_at,
    curriculum notes) so future content rounds are just a new bundle.
    """

    matter: str
    meta: dict[str, Any] = field(default_factory=dict)
    subjects: list[Matter] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter": self.matter,
            "meta": dict(self.meta),
            "subjects": [s.to_dict() for s in self.subjects],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Bundle:
        return cls(
            matter=str(data.get("matter", "")),
            meta=dict(data.get("meta", {})),
            subjects=[Matter.from_dict(s) for s in data.get("subjects", [])],
        )

    def all_questions(self) -> list[Question]:
        return [q for s in self.subjects for m in s.modules for q in m.questions]

    def available_rounds(self) -> list[str]:
        """Return the distinct exam rounds present, in first-seen order."""
        rounds: list[str] = []
        for q in self.all_questions():
            if q.round and q.round not in rounds:
                rounds.append(q.round)
        return rounds

    def filter_by_round(self, round: str) -> Bundle:
        """Return a copy of this bundle with only the questions of one round."""
        subjects = [s.filter_by_round(round) for s in self.subjects]
        subjects = [s for s in subjects if s.all_questions()]
        return Bundle(matter=self.matter, meta=dict(self.meta), subjects=subjects)


def save_bundle(bundle: Bundle, path: str | Path) -> Path:
    """Write a bundle to disk as JSON and return the resolved path."""
    import json

    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(bundle.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def load_bundle(path: str | Path) -> Bundle:
    """Read a bundle back from a JSON file."""
    import json

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Bundle.from_dict(data)
