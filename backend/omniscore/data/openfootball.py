"""Résultats et calendriers réels depuis openfootball/football.json (domaine public, sans clé)."""
from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

BASE = "https://raw.githubusercontent.com/openfootball/football.json/master/{season}/{code}.json"
LEAGUES = {
    "en.1": "Premier League",
    "es.1": "LaLiga",
    "it.1": "Serie A",
    "de.1": "Bundesliga",
    "fr.1": "Ligue 1",
    "nl.1": "Eredivisie",
    "pt.1": "Liga Portugal",
    "en.2": "Championship",
}
CACHE = Path(os.environ.get("OMNISCORE_CACHE", Path(__file__).resolve().parents[2] / "data" / "cache"))


@dataclass(frozen=True)
class Match:
    league: str
    season: str
    date: date
    time: str | None
    round: str | None
    home: str
    away: str
    hg: int | None = None
    ag: int | None = None
    hthg: int | None = None
    htag: int | None = None

    @property
    def played(self) -> bool:
        return self.hg is not None

    @property
    def id(self) -> str:
        return f"{self.league}:{self.date.isoformat()}:{self.home}:{self.away}"


def season_label(start_year: int) -> str:
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def _fetch(season: str, code: str, max_age_h: float) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{season}_{code}.json"
    if path.exists() and (time.time() - path.stat().st_mtime) < max_age_h * 3600:
        return json.loads(path.read_text())
    url = BASE.format(season=season, code=code)
    with urllib.request.urlopen(url, timeout=30) as r:  # noqa: S310 (URL fixe)
        raw = r.read()
    path.write_bytes(raw)
    return json.loads(raw)


def _score(s) -> tuple:
    ft = ht = None
    if isinstance(s, dict):
        ft, ht = s.get("ft"), s.get("ht")
    elif isinstance(s, list) and len(s) == 2:
        ft = s
    ft = ft if ft and len(ft) == 2 else None
    ht = ht if ht and len(ht) == 2 else None
    return (ft[0] if ft else None, ft[1] if ft else None, ht[0] if ht else None, ht[1] if ht else None)


def load_season(code: str, season: str, max_age_h: float = 6) -> list[Match]:
    """Charge une saison ; les saisons terminées restent en cache indéfiniment."""
    past = int(season[:4]) + 1 < date.today().year
    data = _fetch(season, code, 24 * 3650 if past else max_age_h)
    out = []
    for m in data.get("matches", []):
        hg, ag, hthg, htag = _score(m.get("score"))
        out.append(Match(code, season, date.fromisoformat(m["date"]), m.get("time"), m.get("round"),
                         m["team1"], m["team2"], hg, ag, hthg, htag))
    return out


def load(codes=None, first: int = 2021, last: int | None = None) -> list[Match]:
    """Toutes les saisons de `first` à `last` (incluse) pour les ligues demandées."""
    codes = codes or list(LEAGUES)
    today = date.today()
    last = last if last is not None else (today.year if today.month >= 7 else today.year - 1)
    out = []
    for code in codes:
        for y in range(first, last + 1):
            try:
                out.extend(load_season(code, season_label(y)))
            except Exception as e:  # saison absente ou réseau
                print(f"[openfootball] {code} {season_label(y)} ignorée : {e}")
    out.sort(key=lambda m: (m.date, m.league, m.home))
    return out
