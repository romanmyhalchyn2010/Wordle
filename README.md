# Wordle

A multiplayer Wordle game with a Python backend and browser-based frontend.

## Structure

- `public/` — static web client (HTML, CSS)
- `game.py` — core game logic
- `server.py` — WebSocket/HTTP server
- `matchmaking.py` — player matchmaking
- `client.py` — Python test client

## Setup

```bash
pip install -r requirements.txt
python server.py
```

Then open `public/index.html` in a browser.
