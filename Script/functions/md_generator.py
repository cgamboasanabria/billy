"""Generate a static Markdown study guide from a subject's questions.

This is the offline review document: a list of questions with answers and the
textual citation, grouped by topic.
"""

from __future__ import annotations

from pathlib import Path

from Script.functions.data_model import Matter


def generate_subject_md(matter: Matter, output_path: str | Path) -> Path:
    """Write the Markdown guide for a subject and return its path."""
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    topics: dict[str, list] = {}
    for q in matter.all_questions():
        topics.setdefault(q.topic or "General", []).append(q)

    lines: list[str] = [f"# Guia de Estudio: {matter.name}", ""]
    counter = 1
    for topic, questions in topics.items():
        lines.append(f"## {topic}")
        lines.append("")
        for q in questions:
            lines.append(f"**{counter}. {q.question}**")
            lines.append(f"*   **Respuesta:** {q.answer}")
            if q.explanation:
                lines.append(f"*   **Explicacion:** {q.explanation}")
            if q.cita_textual:
                lines.append(f'*   **Cita textual:** "{q.cita_textual}"')
            lines.append("")
            counter += 1

    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest
