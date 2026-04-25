import os  # used to read the PORT environment variable set by Render
from fastapi import FastAPI, HTTPException  # FastAPI is the web framework; HTTPException lets us return error responses
from fastapi.staticfiles import StaticFiles  # serves the public/ folder (HTML, CSS) as static files
from pydantic import BaseModel  # BaseModel validates and parses incoming JSON request bodies automatically
import uvicorn  # ASGI server that actually runs the FastAPI app

# import all matchmaking functions — these handle queuing, game state, moves, and cleanup
from matchmaking import add_to_queue, make_move as _make_move, get_game_state, remove_player

app = FastAPI(title="Wordle API")  # create the FastAPI application instance; title appears in auto-generated docs


# ── request body schemas ───────────────────────────────────────────────────────
# Pydantic models below define the shape of JSON bodies the client must send.
# FastAPI validates incoming requests against these models automatically.

class FindGameRequest(BaseModel):
    player_id: str  # unique ID the client generated for itself (via crypto.randomUUID in the browser)

class MakeMoveRequest(BaseModel):
    player_id: str  # identifies which player is submitting the guess
    guess: str      # the 5-letter word the player is guessing


# ── API routes ─────────────────────────────────────────────────────────────────
# These must be registered BEFORE the static file mount below.
# FastAPI checks its own routes first; the static mount is a catch-all fallback.

@app.post("/api/find-game")
async def find_game(req: FindGameRequest):
    # add this player to the matchmaking queue;
    # returns {"status": "waiting"} or {"status": "game_started", "game_id": "..."}
    return add_to_queue(req.player_id)


@app.post("/api/move")
async def move(req: MakeMoveRequest):
    result = _make_move(req.player_id, req.guess)  # apply the guess to the player's active game
    if result is None:
        # player_id doesn't map to any game — they may not have found a match yet
        raise HTTPException(status_code=404, detail="No active game for this player")
    if not result.get("valid"):
        # move was rejected (wrong length, game already over, etc.) — tell the client why
        raise HTTPException(status_code=400, detail=result.get("reason", "invalid move"))
    return result  # success: return tile results, opponent grid, and game-over state


@app.get("/api/game/{player_id}")
async def game_state(player_id: str):
    # called by the client every 1.5 s during a game to:
    #   1. detect when an opponent has joined (while in the waiting queue)
    #   2. see the opponent's latest coloured grid during gameplay
    state = get_game_state(player_id)
    if state is None:
        # no game found for this player — they haven't been matched yet or their game was cleaned up
        raise HTTPException(status_code=404, detail="No active game for this player")
    return state  # personalised state: own guesses + opponent grid (colours only)


@app.delete("/api/player/{player_id}")
async def leave_game(player_id: str):
    # called when a player closes the tab or intentionally leaves;
    # removes them from the queue or their active game and cleans up server memory
    return remove_player(player_id)


# ── static file mount ──────────────────────────────────────────────────────────
# Mount the public/ folder at the root path so index.html, style.css, etc. are served directly.
# This must come LAST — it's a catch-all that handles any path not matched by the API routes above.
app.mount("/", StaticFiles(directory="public", html=True), name="static")


# ── entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # read the PORT env var — Render sets this automatically (default 10000);
    # fall back to 10000 locally if PORT is not set
    port = int(os.environ.get("PORT", 10000))
    # bind to 0.0.0.0 so Render's router can reach the process from outside the container;
    # localhost would only accept connections from inside the machine and would time out on Render
    uvicorn.run("server:app", host="0.0.0.0", port=port)
