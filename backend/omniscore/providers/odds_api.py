"""Cotes réelles via The Odds API (https://the-odds-api.com), clé dans ODDS_API_KEY.

Sans clé, l'application fonctionne sans value bets (probabilités seules).
Chaque synchronisation ajoute les cotes à data/odds_history.json (mouvements de cotes, onglet Intégrité).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .http import get_json
from .names import norm, same_team

SPORTS = {"en.1": "soccer_epl", "es.1": "soccer_spain_la_liga", "it.1": "soccer_italy_serie_a",
          "de.1": "soccer_germany_bundesliga", "fr.1": "soccer_france_ligue_one", "nl.1": "soccer_netherlands_eredivisie",
          "pt.1": "soccer_portugal_primeira_liga", "en.2": "soccer_efl_champ"}
HISTORY = Path(__file__).resolve().parents[2] / "data" / "odds_history.json"

_norm = norm  # compatibilité


def fetch_odds(league: str, markets: str = "h2h,totals", regions: str = "eu,uk") -> list[dict]:
    key = os.environ.get("ODDS_API_KEY")
    if not key or league not in SPORTS:
        return []
    data = get_json(f"https://api.the-odds-api.com/v4/sports/{SPORTS[league]}/odds",
                    {"apiKey": key, "regions": regions, "markets": markets, "oddsFormat": "decimal"},
                    ttl_s=1800, secret_params=("apiKey",))
    return data if isinstance(data, list) else []


def best_prices(event: dict) -> dict:
    """Meilleure cote par sélection (clés internes : 1, X, 2, O2.5, U2.5…) et bookmaker associé."""
    home, away, best = event["home_team"], event["away_team"], {}
    for bk in event.get("bookmakers", []):
        for mk in bk.get("markets", []):
            for o in mk.get("outcomes", []):
                if mk["key"] == "h2h":
                    k = "1" if o["name"] == home else "2" if o["name"] == away else "X"
                elif mk["key"] == "totals":
                    k = ("O" if o["name"] == "Over" else "U") + str(o.get("point"))
                else:
                    continue
                if o["price"] > best.get(k, (0, ""))[0]:
                    best[k] = (o["price"], bk["title"])
    return best


def find_event(events: list[dict], home: str, away: str) -> dict | None:
    for e in events:
        if same_team(e["home_team"], home) and same_team(e["away_team"], away):
            return e
    return None


def _record_history(snap: dict[str, dict]) -> None:
    """Ajoute les cotes du moment à l'historique (une entrée par match et par marché, seulement si elles changent)."""
    hist = json.loads(HISTORY.read_text()) if HISTORY.exists() else {}
    now = int(time.time())
    for mid, prices in snap.items():
        h = hist.setdefault(mid, {})
        for k, o in prices.items():
            series = h.setdefault(k, [])
            if not series or series[-1][1] != o:
                series.append([now, o])
                del series[:-60]
    HISTORY.write_text(json.dumps(hist, separators=(",", ":")))


def attach_odds(preds: list[dict]) -> int:
    """Ajoute cote, bookmaker et value aux prédictions ; renvoie le nombre de matchs appariés."""
    from ..value import kelly, value
    n, snap = 0, {}
    for league in {p["league"] for p in preds}:
        events = fetch_odds(league)
        for p in (x for x in preds if x["league"] == league):
            e = find_event(events, p["home"], p["away"])
            if not e:
                continue
            n += 1
            prices = best_prices(e)
            snap[p["id"]] = {k: o for k, (o, _) in prices.items()}
            for mk in p["markets"]:
                if mk["key"] in prices:
                    o, bk = prices[mk["key"]]
                    mk.update(odds=o, bookmaker=bk, value=round(value(mk["p"], o), 4), kelly=round(kelly(mk["p"], o), 4))
    if snap:
        _record_history(snap)
    return n
