"""AllSportsApi (clé ALLSPORTS_KEY) : source de secours pour le direct."""
from __future__ import annotations

import os

from .http import get_json

BASE = "https://apiv2.allsportsapi.com/football/"
LEAGUE_NAMES = {"en.1": "Premier League", "en.2": "Championship", "es.1": "LaLiga", "it.1": "Serie A",
                "de.1": "Bundesliga", "fr.1": "Ligue 1", "nl.1": "Eredivisie", "pt.1": "Primeira Liga"}
COUNTRIES = {"en.1": "England", "en.2": "England", "es.1": "Spain", "it.1": "Italy", "de.1": "Germany",
             "fr.1": "France", "nl.1": "Netherlands", "pt.1": "Portugal"}


def _league(name: str, country: str) -> str | None:
    for code, n in LEAGUE_NAMES.items():
        if n.lower() in (name or "").lower() and COUNTRIES[code].lower() in (country or "").lower():
            return code
    return None


def live() -> list[dict]:
    key = os.environ.get("ALLSPORTS_KEY")
    if not key:
        return []
    data = get_json(BASE, {"met": "Livescore", "APIkey": key}, ttl_s=60, secret_params=("APIkey",))
    out = []
    for r in (data or {}).get("result") or []:
        lg = _league(r.get("league_name"), r.get("country_name"))
        if not lg:
            continue
        try:
            hg, ag = (int(x) for x in (r.get("event_final_result") or "").replace(" ", "").split("-"))
        except ValueError:
            hg = ag = None
        minute = "".join(c for c in str(r.get("event_status") or "") if c.isdigit())
        events = [{"min": g.get("time"), "type": "Goal", "detail": g.get("score"),
                   "team": "h" if g.get("home_scorer") else "a"} for g in r.get("goalscorers") or []]
        out.append({"league": lg, "home": r.get("event_home_team", ""), "away": r.get("event_away_team", ""),
                    "minute": int(minute) if minute else None, "status": r.get("event_status"),
                    "hg": hg, "ag": ag, "events": events[-12:], "source": "AllSportsApi"})
    return out
