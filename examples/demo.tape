# tapegif demo tape — records the explorer.py example app.
# Run from the repo root:
#   tapegif record examples/explorer.py --tape examples/demo.tape --output demo.gif

size: [100, 28]
gif_width: 900
app_args:
  root: "."

steps:
  # Initial load — show the project root
  - sleep: 4.0
    capture: 1800

  # Navigate down a few rows
  - press: down
    sleep: 0.15
  - press: down
    sleep: 0.15
  - press: down
    sleep: 0.15
    capture: 900

  # Navigate back up
  - press: up
    sleep: 0.15
  - press: up
    sleep: 0.15
    capture: 800

  # Open the first directory (cursor is on row 1; go back to row 0 — first dir)
  - press: up
    sleep: 0.15
  - press: enter
    sleep: 0.6
    capture: 1200

  # Go back up to project root
  - press: backspace
    sleep: 0.4
    capture: 1000

  # Final hold
  - sleep: 0.1
    capture: 1500
