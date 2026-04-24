# Wordle — Claude Code project notes

## Overview
Multiplayer Wordle game. Python backend (server.py, game.py, matchmaking.py), browser frontend (public/), and a headless Python client (client.py).

## Key files
- `game.py` — game rules and guess evaluation
- `server.py` — server entry point
- `matchmaking.py` — lobby/queue logic
- `client.py` — test client
- `public/index.html` + `public/style.css` — web frontend

## Dev
```bash
pip install -r requirements.txt
python server.py
```
