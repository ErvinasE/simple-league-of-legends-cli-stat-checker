from dataclasses import dataclass


@dataclass
class MatchSummary:
    riot_id: str
    region: str
    platform: str
    match_id: str
    queue_id: int
    win: bool
    champion: str
    kills: int
    deaths: int
    assists: int
    cs: int
    cs_per_min: float
    damage_dealt: int
    damage_taken: int
    duration_seconds: int
