import os
import requests

class SteamAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("STEAM_API_KEY")
        if not self.api_key:
            raise ValueError("Steam API key is required.")
        self.base_url = "http://api.steampowered.com"

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
            return players[0] if players else None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to fetch player summary: {e}")
            return None

    def get_owned_games(self, steam_id, include_appinfo=True, include_played_free_games=True):
        url = f"{self.base_url}/IPlayerService/GetOwnedGames/v0001/"
        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "include_appinfo": int(include_appinfo),
            "include_played_free_games": int(include_played_free_games)
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("response", {}).get("games", [])
        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                raise ValueError("Steam profile is private or restricted.")
            raise ValueError(f"Steam API error: {e}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to get owned games: {e}")

    def resolve_vanity_url(self, vanity_url):
        url = f"{self.base_url}/ISteamUser/ResolveVanityURL/v0001/"
        params = {
            "key": self.api_key,
            "vanityurl": vanity_url
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("response", {}).get("success") == 1:
                return data["response"]["steamid"]
            else:
                raise ValueError(f"Vanity URL '{vanity_url}' could not be resolved.")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to resolve vanity URL: {e}")


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
    def resolve_vanity_url(self, vanity_url):
        url = f"{self.base_url}/ISteamUser/ResolveVanityURL/v1/"
        params = {"key": self.api_key, "vanityurl": vanity_url}
        response = requests.get(url, params=params)
        data = response.json()
        if data.get("response", {}).get("success") == 1:
            return data["response"]["steamid"]
        return None
