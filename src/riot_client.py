from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


class RiotApiError(Exception):
    pass


@dataclass(frozen=True)
class RiotRegions:
    routing: str
    platform: str


REGION_ALIASES: dict[str, RiotRegions] = {
    "euw": RiotRegions(routing="europe", platform="euw1"),
    "euw1": RiotRegions(routing="europe", platform="euw1"),
    "eune": RiotRegions(routing="europe", platform="eun1"),
    "eun1": RiotRegions(routing="europe", platform="eun1"),
    "na": RiotRegions(routing="americas", platform="na1"),
    "na1": RiotRegions(routing="americas", platform="na1"),
    "br": RiotRegions(routing="americas", platform="br1"),
    "br1": RiotRegions(routing="americas", platform="br1"),
    "lan": RiotRegions(routing="americas", platform="la1"),
    "la1": RiotRegions(routing="americas", platform="la1"),
    "las": RiotRegions(routing="americas", platform="la2"),
    "la2": RiotRegions(routing="americas", platform="la2"),
    "kr": RiotRegions(routing="asia", platform="kr"),
    "jp": RiotRegions(routing="asia", platform="jp1"),
    "jp1": RiotRegions(routing="asia", platform="jp1"),
    "oce": RiotRegions(routing="sea", platform="oc1"),
    "oc1": RiotRegions(routing="sea", platform="oc1"),
    "sea": RiotRegions(routing="sea", platform="sg2"),
    "sg2": RiotRegions(routing="sea", platform="sg2"),
    "tr": RiotRegions(routing="europe", platform="tr1"),
    "tr1": RiotRegions(routing="europe", platform="tr1"),
    "ru": RiotRegions(routing="europe", platform="ru"),
}


def resolve_region(region_or_platform: str, platform: str | None = None) -> RiotRegions:
    if platform:
        key = region_or_platform.strip().lower()
        if key not in {"americas", "europe", "asia", "sea"}:
            raise RiotApiError("Invalid routing region. Use one of: americas, europe, asia, sea.")
        return RiotRegions(routing=key, platform=platform.strip().lower())

    key = region_or_platform.strip().lower()
    if key in {"americas", "europe", "asia", "sea"}:
        default_platform = {"americas": "na1", "europe": "euw1", "asia": "kr", "sea": "oc1"}[key]
        return RiotRegions(routing=key, platform=default_platform)
    if key not in REGION_ALIASES:
        raise RiotApiError(f"Unknown region/platform '{region_or_platform}'.")
    return REGION_ALIASES[key]


class RiotClient:
    def __init__(self, api_key: str, routing_region: str, platform_region: str, timeout: int = 15) -> None:
        self.api_key = api_key
        self.routing_region = routing_region
        self.platform_region = platform_region
        self.timeout = timeout

    @property
    def account_base(self) -> str:
        return f"https://{self.routing_region}.api.riotgames.com"

    @property
    def match_base(self) -> str:
        return f"https://{self.routing_region}.api.riotgames.com"

    @property
    def summoner_base(self) -> str:
        return f"https://{self.platform_region}.api.riotgames.com"

    def _request(self, url: str, params: dict[str, Any] | None = None) -> Any:
        headers = {"X-Riot-Token": self.api_key}
        response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
        if response.status_code == 429:
            raise RiotApiError("Rate limit hit (HTTP 429). Try again in a moment.")
        if response.status_code == 403:
            raise RiotApiError("Forbidden (HTTP 403). Check if your Riot API key is valid/active.")
        if response.status_code == 401:
            raise RiotApiError("Unauthorized (HTTP 401). API key is missing, expired, or invalid.")
        if response.status_code == 404:
            raise RiotApiError("Not found (HTTP 404). Check Riot ID/tag and region.")
        if response.status_code >= 400:
            raise RiotApiError(f"Riot API error {response.status_code}: {response.text}")
        return response.json()

    def get_account_by_riot_id(self, game_name: str, tag_line: str) -> dict[str, Any]:
        url = f"{self.account_base}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        data = self._request(url)
        if not data.get("puuid"):
            raise RiotApiError("Account lookup succeeded but no PUUID was returned.")
        return data

    def get_summoner_by_puuid(self, puuid: str) -> dict[str, Any]:
        url = f"{self.summoner_base}/lol/summoner/v4/summoners/by-puuid/{puuid}"
        return self._request(url)

    def get_latest_match_id(self, puuid: str) -> str:
        url = f"{self.match_base}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        match_ids = self._request(url, params={"start": 0, "count": 1})
        if not match_ids:
            raise RiotApiError("No recent matches found for this player.")
        return match_ids[0]

    def get_match_detail(self, match_id: str) -> dict[str, Any]:
        url = f"{self.match_base}/lol/match/v5/matches/{match_id}"
        return self._request(url)
