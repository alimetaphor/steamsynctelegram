import os
import requests
from functools import lru_cache

class SteamAPI:
    def __init__(self):
        self.api_key = os.environ.get("STEAM_API_KEY")
        if not self.api_key:
            raise ValueError("STEAM_API_KEY environment variable is not set")
    
    @lru_cache(maxsize=100)
    def get_player_summary(self, steam_id):
        url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={self.api_key}&steamids={steam_id}"
        response = requests.get(url)
        response.raise_for_status()  # خطاها رو بندازه بالا
        return response.json()["response"]["players"][0]
    
    def get_owned_games(self, steam_id):
        url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.api_key}&steamid={steam_id}&include_appinfo=1"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()["response"].get("games", [])
        
    def get_total_games(self, steam_id):
        games = self.get_owned_games(steam_id)
        return len(games)
