"""
Tape file parser.

Tape format (YAML):

    size: [110, 30]       # terminal cols × rows (default: 120 × 30)
    gif_width: 900        # output GIF pixel width (default: 900)
    app_args: {}          # kwargs passed to the AppClass constructor

    steps:
      - sleep: 3.0        # wait N seconds (float)
        capture: 2000     # also capture a frame, hold it N ms in the GIF

      - press: a          # press a single key
        sleep: 0.4
        capture: 1200

      - type: "hello"     # type a string character by character
        sleep: 0.1

      - capture: 800      # capture without any other action

`sleep` and `capture` may appear together on any step.
If `capture` is omitted, the step performs its action without grabbing a frame.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Step:
    press: str | None = None       # single key name  e.g. "a", "space", "enter"
    type: str | None = None        # string to type
    sleep: float = 0.0             # seconds to wait after action
    capture: int | None = None     # ms to hold this frame in the GIF (None = no capture)


@dataclass
class Tape:
    size: tuple[int, int] = (120, 30)
    gif_width: int = 900
    app_args: dict[str, Any] = field(default_factory=dict)
    steps: list[Step] = field(default_factory=list)


def load(path: str | Path) -> Tape:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    size = tuple(data.get("size", [120, 30]))
    gif_width = int(data.get("gif_width", 900))
    app_args = data.get("app_args") or {}

    steps = []
    for raw in data.get("steps", []):
        steps.append(Step(
            press=raw.get("press"),
            type=raw.get("type"),
            sleep=float(raw.get("sleep", 0.0)),
            capture=int(raw["capture"]) if "capture" in raw else None,
        ))

    return Tape(size=size, gif_width=gif_width, app_args=app_args, steps=steps)


def default_tape() -> Tape:
    """A sensible single-capture default — just loads the app and grabs a screenshot."""
    return Tape(steps=[Step(sleep=2.0, capture=3000)])
