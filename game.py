import random  # used to pick a random word from WORD_LIST when no word is provided

# all valid answer words the game will randomly choose from
WORD_LIST = [
    "crane", "stare", "audio", "adieu", "later", "raise", "arose", "atone",
    "irate", "snare", "blaze", "crisp", "dwarf", "fjord", "glyph", "jumpy",
    "knack", "lusty", "mirth", "nymph", "oxide", "pixie", "quaff", "relax",
    "stomp", "tryst", "ulcer", "vixen", "waltz", "xylem", "yearn", "zesty",
]

# tile state constants — sent to the frontend to colour each cell
TILE_CORRECT = "correct"  # letter is in the word AND in the right position (green)
TILE_PRESENT = "present"  # letter is in the word but in the wrong position (yellow)
TILE_ABSENT  = "absent"   # letter is not in the word at all (gray)

MAX_GUESSES = 6  # each player gets 6 attempts before they run out
WORD_LENGTH = 5  # every Wordle word is exactly 5 letters


class WordleGame:
    def __init__(self, word: str | None = None):
        # pick the secret word: use the provided word or choose one at random
        self.word = (word or random.choice(WORD_LIST)).lower()
        self.players: list[str] = []    # stores up to 2 player IDs in join order
        self.guesses: list[dict] = []   # every guess from both players, in submission order
        self.game_over = False          # becomes True when someone wins or both players exhaust their guesses
        self.winner: str | None = None  # player_id of whoever guessed correctly, or None if no winner yet

    def add_player(self, player_id: str) -> dict:
        if len(self.players) >= 2:          # room is full — reject a third player
            return {"full": True}
        self.players.append(player_id)      # register this player in the game
        # started: True when the second player joins, signalling matchmaking the game can begin
        return {"joined": True, "started": len(self.players) == 2}

    def remove_player(self, player_id: str):
        # drop the player from the list, e.g. when they disconnect
        self.players = [p for p in self.players if p != player_id]

    def evaluate_guess(self, player_id: str, guess: str) -> dict:
        if self.game_over:                      # reject any move after the game has already ended
            return {"valid": False, "reason": "game_over"}
        if player_id not in self.players:       # reject moves from unknown / unregistered players
            return {"valid": False, "reason": "not_in_game"}
        guess = guess.lower().strip()           # normalise: lowercase and remove surrounding whitespace
        if len(guess) != WORD_LENGTH:           # reject guesses that aren't exactly 5 letters
            return {"valid": False, "reason": "wrong_length"}

        result = self._score(guess)             # compute green/yellow/gray result for each letter
        # store the guess so both players can later retrieve full game history
        self.guesses.append({"player_id": player_id, "guess": guess, "result": result})

        # count how many guesses this specific player has made so far
        player_guesses = [g for g in self.guesses if g["player_id"] == player_id]
        # win condition: every tile in the result is green (correct position)
        won = all(r == TILE_CORRECT for r in result)

        if won:
            self.game_over = True       # lock the game so no more moves are accepted
            self.winner = player_id     # record who won
        elif len(player_guesses) >= MAX_GUESSES:
            # this player used all their guesses; check if the other player is also done
            all_done = all(
                len([g for g in self.guesses if g["player_id"] == p]) >= MAX_GUESSES
                for p in self.players   # iterate over both registered players
            )
            if all_done:                # only end the game when BOTH players are exhausted
                self.game_over = True

        return {
            "valid":     True,          # move was accepted and processed
            "guess":     guess,         # echo the normalised guess back to the client
            "result":    result,        # list of 5 tile states for the client to colour
            "won":       won,           # True if this guess solved the word
            "game_over": self.game_over,# True if the whole game is now finished
            # reveal the secret word only after the game ends so opponents can't peek mid-game
            "word":      self.word if self.game_over else None,
        }

    def get_player_state(self, player_id: str) -> dict:
        # collect only this player's own guesses (with letters) for their board
        my_guesses = [g for g in self.guesses if g["player_id"] == player_id]
        # find the other player's ID — returns None if we only have one player so far
        opponent_id = next((p for p in self.players if p != player_id), None)
        # build the opponent grid: colours only, letters stripped — the player can see progress but not the exact guesses
        opponent_grid = [
            g["result"]  # just the list of tile states, no "guess" key included
            for g in self.guesses if g["player_id"] == opponent_id
        ] if opponent_id else []  # empty list if there is no opponent yet

        return {
            "word_length":   WORD_LENGTH,    # tells the client how wide to draw the board
            "max_guesses":   MAX_GUESSES,    # tells the client how many rows to draw
            "my_guesses":    my_guesses,     # this player's full guess history (letters + colours)
            "opponent_grid": opponent_grid,  # opponent's guess history as colours only
            "game_over":     self.game_over, # whether the game has ended
            "winner":        self.winner,    # player_id of the winner, or None
            # convenience bool so the client doesn't have to compare IDs
            "i_won":         self.winner == player_id if self.winner else False,
            # word is hidden until game over so neither player can read it from the API mid-game
            "word":          self.word if self.game_over else None,
        }

    def get_state(self) -> dict:
        # raw full state used internally; does not personalise for either player
        return {
            "word_length": WORD_LENGTH,   # board width
            "max_guesses": MAX_GUESSES,   # board height
            "guesses":     self.guesses,  # all guesses from all players, unfiltered
            "game_over":   self.game_over,
            "winner":      self.winner,
            "word":        self.word if self.game_over else None,
        }

    def _score(self, guess: str) -> list[str]:
        result     = [TILE_ABSENT] * WORD_LENGTH  # start with everything gray; correct passes will upgrade tiles
        word_chars = list(self.word)              # mutable copy so we can "consume" letters to avoid double-counting

        # first pass — mark exact position matches (green) and consume those letters
        for i, ch in enumerate(guess):
            if ch == word_chars[i]:       # letter matches at this exact position
                result[i]     = TILE_CORRECT
                word_chars[i] = None      # mark as consumed so the second pass won't count it again

        # second pass — mark letters that exist elsewhere in the word (yellow)
        for i, ch in enumerate(guess):
            if result[i] == TILE_CORRECT:          # already marked green in the first pass — skip
                continue
            if ch in word_chars:                   # letter exists somewhere in the remaining (unconsumed) positions
                result[i] = TILE_PRESENT
                word_chars[word_chars.index(ch)] = None  # consume this occurrence so duplicates are handled correctly

        return result  # list of 5 strings: "correct", "present", or "absent"
