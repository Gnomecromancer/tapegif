"""Tests for tape.py — no Textual or Playwright required."""

import textwrap
import tempfile
from pathlib import Path

import pytest

from termgif.tape import load, default_tape, Tape, Step


def _write_tape(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        suffix=".tape", delete=False, mode="w", encoding="utf-8"
    )
    f.write(textwrap.dedent(content))
    f.close()
    return Path(f.name)


def test_default_tape():
    t = default_tape()
    assert isinstance(t, Tape)
    assert len(t.steps) == 1
    assert t.steps[0].capture == 3000


def test_load_minimal():
    path = _write_tape("""\
        steps:
          - sleep: 2.0
            capture: 1000
    """)
    t = load(path)
    assert t.size == (120, 30)
    assert t.gif_width == 900
    assert len(t.steps) == 1
    assert t.steps[0].sleep == 2.0
    assert t.steps[0].capture == 1000


def test_load_full():
    path = _write_tape("""\
        size: [110, 25]
        gif_width: 1200
        app_args:
          root: /tmp
          older_than: 30

        steps:
          - sleep: 3.0
            capture: 2000
          - press: a
            sleep: 0.4
            capture: 1200
          - type: "hello"
            sleep: 0.1
          - capture: 800
    """)
    t = load(path)
    assert t.size == (110, 25)
    assert t.gif_width == 1200
    assert t.app_args == {"root": "/tmp", "older_than": 30}
    assert len(t.steps) == 4
    assert t.steps[1].press == "a"
    assert t.steps[2].type == "hello"
    assert t.steps[2].capture is None
    assert t.steps[3].capture == 800


def test_load_no_capture_steps():
    path = _write_tape("""\
        steps:
          - press: a
            sleep: 0.5
          - press: b
    """)
    t = load(path)
    assert all(s.capture is None for s in t.steps)


def test_bad_spec_missing_file():
    from termgif.recorder import _load_app_class
    with pytest.raises(FileNotFoundError):
        _load_app_class("/nonexistent/app.py:MyApp")


def test_bad_spec_missing_file_no_colon():
    from termgif.recorder import _load_app_class
    with pytest.raises(FileNotFoundError):
        _load_app_class("/nonexistent/app.py")
