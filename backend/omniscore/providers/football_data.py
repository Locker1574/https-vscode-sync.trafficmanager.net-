"""football-data.org (clé FOOTBALL_DATA_KEY) : calendrier, résultats avec la mi-temps, classements.

Complète openfootball : scores publiés plus vite, score à la mi-temps (règlement des marchés de 1re MT)
et classements réels pour l'indice d'enjeu.
"""
from __future__ import annotations

import os
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

from .http import get_json
from .names import same_team

BASE = "https://api.football-data.org/v4"
COMPETITIONS = {"en.1": "PL", "en.2": "ELC", "es.1": "PD", "it.1": "SA", "de.1": "BL1", "fr.1": "FL1", "nl.1": "DED", "pt.1": "PPL"}
# Places qualificatives et de relégation par ligue (approximation stable d'une saison à l'autre).
ZONES = {"en.1": (4, 18), "en.2": (2, 22), "es.1": (4, 18), "it.1": (4, 18), "de.1": (4, 16), "fr.1": (4, 16), "nl.1": (2, 16), "pt.1": (2, 16)}


def _key() -> str | None:
    return os.environ.get("FOOTBALL_DATA_KEY")


def _get(path: str, params: dict | None = None, ttl_s: float = 3600):
    if not _key():
        return None
    return get_json(BASE + path, params, headers={"X-Auth-Token": _key()}, ttl_s=ttl_s)


def fetch_matches(league: str, start: date, end: date) -> list[dict]:
    code = COMPETITIONS.get(league)
    if not code:
        return []
    data = _get(f"/competitions/{code}/matches", {"dateFrom": start.isoformat(), "dateTo": end.isoformat()}, ttl_s=1800)
    out = []
    for m in (data or {}).get("matches", []):
        ft, ht = (m.get("score") or {}).get("fullTime") or {}, (m.get("score") or {}).get("halfTime") or {}
        utc = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
        out.append({
            "league": league, "utc": utc, "date": utc.date(), "status": m.get("status"),
            "home": (m.get("homeTeam") or {}).get("name") or "", "away": (m.get("awayTeam") or {}).get("name") or "",
            "hg": ft.get("home"), "ag": ft.get("away"), "hthg": ht.get("home"), "htag": ht.get("away"),
        })
    return out


def fetch_standings(league: str) -> list[dict]:
    code = COMPETITIONS.get(league)
    data = _get(f"/competitions/{code}/standings", ttl_s=6 * 3600) if code else None
    for table in (data or {}).get("standings", []):
        if table.get("type") == "TOTAL":
            return [{"pos": r["position"], "team": r["team"]["name"], "played": r["playedGames"], "pts": r["points"],
                     "gd": r.get("goalDifference"), "form": r.get("form")} for r in table.get("table", [])]
    return []


def enrich(matches: list, days_back: int = 10, days_ahead: int = 30) -> tuple[list, int]:
    """Complète les scores (fin de match et mi-temps) des matchs openfootball ; renvoie (matchs, nb complétés)."""
    if not _key():
        return matches, 0
    today = date.today()
    by_league: dict[str, list[dict]] = {}
    for lg in {m.league for m in matches} & COMPETITIONS.keys():
        by_league[lg] = fetch_matches(lg, today - timedelta(days=days_back), today + timedelta(days=days_ahead))
    out, n = [], 0
    for m in matches:
        fd = next((x for x in by_league.get(m.league, []) if abs((x["date"] - m.date).days) <= 1
                   and same_team(x["home"], m.home) and same_team(x["away"], m.away)), None)
        if fd and fd["status"] == "FINISHED" and fd["hg"] is not None and (m.hg is None or m.hthg is None):
            m = replace(m, hg=fd["hg"], ag=fd["ag"], hthg=fd["hthg"], htag=fd["htag"])
            n += 1
        out.append(m)
    return out, n


def stakes(league: str, table: list[dict]) -> dict[str, dict]:
    """Indice d'enjeu (0-100) par équipe à partir du classement réel."""
    if not table:
        return {}
    top, releg = ZONES.get(league, (4, 18))
    size = len(table)
    out = {}
    for r in table:
        pos = r["pos"]
        if pos <= 2:
            out[r["team"]] = {"idx": 92, "label": "Course au titre", "pos": pos, "pts": r["pts"]}
        elif pos <= top + 2:
            out[r["team"]] = {"idx": 78, "label": "Places européennes" if league != "en.2" else "Promotion", "pos": pos, "pts": r["pts"]}
        elif pos >= min(releg, size) - 2:
            out[r["team"]] = {"idx": 85, "label": "Maintien", "pos": pos, "pts": r["pts"]}
        else:
            out[r["team"]] = {"idx": 45, "label": "Milieu de tableau", "pos": pos, "pts": r["pts"]}
    return out


def attach_context(preds: list[dict]) -> int:
    """Ajoute classement et enjeu réels à chaque prédiction ; renvoie le nombre de matchs enrichis."""
    if not _key():
        return 0
    n = 0
    for league in {p["league"] for p in preds}:
        table = fetch_standings(league)
        st = stakes(league, table)
        for p in (x for x in preds if x["league"] == league):
            h = next((v for k, v in st.items() if same_team(k, p["home"])), None)
            a = next((v for k, v in st.items() if same_team(k, p["away"])), None)
            if not (h or a):
                continue
            main = max((x for x in (h, a) if x), key=lambda x: x["idx"])
            p["stake"] = {"idx": main["idx"], "label": main["label"],
                          "home": h and {"pos": h["pos"], "pts": h["pts"]}, "away": a and {"pos": a["pos"], "pts": a["pts"]}}
            n += 1
    return n


def standings_all(leagues) -> dict[str, list[dict]]:
    return {lg: t for lg in leagues if (t := fetch_standings(lg))}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
