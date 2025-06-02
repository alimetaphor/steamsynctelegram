import requests

class SteamAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.steampowered.com"

    def get_player_summary(self, steam_id):
        url = f"{self.base_url}/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            "key": self.api_key,
            "steamids": steam_id
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            players = data.get("response", {}).get("players", [])
            if not players:
                print(f"[WARN] No player summary found for Steam ID: {steam_id}")
                return None
            return players[0]
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] HTTP error in get_player_summary: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error in get_player_summary: {e}")
        return None

    def get_owned_games(self, steam_id):
        url = f"{self.base_url}/IPlayerService/GetOwnedGames/v0001/"
        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "include_appinfo": True,
            "include_played_free_games": True
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            games = data.get("response", {}).get("games", [])
            return games
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] HTTP error in get_owned_games: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error in get_owned_games: {e}")
        return []

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
