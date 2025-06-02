import requests

class SteamAPI:
    BASE_URL = "http://api.steampowered.com"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("STEAM_API_KEY")
        if not self.api_key:
            raise ValueError("❌ کلید API استیم پیدا نشد. لطفاً متغیر محیطی STEAM_API_KEY را تنظیم کنید.")

    def get_player_summary(self, steam_id):
        url = f"{self.BASE_URL}/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            "key": self.api_key,
            "steamids": steam_id
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        players = response.json().get("response", {}).get("players", [])
        return players[0] if players else None

    def get_owned_games(self, steam_id):
        url = f"{self.BASE_URL}/IPlayerService/GetOwnedGames/v0001/"
        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "include_appinfo": 1
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("response", {}).get("games", [])
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
