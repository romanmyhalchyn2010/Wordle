import uuid
from game import WordleGame

waiting_queue:   list[str]       = []   # player_ids waiting for an opponent
active_games:    dict[str, WordleGame] = {}   # game_id  -> WordleGame
player_sessions: dict[str, str]  = {}   # player_id -> game_id


def _new_game_id() -> str:
    return str(uuid.uuid4())


def add_to_queue(player_id: str) -> dict:
    # guard: already in an active game
    if player_id in player_sessions:
        return {"status": "already_in_game", "game_id": player_sessions[player_id]}

    # guard: already in queue — prevent double-queuing on fast clicks
    if player_id in waiting_queue:
        return {"status": "waiting"}

    if waiting_queue:
        opponent_id = waiting_queue.pop(0)
        game_id     = _new_game_id()
        game        = WordleGame()
        game.add_player(opponent_id)
        game.add_player(player_id)

        active_games[game_id]        = game
        player_sessions[opponent_id] = game_id
        player_sessions[player_id]   = game_id

        return {"status": "game_started", "game_id": game_id}

    waiting_queue.append(player_id)
    return {"status": "waiting"}


def make_move(player_id: str, guess: str) -> dict | None:
    game_id = player_sessions.get(player_id)
    if not game_id:
        return None
    game = active_games.get(game_id)
    if not game:
        return None
    return {**game.evaluate_guess(player_id, guess), "game_id": game_id}


def get_game_state(player_id: str) -> dict | None:
    game_id = player_sessions.get(player_id)
    if not game_id:
        return None
    game = active_games.get(game_id)
    if not game:
        return None
    return {**game.get_state(), "game_id": game_id}


def remove_player(player_id: str) -> dict:
    # remove from queue if still waiting
    if player_id in waiting_queue:
        waiting_queue.remove(player_id)

    game_id = player_sessions.pop(player_id, None)
    if not game_id:
        return {"status": "removed"}

    game = active_games.get(game_id)
    if game:
        opponent_ids = [p for p in game.players if p != player_id]
        game.remove_player(player_id)
        # clean up if no players remain
        if not game.players:
            active_games.pop(game_id, None)
            for pid in opponent_ids:
                player_sessions.pop(pid, None)

    return {"status": "removed", "game_id": game_id}
