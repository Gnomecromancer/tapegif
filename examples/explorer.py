"""
A simple directory explorer — ships as the tapegif demo app.
No external dependencies beyond Textual.

Usage:
    python examples/explorer.py [path]
    tapegif record examples/explorer.py --tape examples/demo.tape
"""
import os
import sys
from pathlib import Path
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Label, Static


def _fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _fmt_time(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


class ExplorerApp(App):
    TITLE = "tapegif explorer"
    CSS = """
    Screen { layout: vertical; }
    #path-bar {
        height: 1;
        background: $boost;
        padding: 0 1;
        color: $text-muted;
    }
    DataTable { height: 1fr; }
    """
    BINDINGS = [
        Binding("enter", "enter_dir", "Open"),
        Binding("backspace", "go_up", "Up"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, root: str = "."):
        super().__init__()
        self._cwd = Path(root).resolve()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(str(self._cwd), id="path-bar")
        yield DataTable(id="table", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        self._load()

    def _load(self) -> None:
        self.query_one("#path-bar", Static).update(str(self._cwd))
        tbl = self.query_one(DataTable)
        tbl.clear(columns=True)
        tbl.add_columns("  Name", "Size", "Modified")

        entries = []
        try:
            for p in sorted(self._cwd.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    stat = p.stat()
                    size = _fmt_size(stat.st_size) if p.is_file() else "—"
                    mtime = _fmt_time(stat.st_mtime)
                    icon = "📁 " if p.is_dir() else "   "
                    entries.append((icon + p.name, size, mtime))
                except (PermissionError, OSError):
                    entries.append(("🔒 " + p.name, "—", "—"))
        except PermissionError:
            entries.append(("(permission denied)", "", ""))

        for name, size, mtime in entries:
            tbl.add_row(name, size, mtime)

        self.title = f"tapegif explorer — {self._cwd.name}"

    def action_enter_dir(self) -> None:
        tbl = self.query_one(DataTable)
        row = tbl.cursor_row
        rows = list(tbl.get_column_at(0))
        if row >= len(rows):
            return
        name = str(rows[row]).lstrip("📁 ").lstrip("   ").lstrip("🔒 ")
        candidate = self._cwd / name
        if candidate.is_dir():
            self._cwd = candidate
            self._load()

    def action_go_up(self) -> None:
        parent = self._cwd.parent
        if parent != self._cwd:
            self._cwd = parent
            self._load()


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    ExplorerApp(root=root).run()
