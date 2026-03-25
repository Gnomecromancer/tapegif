"""
tapegif CLI entry point.

Usage:
    tapegif record path/to/app.py [--tape demo.tape] [--output demo.gif]
    tapegif init                          # scaffold a demo.tape in the current directory
"""

from __future__ import annotations
import sys
from pathlib import Path

import click

from . import recorder, renderer
from .tape import Tape, load as load_tape, default_tape


_INIT_TAPE = """\
# tapegif tape — edit to match your app's interactions.
# Run with: tapegif record path/to/yourapp.py --tape demo.tape

size: [120, 30]       # terminal cols × rows
gif_width: 900        # output GIF width in pixels
app_args: {}          # kwargs passed to your App constructor, e.g. {root: "/tmp"}

steps:
  # Wait for the app to fully load, then capture the initial state
  - sleep: 3.0
    capture: 2000     # hold this frame for 2 seconds in the GIF

  # Example interactions — uncomment and modify as needed:
  # - press: a        # press a key
  #   sleep: 0.4
  #   capture: 1200

  # - type: "hello"   # type a string
  #   sleep: 0.5
  #   capture: 1000

  # - press: "ctrl+c"
  #   sleep: 0.2
  #   capture: 800
"""


@click.group()
def main():
    """tapegif — record animated GIFs of Textual apps."""


@main.command()
@click.argument("app_spec", metavar="APP")
@click.option(
    "--tape", "-t",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to a .tape YAML file. Defaults to a single-capture snapshot.",
)
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output .gif path. Defaults to demo.gif in the current directory.",
)
@click.option(
    "--width", "-w",
    type=int,
    default=None,
    help="Override GIF pixel width (default comes from tape or 900).",
)
def record(app_spec: str, tape: Path | None, output: Path | None, width: int | None):
    """
    Record APP to an animated GIF.

    APP is path/to/file.py (auto-discovers App subclass) or path/to/file.py:ClassName.

    \b
    Examples:
        tapegif record myapp.py
        tapegif record myapp.py --tape demo.tape --output my_demo.gif
        tapegif record myapp.py:MyApp --width 1200
    """
    tape_obj: Tape = load_tape(tape) if tape else default_tape()
    if width is not None:
        tape_obj.gif_width = width

    out = output or Path("demo.gif")

    click.echo(f"recording {app_spec} …")
    try:
        frames = recorder.record(app_spec, tape_obj)
    except Exception as e:
        click.echo(f"error during recording: {e}", err=True)
        sys.exit(1)

    if not frames:
        click.echo("no frames captured — check that your tape has capture: steps", err=True)
        sys.exit(1)

    click.echo(f"rendering {len(frames)} frame(s) …")
    try:
        result = renderer.render(frames, out, gif_width=tape_obj.gif_width)
    except Exception as e:
        click.echo(f"error during rendering: {e}", err=True)
        sys.exit(1)

    size_kb = result.stat().st_size // 1024
    click.echo(f"saved {result} ({len(frames)} frames, {size_kb} KB)")


@main.command()
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("demo.tape"),
    show_default=True,
    help="Where to write the scaffold tape file.",
)
def init(output: Path):
    """Scaffold a demo.tape file in the current directory."""
    if output.exists():
        click.confirm(f"{output} already exists. Overwrite?", abort=True)
    output.write_text(_INIT_TAPE, encoding="utf-8")
    click.echo(f"wrote {output}")
    click.echo(f"edit it, then run: tapegif record path/to/yourapp.py --tape {output}")
