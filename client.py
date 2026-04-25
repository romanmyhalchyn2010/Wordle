# Headless Python test client — simulates a player connecting to the server via HTTP
# Useful for testing the API without opening a browser:
#   - registers a player ID
#   - calls /api/find-game to join the matchmaking queue
#   - polls /api/game/{player_id} until paired with an opponent
#   - submits guesses to /api/move and prints the coloured tile results
