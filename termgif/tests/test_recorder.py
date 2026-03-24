"""Integration test: record a minimal Textual app and verify SVG frames are produced."""

import textwrap
import tempfile
from pathlib import Path

import pytest

from termgif.tape import Tape, Step
from termgif.recorder import record


_SIMPLE_APP = textwrap.dedent("""\
    from textual.app import App, ComposeResult
    from textual.widgets import Label

    class HelloApp(App):
        def compose(self) -> ComposeResult:
            yield Label("hello from termgif")
""")


@pytest.fixture
def simple_app_file(tmp_path):
    f = tmp_path / "hello.py"
    f.write_text(_SIMPLE_APP, encoding="utf-8")
    return f


def test_record_single_frame(simple_app_file):
    tape = Tape(
        size=(40, 10),
        steps=[Step(sleep=0.5, capture=500)],
    )
    frames = record(f"{simple_app_file}:HelloApp", tape)
    assert len(frames) == 1
    svg, hold = frames[0]
    assert hold == 500
    assert "<svg" in svg
    # Textual SVG encodes spaces as &#160; (non-breaking space)
    assert "hello" in svg and "termgif" in svg


def test_record_multiple_frames(simple_app_file):
    tape = Tape(
        size=(40, 10),
        steps=[
            Step(sleep=0.3, capture=400),
            Step(sleep=0.1, capture=200),
        ],
    )
    frames = record(f"{simple_app_file}:HelloApp", tape)
    assert len(frames) == 2


def test_record_no_capture_returns_empty(simple_app_file):
    tape = Tape(
        size=(40, 10),
        steps=[Step(press="q", sleep=0.2)],  # no capture
    )
    frames = record(f"{simple_app_file}:HelloApp", tape)
    assert frames == []
