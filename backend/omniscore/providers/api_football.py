"""API-Football (clé API_FOOTBALL_KEY) : matchs en direct et blessés / suspendus.

Offre gratuite : 100 requêtes par jour. Le direct est mis en cache 60 s, les absences 12 h.
"""
from __future__ import annotations

import os
from datetime import date

from .http import get_json

BASE = "https://v3.football.api-sports.io"
LEAGUE_IDS = {"en.1": 39, "en.2": 40, "es.1": 140, "it.1": 135, "de.1": 78, "fr.1": 61, "nl.1": 88, "pt.1": 94}
_BY_ID = {v: k for k, v in LEAGUE_IDS.items()}


def _get(path: str, params: dict, ttl_s: float):
    key = os.environ.get("API_FOOTBALL_KEY")
    if not key:
        return None
    return get_json(BASE + path, params, headers={"x-apisports-key": key}, ttl_s=ttl_s)


def live() -> list[dict]:
    """Matchs en cours dans les 8 championnats suivis."""
    data = _get("/fixtures", {"live": "-".join(str(i) for i in LEAGUE_IDS.values())}, ttl_s=60)
    out = []
    for r in (data or {}).get("response", []):
        lg = _BY_ID.get((r.get("league") or {}).get("id"))
        if not lg:
            continue
        fx, teams, goals = r.get("fixture") or {}, r.get("teams") or {}, r.get("goals") or {}
        home = (teams.get("home") or {}).get("name", "")
        events = [{"min": (e.get("time") or {}).get("elapsed"), "type": e.get("type"), "detail": e.get("detail"),
                   "team": "h" if (e.get("team") or {}).get("name") == home else "a"} for e in r.get("events") or []]
        out.append({"league": lg, "home": home, "away": (teams.get("away") or {}).get("name", ""),
                     "minute": (fx.get("status") or {}).get("elapsed"), "status": (fx.get("status") or {}).get("short"),
                     "hg": goals.get("home"), "ag": goals.get("away"), "events": events[-12:], "source": "API-Football"})
    return out


def injuries(leagues, season: int | None = None) -> dict[str, list[dict]]:
    """Joueurs absents du jour par équipe (nom d'équipe API-Football → liste)."""
    today = date.today()
    season = season or (today.year if today.month >= 7 else today.year - 1)
    out: dict[str, list[dict]] = {}
    for lg in leagues:
        if lg not in LEAGUE_IDS:
            continue
        data = _get("/injuries", {"league": LEAGUE_IDS[lg], "season": season, "date": today.isoformat()}, ttl_s=12 * 3600)
        for r in (data or {}).get("response", []):
            team = (r.get("team") or {}).get("name")
            if team:
                out.setdefault(team, []).append({"player": (r.get("player") or {}).get("name"),
                                                 "reason": (r.get("player") or {}).get("reason")})
    return out
