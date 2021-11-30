import json
from typing import Optional

import requests

with open("config.json") as f:
    config = json.load(f)


def get_google_map_api_key() -> str:
    """
    Get Google Map API key
    """

    return config['google_map_api_key']


def get_google_geocode_api_url(address: str) -> str:
    """
    Get Google Map Geocode API URL
    """

    key = get_google_map_api_key()

    return f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={key}"


def get_google_geocode_rev_api_url(lat: float, lng: float) -> str:
    """
    Get Google Map Reverse Geocode API URL
    """

    key = get_google_map_api_key()

    return f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={key}"


def get_google_map_api_result(url: str) -> Optional[dict]:
    """
    Get Google Map API result
    """

    result = requests.get(url).json()

    if result["status"] != "OK":
        return None

    return result["results"]
