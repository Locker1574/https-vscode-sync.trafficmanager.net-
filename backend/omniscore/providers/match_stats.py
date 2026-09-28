"""Statistiques réelles de chaque match joué : corners, tirs, tirs cadrés, fautes, cartons, hors-jeux, xG.

- football-data.co.uk (sans clé) : fichiers CSV par saison et par championnat → corners, tirs, tirs cadrés, fautes, cartons.
- API-Football (clé API_FOOTBALL_KEY) : /fixtures/statistics → hors-jeux et xG. Offre gratuite limitée à 100 requêtes par
  jour : au plus MAX_CALLS appels par exécution ; un match terminé reste en cache définitivement, l'historique se complète
  donc sur quelques jours.
"""
from __future__ import annotations

import csv
import io
import os
import re
import urllib.request
from datetime import date, datetime
from pathlib import Path

from .http import CACHE, get_json
from .names import norm, same_team

FDUK = "https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
FDUK_CODES = {"en.1": "E0", "en.2": "E1", "es.1": "SP1", "it.1": "I1", "de.1": "D1", "fr.1": "F1", "nl.1": "N1", "pt.1": "P1"}
# colonne domicile, colonne extérieur, statistique
FDUK_COLS = (("HC", "AC", "corners"), ("HS", "AS", "shots"), ("HST", "AST", "sot"), ("HF", "AF", "fouls"))
METRICS = ("corners", "shots", "sot", "fouls", "cards", "offsides", "xg")
MAX_CALLS = 80
FOREVER = 10 ** 10

# Noms abrégés de football-data.co.uk → nom reconnaissable par same_team.
ALIASES = {
    "man city": "manchester city", "man united": "manchester united", "nott m forest": "nottingham forest",
    "sheffield weds": "sheffield wednesday", "sheffield united": "sheffield united", "wolves": "wolverhampton",
    "qpr": "queens park rangers", "west brom": "west bromwich", "ath madrid": "atletico madrid",
    "ath bilbao": "athletic bilbao", "sociedad": "real sociedad", "espanol": "espanyol", "betis": "real betis",
    "celta": "celta vigo", "vallecano": "rayo vallecano", "alaves": "alaves", "inter": "internazionale",
    "milan": "milan", "roma": "roma", "m gladbach": "monchengladbach", "ein frankfurt": "eintracht frankfurt",
    "fc koln": "koln", "leverkusen": "bayer leverkusen", "dortmund": "borussia dortmund", "paris sg": "paris saint germain",
    "st etienne": "saint etienne", "psv eindhoven": "psv", "sp lisbon": "sporting", "sp braga": "braga",
    "for sittard": "fortuna sittard", "nijmegen": "nec", "guimaraes": "vitoria",
}


def _season_code(d: date) -> str:
    y = d.year if d.month >= 7 else d.year - 1
    return f"{y % 100:02d}{(y + 1) % 100:02d}"


def _fetch_csv(url: str, ttl_s: float) -> str | None:
    import hashlib
    import time
    path = CACHE / f"csv_{hashlib.sha256(url.encode()).hexdigest()[:24]}.csv"
    if path.exists() and time.time() - path.stat().st_mtime < ttl_s:
        return path.read_text(encoding="utf-8", errors="ignore")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "omniscore/1.0"}), timeout=30) as r:  # noqa: S310
            text = r.read().decode("utf-8-sig", errors="ignore")
    except Exception as e:
        print(f"[football-data.co.uk] {url} : {e}")
        return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else None
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return text


def _int(v) -> int | None:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _date(s: str) -> date | None:
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except (ValueError, AttributeError):
            pass
    return None


def parse_fduk(text: str) -> list[dict]:
    """Lignes du CSV → [{date, home, away, h:{stat:v}, a:{stat:v}}]."""
    out = []
    for r in csv.DictReader(io.StringIO(text)):
        d = _date(r.get("Date", ""))
        if not d or not r.get("HomeTeam"):
            continue
        h, a = {}, {}
        for hc, ac, name in FDUK_COLS:
            if _int(r.get(hc)) is not None and _int(r.get(ac)) is not None:
                h[name], a[name] = _int(r[hc]), _int(r[ac])
        hy, ay, hr, ar = (_int(r.get(k)) for k in ("HY", "AY", "HR", "AR"))
        if hy is not None and ay is not None:
            h["cards"], a["cards"] = hy + (hr or 0), ay + (ar or 0)
        if h:
            out.append({"date": d, "home": r["HomeTeam"], "away": r["AwayTeam"], "h": h, "a": a})
    return out


def team_match(a: str, b: str) -> bool:
    x = ALIASES.get(" ".join(re.sub(r"[^a-z0-9]", " ", norm(a)).split()), a)
    return same_team(x, b) or same_team(a, b)


