import uuid          # used to generate unique game room IDs
from game import WordleGame  # import the game class so we can create a new game when two players are paired

# module-level state — these live for the entire server process lifetime
waiting_queue:   list[str]            = []  # player_ids of players who clicked "Find Game" but have no opponent yet
active_games:    dict[str, WordleGame] = {}  # maps game_id -> WordleGame instance for every ongoing game
player_sessions: dict[str, str]       = {}  # maps player_id -> game_id so we can look up a player's game quickly


def _new_game_id() -> str:
    return str(uuid.uuid4())  # generate a random UUID string like "a3f2c1d0-..." — guaranteed globally unique


def add_to_queue(player_id: str) -> dict:
    # guard: player is already in an active game — return their existing game_id instead of re-queuing
    if player_id in player_sessions:
        return {"status": "already_in_game", "game_id": player_sessions[player_id]}

    # guard: player already clicked "Find Game" and is waiting — ignore the duplicate request
    if player_id in waiting_queue:
        return {"status": "waiting"}

    if waiting_queue:  # at least one player is already waiting — pair them immediately
        opponent_id = waiting_queue.pop(0)   # take the first player out of the queue (FIFO order)
        game_id     = _new_game_id()         # create a unique ID for this game room
        game        = WordleGame()           # create a fresh game with a randomly chosen word

        game.add_player(opponent_id)  # register the waiting player first (they joined first)
        game.add_player(player_id)    # register the new player second

        active_games[game_id]        = game          # store the game so future requests can find it by ID
        player_sessions[opponent_id] = game_id       # let the opponent look up this game_id later
        player_sessions[player_id]   = game_id       # same for the new player

        return {"status": "game_started", "game_id": game_id}  # tell the caller the game is ready

    # no opponent waiting — park this player in the queue and tell them to wait
    waiting_queue.append(player_id)
    return {"status": "waiting"}


def make_move(player_id: str, guess: str) -> dict | None:
    game_id = player_sessions.get(player_id)  # look up which game this player belongs to
    if not game_id:                            # player has no active game — can't move
        return None
    game = active_games.get(game_id)          # retrieve the actual game object
    if not game:                              # game was cleaned up already — can't move
        return None
    move_result = game.evaluate_guess(player_id, guess)  # apply the guess and get tile results

    # find the opponent's player_id so we can collect their grid
    opponent_id = next((p for p in game.players if p != player_id), None)
    # build opponent's grid (colours only, no letters) to send back with this move response
    # this saves the client from having to wait for the next poll to see the opponent's latest state
    opponent_grid = [
        g["result"] for g in game.guesses if g["player_id"] == opponent_id
    ] if opponent_id else []  # empty list if there's no opponent yet

    # merge move result + game_id + opponent grid into one response dict
    return {**move_result, "game_id": game_id, "opponent_grid": opponent_grid}


def get_game_state(player_id: str) -> dict | None:
    game_id = player_sessions.get(player_id)  # find the game this player is in
    if not game_id:                            # player isn't in any game
        return None
    game = active_games.get(game_id)          # fetch the game object
    if not game:                              # game doesn't exist (already cleaned up)
        return None
    # return a personalised view: own guesses with letters, opponent guesses as colours only
    return {**game.get_player_state(player_id), "game_id": game_id}


def remove_player(player_id: str) -> dict:
    # if the player was still waiting for an opponent, remove them from the queue
    if player_id in waiting_queue:
        waiting_queue.remove(player_id)

    # remove the player's session entry and get their game_id (if any)
    game_id = player_sessions.pop(player_id, None)
    if not game_id:                   # player wasn't in a game — nothing else to clean up
        return {"status": "removed"}

    game = active_games.get(game_id)  # fetch the game they were part of
    if game:
        # collect the other player's ID before modifying the players list
        opponent_ids = [p for p in game.players if p != player_id]
        game.remove_player(player_id)  # remove the leaving player from the game object

        if not game.players:  # no players left in the game — safe to fully delete it
            active_games.pop(game_id, None)         # free the game from memory
            for pid in opponent_ids:                # clean up the opponent's session pointer too
                player_sessions.pop(pid, None)

    return {"status": "removed", "game_id": game_id}  # confirm removal to the caller
