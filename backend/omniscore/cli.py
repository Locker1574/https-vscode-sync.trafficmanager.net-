"""Ligne de commande : python -m omniscore.cli predict --days 14 --out data/predictions.json"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .data.openfootball import load
from .engine import upcoming_predictions
from .providers.odds_api import attach_odds


def main():
    ap = argparse.ArgumentParser(prog="omniscore")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("predict", help="prédire les matchs à venir")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--out", type=Path, default=Path("data/predictions.json"))
    sub.add_parser("backtest", help="backtest walk-forward sur données réelles")
    a = ap.parse_args()
    if a.cmd == "backtest":
        from .backtest import main as bt
        bt()
        return
    preds = upcoming_predictions(load(first=2021), date.today(), a.days)
    n = attach_odds(preds)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({"generated": date.today().isoformat(), "with_odds": n, "matches": preds}, ensure_ascii=False, indent=1))
    print(f"{len(preds)} matchs prédits ({n} avec cotes) → {a.out}")


if __name__ == "__main__":
    main()
