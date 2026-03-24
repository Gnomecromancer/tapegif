"""
Drive a Textual app with the Pilot API, capture SVG frames at specified steps.
Returns a list of (svg_str, hold_ms) pairs ready for rendering.
"""

from __future__ import annotations
import asyncio
import importlib.util
import sys
from pathlib import Path
from typing import Type

from textual.app import App

from .tape import Tape, Step


def _load_app_class(spec: str) -> Type[App]:
    """
    Load an App subclass from a file path spec.

    Formats accepted:
        path/to/app.py              (auto-discovers the single App subclass)
        path/to/app.py:ClassName    (explicit class name)
        mypackage.module:ClassName  (dotted import path, no .py extension)
    """
    if ":" in spec:
        source, class_name = spec.rsplit(":", 1)
    else:
        source, class_name = spec, None

    if source.endswith(".py") or "/" in source or "\\" in source:
        # File path
        file_path = Path(source).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"App file not found: {file_path}")
        mod_spec = importlib.util.spec_from_file_location("_tapegif_app", file_path)
        module = importlib.util.module_from_spec(mod_spec)
        # Add the file's directory to sys.path so relative imports work
        src_dir = str(file_path.parent)
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        mod_spec.loader.exec_module(module)
    else:
        # Dotted module path
        module = importlib.import_module(source)

    if class_name is None:
        # Auto-discover: find all App subclasses defined in this module
        candidates = [
            v for v in vars(module).values()
            if isinstance(v, type) and issubclass(v, App) and v is not App
        ]
        if not candidates:
            raise ValueError(f"No App subclass found in {source!r}")
        if len(candidates) > 1:
            names = [cls.__name__ for cls in candidates]
            raise ValueError(
                f"Multiple App subclasses in {source!r}: {names}. "
                f"Specify one: {source}:ClassName"
            )
        return candidates[0]

    cls = getattr(module, class_name, None)
    if cls is None:
        raise AttributeError(f"Class {class_name!r} not found in {source!r}")
    if not (isinstance(cls, type) and issubclass(cls, App)):
        raise TypeError(f"{class_name!r} is not a Textual App subclass")
    return cls


async def _record(app: App, tape: Tape) -> list[tuple[str, int]]:
    frames: list[tuple[str, int]] = []

    async with app.run_test(size=tape.size) as pilot:
        for step in tape.steps:
            if step.type is not None:
                await pilot.press(*list(step.type))
            if step.press is not None:
                await pilot.press(step.press)
            if step.sleep > 0:
                await pilot.pause(step.sleep)
            if step.capture is not None:
                frames.append((app.export_screenshot(), step.capture))

    return frames


def record(app_spec: str, tape: Tape) -> list[tuple[str, int]]:
    """
    Load the app class from *app_spec*, drive it with *tape*, return frames.

    Each frame is (svg_str, hold_ms).
    """
    AppClass = _load_app_class(app_spec)
    app = AppClass(**tape.app_args)
    return asyncio.run(_record(app, tape))
