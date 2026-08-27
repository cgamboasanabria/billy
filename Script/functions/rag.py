"""Retrieval-augmented generation for the grounded tutor.

The knowledge base is built strictly from the official content: each question
carries its citation and explanation. Retrieval is keyword based (stdlib only)
over that corpus. The generation prompt forces the model to answer only from
the provided context and to abstain when the answer is not present.
"""

from __future__ import annotations

import random
import re
import sys
from dataclasses import dataclass

from Script.functions.data_model import Bundle

_STOPWORDS = {
    "de",
    "la",
    "el",
    "los",
    "las",
    "que",
    "un",
    "una",
    "unos",
    "unas",
    "y",
    "o",
    "a",
    "en",
    "con",
    "por",
    "para",
    "del",
    "al",
    "es",
    "son",
    "se",
    "no",
    "como",
    "cuando",
    "donde",
    "cual",
    "cuales",
    "porque",
    "de",
    "los",
}


@dataclass
class Chunk:
    text: str
    topic: str
    answer: str


def _normalize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9\u00c0-\u024f]+", text.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 2]


def build_corpus(bundle: Bundle) -> list[Chunk]:
    """Turn every question into a chunk: question + answer + citation."""
    chunks: list[Chunk] = []
    for q in bundle.all_questions():
        parts = [q.question, q.answer, q.cita_textual, q.explanation]
        if q.page:
            parts.append(f"pagina {q.page}")
        chunks.append(Chunk(text=" ".join(p for p in parts if p), topic=q.topic, answer=q.answer))
    return chunks


def retrieve(query: str, corpus: list[Chunk], top_k: int = 3) -> list[Chunk]:
    """Return the most relevant chunks by keyword overlap score."""
    query_terms = set(_normalize(query))
    if not query_terms:
        return corpus[:top_k]
    scored = []
    for chunk in corpus:
        terms = set(_normalize(chunk.text))
        score = len(query_terms & terms)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


def grounded_answer(
    query: str, bundle: Bundle, top_k: int = 3, asked: set[str] | None = None
) -> str:
    """Answer a study question only from the official content, else abstain.

    When the query has no keyword overlap with the round corpus, instead of
    abstaining the tutor proactively asks a reworded question from the same
    round, so the child keeps practicing on-topic material.
    """
    from Script.functions.llm_client import tutor_answer

    corpus = build_corpus(bundle)
    chunks = retrieve(query, corpus, top_k=top_k)
    if not chunks:
        return proactive_question(bundle, asked)
    context = "\n\n".join(f"- Tema: {c.topic}\n  {c.text.strip()}" for c in chunks)
    if not context:
        context = "(no hay contenido disponible)"

    system = (
        "Eres un tutor amable para un nino de cuarto grado de Costa Rica. "
        "Ensenas EXCLUSIVAMENTE con la informacion oficial que te dan en el contexto. "
        "Si la respuesta no aparece en el contexto, di exactamente: 'Eso no esta en "
        "tus apuntes todavia.'. Nunca inventes datos, fechas ni nombres. Responde "
        "en espanol sencillo, corto y claro, y al final indica de que tema salio la "
        "respuesta."
    )
    user = f"CONTEXTO OFICIAL:\n{context}\n\nPREGUNTA DEL ESTUDIANTE:\n{query}"
    return tutor_answer(system, user)


_REPHRASE_SYSTEM = (
    "Eres un tutor amable para un nino de cuarto grado de Costa Rica. "
    "Reescribe la pregunta que te doy con otras palabras, pensada de forma "
    "distinta pero con el mismo significado. No incluyas la respuesta ni ninguna "
    "pista sobre ella. Escribe solo la pregunta reformulada, en espanol sencillo."
)


def proactive_question(bundle: Bundle, asked: set[str] | None = None) -> str:
    """Ask a reworded question from the round, rotating without repeats.

    ``asked`` holds the original question texts already posed this session; it
    is mutated in place and reset once the whole round has been covered.
    """
    from Script.functions.llm_client import tutor_answer

    if asked is None:
        asked = set()
    pool = [
        q for q in bundle.all_questions() if q.question and q.answer and q.question not in asked
    ]
    if not pool:
        asked.clear()
        pool = [q for q in bundle.all_questions() if q.question and q.answer]
    if not pool:
        return "No tengo preguntas de esta ronda todavia."

    question = random.choice(pool)
    asked.add(question.question)
    try:
        rephrased = tutor_answer(_REPHRASE_SYSTEM, question.question)
    except Exception as exc:  # noqa: BLE001
        print(f"[Billy tutor] error al reformular pregunta: {exc}", file=sys.stderr)
        rephrased = question.question
    return f"Eso no esta en tus apuntes todavia. Mejor te pregunto: {rephrased}"
