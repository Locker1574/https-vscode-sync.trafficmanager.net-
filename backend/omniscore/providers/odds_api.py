"""Cotes réelles via The Odds API (https://the-odds-api.com), clé dans ODDS_API_KEY.

Sans clé, l'application fonctionne sans value bets (probabilités seules).
"""
from __future__ import annotations

import json
import os
import unicodedata
import urllib.parse
import urllib.request

SPORTS = {"en.1": "soccer_epl", "es.1": "soccer_spain_la_liga", "it.1": "soccer_italy_serie_a",
          "de.1": "soccer_germany_bundesliga", "fr.1": "soccer_france_ligue_one"}


def _norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    for w in (" fc", " cf", " afc", " sc", " ac", "fc ", "ac ", "ssc ", "as ", "rc ", "1. ", " 1901", " 1909", " 04", " calcio"):
        s = s.replace(w, " ")
    return " ".join(s.split())


def fetch_odds(league: str, markets: str = "h2h,totals", regions: str = "eu,uk") -> list[dict]:
    key = os.environ.get("ODDS_API_KEY")
    if not key or league not in SPORTS:
        return []
    q = urllib.parse.urlencode({"apiKey": key, "regions": regions, "markets": markets, "oddsFormat": "decimal"})
    with urllib.request.urlopen(f"https://api.the-odds-api.com/v4/sports/{SPORTS[league]}/odds?{q}", timeout=30) as r:  # noqa: S310
        return json.loads(r.read())


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


def attach_odds(preds: list[dict]) -> int:
    """Ajoute cote, bookmaker et value aux prédictions ; renvoie le nombre de matchs appariés."""
    from ..value import kelly, value
    n = 0
    for league in {p["league"] for p in preds}:
        events = fetch_odds(league)
        idx = {(_norm(e["home_team"]), _norm(e["away_team"])): e for e in events}
        for p in (x for x in preds if x["league"] == league):
            e = idx.get((_norm(p["home"]), _norm(p["away"])))
            if not e:
                continue
            n += 1
            prices = best_prices(e)
            for mk in p["markets"]:
                if mk["key"] in prices:
                    o, bk = prices[mk["key"]]
                    mk.update(odds=o, bookmaker=bk, value=round(value(mk["p"], o), 4), kelly=round(kelly(mk["p"], o), 4))
    return n
