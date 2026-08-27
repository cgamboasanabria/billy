"""Tests for the Streamlit app layout (Billy student view).

The self-contained quiz HTML already carries its own "Estudiar"/"Practicar"
tabs, so the Streamlit layer must not duplicate them. These tests assert the
external "Estudiar" tab is gone and that the subject selector plus the
quiz/tutor columns still render.
"""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

_APP_PATH = Path(__file__).resolve().parent.parent / "src" / "app.py"


def _run_app() -> AppTest:
    return AppTest.from_file(_APP_PATH, default_timeout=120).run()


def test_app_has_no_external_tabs():
    """The Streamlit layer no longer exposes Estudiar/Practicar tabs."""
    at = _run_app()
    assert not at.exception
    assert list(at.tabs) == []


def test_app_renders_subject_selector_and_tutor():
    """Billy still picks a subject and sees the tutor side panel."""
    at = _run_app()
    assert not at.exception
    assert any(sb.key == "billy_subject" for sb in at.selectbox)
    assert any(md.value.startswith("### Tutor") for md in at.markdown)


def test_app_renders_round_selector():
    """The exam round selector is present and defaults to the current round."""
    at = _run_app()
    assert not at.exception
    round_boxes = [sb for sb in at.selectbox if sb.key == "billy_round"]
    assert len(round_boxes) == 1
    assert round_boxes[0].value == "marzo 2026"
