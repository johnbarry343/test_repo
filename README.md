# Block Stacker Game

This repository contains a classic block stacking game (similar to Tetris) implemented in Python.
It features:
- Core Tetris-like gameplay mechanics.
- A "bag" system for fair block distribution.
- Progressive difficulty.
- A "Slow Fall" special ability.
- Unit tests for core logic.

## Play Web Version

You can play a web-based version of this game directly in your browser using Pyodide for Python execution and HTML Canvas for rendering.

**Click here to play:**
[Play Block Stacker Game in Browser](https://htmlpreview.github.io/?https://raw.githubusercontent.com/johnbarry343/test_repo/text-based-block-stacker/index.html)

**Notes:**
- The link above uses the `htmlpreview.github.io` service to render the `index.html` file directly from this GitHub repository.
- This link points to the `text-based-block-stacker` branch of the `johnbarry343/test_repo` repository. If you are viewing this README from a different fork or branch, or if `index.html` is on a different branch, you may need to adjust the link accordingly.
- Alternatively, you can run the game locally:
    1. Clone this repository: `git clone <repository_url>`
    2. Navigate to the project's root directory: `cd <repository_name>`
    3. Start a simple HTTP server: `python -m http.server` (for Python 3) or `python -m SimpleHTTPServer` (for Python 2).
    4. Open `http://localhost:8000/index.html` (or the appropriate port shown by the server) in your web browser.

## Console Version
The original console version can be run by executing `main.py`:
```bash
python main.py
```

Enjoy the game!
