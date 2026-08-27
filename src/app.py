"""Billy Web App - Streamlit dashboard (estudiante).

La app es un cliente para Billy: elige una materia y una ronda de examen,
estudia el material (active recall), practica con el quiz autocontenido y
conversa con el tutor anclado a los apuntes en un panel lateral.

Las tareas del padre (importar, verificar, regenerar y curar) se hacen desde
su propia maquina con OpenCode y el pipeline (`python -m Script.functions.pipeline`),
no desde esta app.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import streamlit.components.v1 as components

from Script.functions.config import DEFAULT_EXAM_ROUND, DELIVERABLES_DIR, EXAM_ROUNDS
from Script.functions.data_model import Bundle, load_bundle
from Script.functions.html_generator import render_subject_html
from Script.functions.import_existing import import_material
from Script.functions.llm_client import describe_llm_error, get_api_key
from Script.functions.rag import grounded_answer

st.set_page_config(page_title="Billy - Aventura de Estudio", layout="wide")


def _ensure_messages() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "tutor_subject" not in st.session_state:
        st.session_state.tutor_subject = ""
    if "tutor_round" not in st.session_state:
        st.session_state.tutor_round = ""
    if "asked_questions" not in st.session_state:
        st.session_state.asked_questions = set()


def _load_bundle() -> Bundle:
    bundle_path = DELIVERABLES_DIR / "bundle.json"
    if bundle_path.exists():
        return load_bundle(bundle_path)
    return import_material()


def _sorted_rounds(bundle: Bundle) -> list[str]:
    available = bundle.available_rounds()
    ordered = [r for r in EXAM_ROUNDS if r in available]
    ordered += [r for r in available if r not in EXAM_ROUNDS]
    return ordered or [DEFAULT_EXAM_ROUND]


def _render_quiz(subject: str, exam_round: str) -> None:
    bundle = st.session_state.bundle
    matter = next((m for m in bundle.subjects if m.name == subject), None)
    if matter is None:
        st.info("Sin contenido para esta materia.")
        return
    filtered = matter.filter_by_round(exam_round)
    if not filtered.all_questions():
        st.info("No hay preguntas de esta ronda todavia.")
        return
    components.html(render_subject_html(filtered), height=900, scrolling=True)


def _render_tutor_panel(subject: str, exam_round: str) -> None:
    _ensure_messages()
    if st.session_state.tutor_subject != subject or st.session_state.tutor_round != exam_round:
        st.session_state.messages = []
        st.session_state.asked_questions = set()
        st.session_state.tutor_subject = subject
        st.session_state.tutor_round = exam_round

    st.markdown("### Tutor")
    st.caption(
        "Pregunta lo que no entiendas sobre esta materia. Responde solo con "
        "lo que esta en tus apuntes."
    )

    if not get_api_key():
        st.warning("La API key del tutor no esta configurada.")
        return

    filtered_bundle = st.session_state.bundle.filter_by_round(exam_round)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.button("No entiendo, ayuda con la materia", key="tutor_help_subject"):
        prompt = f"Expliqueme con palabras sencillas los temas principales de {subject}."
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        try:
            history = st.session_state.messages[:-1][-6:]
            answer = grounded_answer(
                prompt,
                filtered_bundle,
                asked=st.session_state.asked_questions,
                history=history,
            )
        except Exception as exc:  # noqa: BLE001
            answer = describe_llm_error(exc)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.rerun()

    prompt = st.chat_input("Pregunta algo sobre " + subject, key="tutor_input")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        try:
            history = st.session_state.messages[:-1][-6:]
            answer = grounded_answer(
                prompt,
                filtered_bundle,
                asked=st.session_state.asked_questions,
                history=history,
            )
        except Exception as exc:  # noqa: BLE001
            answer = describe_llm_error(exc)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.rerun()


def main() -> None:
    if "bundle" not in st.session_state:
        st.session_state.bundle = _load_bundle()

    subjects = [m.name for m in st.session_state.bundle.subjects]
    if not subjects:
        st.warning("No hay ninguna materia importada todavia.")
        return

    st.header("Aventura de Estudio")
    subject = st.selectbox("Materia", subjects, key="billy_subject")
    exam_round = st.selectbox(
        "Ronda de examen", _sorted_rounds(st.session_state.bundle), key="billy_round"
    )
    quiz_col, tutor_col = st.columns([2, 1])
    with quiz_col:
        _render_quiz(subject, exam_round)
    with tutor_col:
        _render_tutor_panel(subject, exam_round)


if __name__ == "__main__":
    main()
