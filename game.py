import random

WORD_LIST = [
    "crane", "stare", "audio", "adieu", "later", "raise", "arose", "atone",
    "irate", "snare", "blaze", "crisp", "dwarf", "fjord", "glyph", "jumpy",
    "knack", "lusty", "mirth", "nymph", "oxide", "pixie", "quaff", "relax",
    "stomp", "tryst", "ulcer", "vixen", "waltz", "xylem", "yearn", "zesty",
]

TILE_CORRECT = "correct"   # right letter, right position (green)
TILE_PRESENT = "present"   # right letter, wrong position (yellow)
TILE_ABSENT  = "absent"    # letter not in word (gray)

MAX_GUESSES  = 6
WORD_LENGTH  = 5


class WordleGame:
    def __init__(self, word: str | None = None):
        self.word    = (word or random.choice(WORD_LIST)).lower()
        self.players: list[str] = []           # up to 2 player IDs
        self.guesses: list[dict] = []          # all guesses from both players
        self.game_over = False
        self.winner: str | None = None         # player_id of winner, or None

    def add_player(self, player_id: str) -> dict:
        if len(self.players) >= 2:
            return {"full": True}
        self.players.append(player_id)
        return {"joined": True, "started": len(self.players) == 2}

    def remove_player(self, player_id: str):
        self.players = [p for p in self.players if p != player_id]

    def evaluate_guess(self, player_id: str, guess: str) -> dict:
        if self.game_over:
            return {"valid": False, "reason": "game_over"}
        if player_id not in self.players:
            return {"valid": False, "reason": "not_in_game"}
        guess = guess.lower().strip()
        if len(guess) != WORD_LENGTH:
            return {"valid": False, "reason": "wrong_length"}

        result = self._score(guess)
        self.guesses.append({"player_id": player_id, "guess": guess, "result": result})

        player_guesses = [g for g in self.guesses if g["player_id"] == player_id]
        won = all(r == TILE_CORRECT for r in result)

        if won:
            self.game_over = True
            self.winner = player_id
        elif len(player_guesses) >= MAX_GUESSES:
            # end the game only when all players are exhausted
            all_done = all(
                len([g for g in self.guesses if g["player_id"] == p]) >= MAX_GUESSES
                for p in self.players
            )
            if all_done:
                self.game_over = True

        return {
            "valid":     True,
            "guess":     guess,
            "result":    result,
            "won":       won,
            "game_over": self.game_over,
            "word":      self.word if self.game_over else None,
        }

    def get_state(self) -> dict:
        return {
            "word_length": WORD_LENGTH,
            "max_guesses": MAX_GUESSES,
            "guesses":     self.guesses,
            "game_over":   self.game_over,
            "winner":      self.winner,
            "word":        self.word if self.game_over else None,
        }

    def _score(self, guess: str) -> list[str]:
        result     = [TILE_ABSENT] * WORD_LENGTH
        word_chars = list(self.word)

        # first pass — exact matches (green)
        for i, ch in enumerate(guess):
            if ch == word_chars[i]:
                result[i]     = TILE_CORRECT
                word_chars[i] = None

        # second pass — present but wrong position (yellow)
        for i, ch in enumerate(guess):
            if result[i] == TILE_CORRECT:
                continue
            if ch in word_chars:
                result[i] = TILE_PRESENT
                word_chars[word_chars.index(ch)] = None

        return result
