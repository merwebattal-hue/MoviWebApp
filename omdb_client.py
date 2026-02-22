import requests

class OmdbClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.omdbapi.com/"

    def film_suchen(self, titel: str) -> dict | None:
        if not self.api_key:
            raise RuntimeError("OMDB_API_KEY fehlt. Bitte als Umgebungsvariable setzen.")

        params = {"t": titel, "apikey": self.api_key}
        antwort = requests.get(self.base_url, params=params, timeout=10)
        daten = antwort.json()

        if daten.get("Response") == "True":
            return daten
        return None
