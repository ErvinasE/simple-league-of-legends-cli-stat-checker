from __future__ import annotations

from .models import MatchSummary

QUEUE_NAMES = {
    420: "Ranked Solo/Duo",
    440: "Ranked Flex",
    400: "Normal Draft",
    430: "Normal Blind",
    450: "ARAM",
}


def queue_name(queue_id: int) -> str:
    return QUEUE_NAMES.get(queue_id, f"Queue {queue_id}")


def kda_ratio(kills: int, deaths: int, assists: int) -> float:
    if deaths == 0:
        return float(kills + assists)
    return round((kills + assists) / deaths, 2)


def format_duration(seconds: int) -> str:
    mins, secs = divmod(max(seconds, 0), 60)
    return f"{mins:02d}:{secs:02d}"


def render_summary(summary: MatchSummary) -> str:
    result = "WIN" if summary.win else "LOSS"
    kda = kda_ratio(summary.kills, summary.deaths, summary.assists)
    duration = format_duration(summary.duration_seconds)
    queue = queue_name(summary.queue_id)

    return (
        "=== Simple League of Legends CLI Stat Checker: Latest Match ===\n"
        f"Riot ID: {summary.riot_id}\n"
        f"Region: {summary.region} | Platform: {summary.platform}\n"
        f"Match: {summary.match_id} ({queue})\n"
        f"Result: {result}\n"
        f"Champion: {summary.champion}\n"
        f"K/D/A: {summary.kills}/{summary.deaths}/{summary.assists} (KDA: {kda})\n"
        f"CS: {summary.cs} ({summary.cs_per_min:.1f}/min)\n"
        f"Damage: dealt {summary.damage_dealt:,} | taken {summary.damage_taken:,}\n"
        f"Duration: {duration}\n"
    )
