from __future__ import annotations

import argparse
import os
import re
import sys

from dotenv import load_dotenv

from src.riot_client import RiotApiError, RiotClient, resolve_region
from src.models import MatchSummary
from src.formatters import render_summary


def parse_riot_id(value: str) -> tuple[str, str]:
    if "#" not in value:
        raise ValueError("Riot ID must be in format gameName#tagLine.")
    game_name, tag_line = value.split("#", 1)
    if not game_name or not tag_line:
        raise ValueError("Riot ID must include both gameName and tagLine.")
    return game_name, tag_line


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch latest League match summary from Riot API.")
    parser.add_argument("riot_id", help="Riot ID in format gameName#tagLine")
    parser.add_argument(
        "--region",
        default="euw",
        help="Region or platform shorthand (euw, na, kr) or routing region (europe, americas, asia, sea)",
    )
    parser.add_argument(
        "--platform",
        default=None,
        help="Optional explicit platform region override (euw1, na1, kr, ...)",
    )
    parser.add_argument("--verbose", action="store_true", help="Print extra lookup information.")
    return parser.parse_args()


def build_summary(
    riot_id: str,
    routing_region: str,
    platform_region: str,
    api_key: str,
    verbose: bool = False,
) -> MatchSummary:
    game_name, tag_line = parse_riot_id(riot_id)
    client = RiotClient(api_key=api_key, routing_region=routing_region, platform_region=platform_region)

    account = client.get_account_by_riot_id(game_name, tag_line)
    puuid = account["puuid"]

    _ = client.get_summoner_by_puuid(puuid)

    match_id = client.get_latest_match_id(puuid)
    match_data = client.get_match_detail(match_id)

    info = match_data.get("info", {})
    participants = info.get("participants", [])
    participant = next((p for p in participants if p.get("puuid") == puuid), None)
    if participant is None:
        raise RiotApiError("Could not find this player in latest match participant list.")

    duration_seconds = info.get("gameDuration", 0) or 0
    total_minions = int(participant.get("totalMinionsKilled", 0)) + int(participant.get("neutralMinionsKilled", 0))
    cs_per_min = total_minions / (duration_seconds / 60) if duration_seconds > 0 else 0.0

    if verbose:
        print(f"Resolved player PUUID: {puuid}")
        print(f"Latest match ID: {match_id}")

    return MatchSummary(
        riot_id=f"{game_name}#{tag_line}",
        region=routing_region,
        platform=platform_region,
        match_id=match_id,
        queue_id=int(info.get("queueId", 0)),
        win=bool(participant.get("win", False)),
        champion=str(participant.get("championName", "Unknown")),
        kills=int(participant.get("kills", 0)),
        deaths=int(participant.get("deaths", 0)),
        assists=int(participant.get("assists", 0)),
        cs=total_minions,
        cs_per_min=cs_per_min,
        damage_dealt=int(participant.get("totalDamageDealtToChampions", 0)),
        damage_taken=int(participant.get("totalDamageTaken", 0)),
        duration_seconds=int(duration_seconds),
    )


def main() -> int:
    load_dotenv()
    args = parse_args()

    api_key_raw = os.getenv("RIOT_API_KEY")
    api_key = (api_key_raw or "").strip().strip('"').strip("'")
    if not api_key:
        print("Missing RIOT_API_KEY. Add it to your .env file.", file=sys.stderr)
        return 2
    key_format_ok = bool(re.fullmatch(r"RGAPI-[0-9a-fA-F-]{36}", api_key))
    if not key_format_ok:
        print(
            "Invalid RIOT_API_KEY format. Expected value like "
            "RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            file=sys.stderr,
        )
        return 2

    try:
        resolved = resolve_region(args.region, args.platform)
        summary = build_summary(
            riot_id=args.riot_id,
            routing_region=resolved.routing,
            platform_region=resolved.platform,
            api_key=api_key,
            verbose=args.verbose,
        )
        print(render_summary(summary))
        return 0
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    except RiotApiError as exc:
        print(f"Riot API error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
