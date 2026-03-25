# tapegif

Records animated GIFs of Textual terminal apps using the Pilot API + Playwright + Pillow.

## Package names
- PyPI distribution: `tapegif`
- Python import package: `termgif` (rename to `tapegif` is a future TODO — non-trivial, requires bumping all imports in tapegif-pro too)
- CLI command: `tapegif`
- GitHub repo: gnomecromancer/tapegif

## Build & test
```
python -m pytest termgif/tests/ -v        # 9 tests, ~2s
python -m build                            # dist/tapegif-*.whl
```

## Publish
```
TWINE_USERNAME=__token__ TWINE_PASSWORD=$(cat ~/.claude/pypi_token.txt) python -m twine upload dist/*
```

## Key design decisions & gotchas
- **SVG rendering bug**: Rich/Textual SVGs have `viewBox` but NO `width`/`height` attrs.
  Playwright defaults to 0×0 viewport → all-white screenshots.
  Fix: parse viewBox from SVG string BEFORE calling `page.goto()`. Setting viewport after load doesn't trigger reflow.
  Same fix applies in: `renderer.py`, `tapegif_pro/formats.py`, `tapegif_pro/cli.py` (preview cmd).

- **HTML template**: Must use `display: block` on `svg` and `background: #000` on body.
  `display: inline-block` + `background: transparent` collapses the SVG layout in Playwright.

- **Auto-discovery**: When no `:ClassName` given, scans module vars for App subclasses.
  Errors on 0 or 2+ candidates. Relative paths are fine; absolute paths on Windows hit `:` in drive letter
  if using `rsplit(":", 1)` — current code branches on `.py` extension first to avoid this.

- **YAML app_args**: Always strings from YAML. If App.__init__ takes a Path argument,
  coerce in the constructor (`self.root = Path(root)`), not in the tape loader.

- **Tape file**: `app_args` is passed as `**kwargs` to `AppClass(**tape.app_args)`.

- **tests/test_tape.py**: `test_bad_spec_no_colon` was removed when auto-discovery was added.
  The old test expected `ValueError("App spec must be")` which no longer fires.
