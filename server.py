from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from matchmaking import add_to_queue, make_move as _make_move, get_game_state, remove_player

app = FastAPI(title="Wordle API")


# ── request bodies ────────────────────────────────────────────────────────────

class FindGameRequest(BaseModel):
    player_id: str

class MakeMoveRequest(BaseModel):
    player_id: str
    guess: str


# ── API routes (must be registered before the static file mount) ──────────────

@app.post("/api/find-game")
async def find_game(req: FindGameRequest):
    """Add player to matchmaking queue; returns status and game_id when paired."""
    return add_to_queue(req.player_id)


@app.post("/api/move")
async def move(req: MakeMoveRequest):
    """Submit a 5-letter Wordle guess; returns tile result and game state."""
    result = _make_move(req.player_id, req.guess)
    if result is None:
        raise HTTPException(status_code=404, detail="No active game for this player")
    if not result.get("valid"):
        raise HTTPException(status_code=400, detail=result.get("reason", "invalid move"))
    return result


@app.get("/api/game/{player_id}")
async def game_state(player_id: str):
    """Poll for current game state — used while waiting for an opponent or checking progress."""
    state = get_game_state(player_id)
    if state is None:
        raise HTTPException(status_code=404, detail="No active game for this player")
    return state


@app.delete("/api/player/{player_id}")
async def leave_game(player_id: str):
    """Remove a player from the queue or their active game (mirrors socket disconnect)."""
    return remove_player(player_id)


# ── static files (catch-all — must come last) ─────────────────────────────────

app.mount("/", StaticFiles(directory="public", html=True), name="static")


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("server:app", host="localhost", port=3000, reload=True)
