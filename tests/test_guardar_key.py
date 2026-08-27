"""Tests for the key-storing script (direct argument and interactive fallback)."""

import sys

from Script import guardar_key


def test_guardar_key_direct_arg(monkeypatch, capsys):
    captured = {}

    def fake_store(key):
        captured["key"] = key

    monkeypatch.setattr(guardar_key, "store_api_key", fake_store)
    monkeypatch.setattr(sys, "argv", ["guardar_key.py", "  sk-abc123  "])
    guardar_key.main()
    assert captured["key"] == "sk-abc123"
    assert "guardada" in capsys.readouterr().out


def test_guardar_key_empty_arg_skips(monkeypatch, capsys):
    called = []

    def fake_store(key):
        called.append(key)

    monkeypatch.setattr(guardar_key, "store_api_key", fake_store)
    monkeypatch.setattr(sys, "argv", ["guardar_key.py", "   "])
    guardar_key.main()
    assert called == []
    assert "No se guardo" in capsys.readouterr().out


def test_guardar_key_interactive_fallback(monkeypatch):
    captured = {}

    def fake_store(key):
        captured["key"] = key

    monkeypatch.setattr(guardar_key, "store_api_key", fake_store)
    monkeypatch.setattr(guardar_key.getpass, "getpass", lambda prompt: "sk-interactive")
    monkeypatch.setattr(sys, "argv", ["guardar_key.py"])
    guardar_key.main()
    assert captured["key"] == "sk-interactive"


def test_guardar_key_runtime_error_warns(monkeypatch, capsys):
    def boom(key):
        raise RuntimeError("no persiste")

    monkeypatch.setattr(guardar_key, "store_api_key", boom)
    monkeypatch.setattr(sys, "argv", ["guardar_key.py", "sk-x"])
    guardar_key.main()
    assert "ADVERTENCIA" in capsys.readouterr().out
