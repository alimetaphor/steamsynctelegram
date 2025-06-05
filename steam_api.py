import os
import requests
from functools import lru_cache


class SteamAPI:
    def __init__(self, api_key):
        self.api_key = api_key

    def resolve_vanity_url(self, vanity_url):
        url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={self.api_key}&vanityurl={vanity_url}"
        response = requests.get(url)
        data = response.json()
        if data["response"]["success"] == 1:
            return data["response"]["steamid"]
        raise Exception("Vanity URL not found")

    @lru_cache(maxsize=200)
    def get_player_summary(self, steam_id):
        url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={self.api_key}&steamids={steam_id}"
        response = requests.get(url)
        return response.json()["response"]["players"][0]

    def get_owned_games(self, steam_id):
        url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.api_key}&steamid={steam_id}&include_appinfo=1"
        response = requests.get(url)
        return response.json()["response"].get("games", [])
    def get_recently_played_games(self, steam_id, count=5):
        url = f"{self.base_url}/IPlayerService/GetRecentlyPlayedGames/v0001/"
        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "count": count
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            games = data.get("response", {}).get("games", [])
            return games
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] HTTP error in get_recently_played_games: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error in get_recently_played_games: {e}")
        return []
   
