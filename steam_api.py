import requests
from functools import lru_cache

class SteamAPI:
    def __init__(self, api_key):
        self.api_key = api_key
    
    @lru_cache(maxsize=100)
    def get_player_summary(self, steam_id):
        url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={self.api_key}&steamids={steam_id}"
        response = requests.get(url)
        return response.json()["response"]["players"][0]
    
    def get_owned_games(self, steam_id):
        url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.api_key}&steamid={steam_id}&include_appinfo=1"
        response = requests.get(url)
        return response.json()["response"].get("games", [])
