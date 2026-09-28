"""Ligne de commande.

  python -m omniscore.cli predict   prédictions des 30 prochains jours (+ cotes, classements, absences si clés)
  python -m omniscore.cli live      matchs en direct → data/live.json
  python -m omniscore.cli backtest  backtest walk-forward sur données réelles

Clés facultatives (variables d'environnement) : ODDS_API_KEY, FOOTBALL_DATA_KEY, API_FOOTBALL_KEY, ALLSPORTS_KEY.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from .data.openfootball import load
from .engine import upcoming_predictions
from .providers import api_football, allsports, football_data
from .providers.names import same_team
from .providers.odds_api import attach_odds

DATA = Path(__file__).resolve().parents[1] / "data"


def load_matches(first: int = 2021):
    """Résultats openfootball complétés par football-data.org (scores récents et mi-temps)."""
    matches, n = football_data.enrich(load(first=first))
    if n:
        print(f"[football-data] {n} scores complétés")
    return matches


def attach_injuries(preds: list[dict]) -> int:
    inj = api_football.injuries({p["league"] for p in preds})
    n = 0
    for p in preds:
        for side in ("home", "away"):
            lst = next((v for k, v in inj.items() if same_team(k, p[side])), None)
            if lst:
                p.setdefault("absences", {})[side] = lst[:12]
                n += 1
    return n


def fetch_live() -> dict:
    """Direct : API-Football, puis AllSportsApi en secours."""
    matches = api_football.live() or allsports.live()
    return {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "matches": matches}


def main():
    ap = argparse.ArgumentParser(prog="omniscore")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("predict", help="prédire les matchs à venir")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--out", type=Path, default=DATA / "predictions.json")
    sub.add_parser("live", help="matchs en direct")
    sub.add_parser("backtest", help="backtest walk-forward sur données réelles")
    a = ap.parse_args()
    if a.cmd == "backtest":
        from .backtest import main as bt
        bt()
        return
    if a.cmd == "live":
        live = fetch_live()
        (DATA / "live.json").write_text(json.dumps(live, ensure_ascii=False, indent=1))
        print(f"{len(live['matches'])} matchs en direct → data/live.json")
        return
    preds = upcoming_predictions(load_matches(), date.today(), a.days)
    n_odds = attach_odds(preds)
    n_ctx = football_data.attach_context(preds)
    n_abs = attach_injuries(preds)
    standings = football_data.standings_all(sorted({p["league"] for p in preds}))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({"generated": date.today().isoformat(), "with_odds": n_odds, "with_context": n_ctx,
                                 "standings": standings, "matches": preds}, ensure_ascii=False, indent=1))
    live = fetch_live()
    (DATA / "live.json").write_text(json.dumps(live, ensure_ascii=False, indent=1))
    print(f"{len(preds)} matchs prédits · {n_odds} avec cotes · {n_ctx} avec classement · {n_abs} équipes avec absences · "
          f"{len(live['matches'])} en direct → {a.out}")


if __name__ == "__main__":
    main()
