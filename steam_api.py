import requests
from functools import lru_cache

class SteamAPI:
    def __init__(self, api_key):
        self.api_key = api_key
    
    @lru_cache(maxsize=100)
    def get_player_summary(self, steam_id):
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={self.api_key}&steamids={steam_id}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            players = data.get("response", {}).get("players", [])
            if not players:
                raise ValueError("No player data found for this SteamID")
            return players[0]
        except (requests.RequestException, ValueError) as e:
            print(f"Error fetching player summary: {e}")
            return None
    
    def get_owned_games(self, steam_id):
        url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.api_key}&steamid={steam_id}&include_appinfo=1"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get("response", {}).get("games", [])
        except requests.RequestException as e:
            print(f"Error fetching owned games: {e}")
            return []
        
    def get_total_games(self, steam_id):
        games = self.get_owned_games(steam_id)
        return len(games)