def fduk_rows(league: str, seasons: list[str], current: str) -> list[dict]:
    code = FDUK_CODES.get(league)
    if not code:
        return []
    rows = []
    for s in seasons:
        text = _fetch_csv(FDUK.format(season=s, code=code), ttl_s=12 * 3600 if s == current else FOREVER)
        if text:
            rows += parse_fduk(text)
    return rows


class _Budget:
    def __init__(self, n: int):
        self.left = n

    def take(self) -> bool:
        if self.left <= 0:
            return False
        self.left -= 1
        return True


def _af_get(path: str, params: dict, ttl_s: float, budget: _Budget):
    from . import api_football
    key = os.environ.get("API_FOOTBALL_KEY")
    if not key:
        return None
    # déjà en cache ? get_json le relit sans appel réseau ; sinon il faut un crédit.
    import hashlib
    import time
    import urllib.parse
    k = hashlib.sha256((api_football.BASE + path + "?" + urllib.parse.urlencode(sorted(params.items()))).encode()).hexdigest()[:24]
    cached = CACHE / f"{k}.json"
    if not (cached.exists() and time.time() - cached.stat().st_mtime < ttl_s) and not budget.take():
        return None
    return get_json(api_football.BASE + path, params, headers={"x-apisports-key": key}, ttl_s=ttl_s)


def _num(v) -> float | None:
    if v is None:
        return None
    try:
        return float(str(v).rstrip("%"))
    except ValueError:
        return None


def af_stats(league: str, season_year: int, games: list, budget: _Budget) -> dict[str, dict]:
    """Hors-jeux et xG par match (id openfootball → {h:{}, a:{}}) pour les matchs `games` déjà joués."""
    from . import api_football
    lid = api_football.LEAGUE_IDS.get(league)
    if not lid or not games:
        return {}
    fx = _af_get("/fixtures", {"league": lid, "season": season_year, "status": "FT-AET-PEN"}, 12 * 3600, budget)
    fixtures = (fx or {}).get("response", [])
    out = {}
    for g in sorted(games, key=lambda g: g.date, reverse=True):
        f = next((f for f in fixtures if (f.get("fixture") or {}).get("date", "")[:10] == g.date.isoformat()
                  and team_match((f["teams"]["home"] or {}).get("name", ""), g.home)), None)
        if not f:
            continue
        st = _af_get("/fixtures/statistics", {"fixture": f["fixture"]["id"]}, FOREVER, budget)
        resp = (st or {}).get("response") or []
        if len(resp) != 2:
            continue
        sides = {}
        for side, r in zip("ha", resp):
            vals = {s.get("type"): s.get("value") for s in r.get("statistics") or []}
            d = {}
            if "Offsides" in vals:
                d["offsides"] = int(_num(vals.get("Offsides")) or 0)
            if _num(vals.get("expected_goals")) is not None:
                d["xg"] = round(_num(vals["expected_goals"]), 2)
            sides[side] = d
        if sides["h"] or sides["a"]:
            out[g.id] = sides
    return out


def collect(games, today: date | None = None, max_calls: int = MAX_CALLS) -> dict[str, dict]:
    """Statistiques par match (id → {"h": {...}, "a": {...}}) pour la liste `games` (matchs joués)."""
    today = today or date.today()
    cur = _season_code(today)
    prev = _season_code(date(today.year - 1, today.month, 1))
    by_lg: dict[str, list] = {}
    for g in games:
        by_lg.setdefault(g.league, []).append(g)
    out: dict[str, dict] = {}
    budget = _Budget(max_calls)
    for lg, gs in by_lg.items():
        rows = fduk_rows(lg, [prev, cur], cur)
        by_date: dict[date, list] = {}
        for r in rows:
            by_date.setdefault(r["date"], []).append(r)
        for g in gs:
            r = next((r for r in by_date.get(g.date, []) if team_match(r["home"], g.home) and team_match(r["away"], g.away)), None)
            if r:
                out[g.id] = {"h": dict(r["h"]), "a": dict(r["a"])}
    # API-Football : les matchs les plus récents d'abord, dans la limite du quota.
    y = today.year if today.month >= 7 else today.year - 1
    for lg, gs in by_lg.items():
        for sy in (y, y - 1):
            season_games = [g for g in gs if (g.date.year if g.date.month >= 7 else g.date.year - 1) == sy]
            for mid, sides in af_stats(lg, sy, season_games, budget).items():
                d = out.setdefault(mid, {"h": {}, "a": {}})
                d["h"].update(sides["h"])
                d["a"].update(sides["a"])
    return out
