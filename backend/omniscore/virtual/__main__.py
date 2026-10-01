"""Ligne de commande du module virtuel.

python -m omniscore.virtual demo            # données simulées → backtest, calibration, prédictions, journal → data/virtual/demo.json
python -m omniscore.virtual csv FICHIER.csv # mêmes étapes sur vos résultats réels importés
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np

from . import backtest as bt
from . import demo as dm
from .competitions import COMPETITIONS
from .ingest import load_csv
from .journal import Journal
from .patterns import analyse
from .predictor import DATA, VirtualModel, load_calibrator

UPCOMING, JOURNAL_N = 4, 40


def build(histories: dict[str, list], upcoming: dict[str, list], simulated: bool, odds_demo: bool) -> dict:
    print("Backtest walk-forward…")
    res = bt.backtest_all(histories, block=200)
    bt.save(res)
    journal = Journal(DATA / ("journal_demo.json" if simulated else "journal.json"))
    if simulated:
        journal.items = []
    comps = []
    for code, events in histories.items():
        comp = COMPETITIONS[code]
        calib = load_calibrator(code)
        # journal : picks figés avant chaque événement des JOURNAL_N derniers, puis réglés
        cut = len(events) - JOURNAL_N
        model = VirtualModel(code, events[:cut], events[cut].at, calib)
        for ev in events[cut:]:
            journal.freeze(model.predict(ev))
            journal.settle(code, ev)
        model = VirtualModel(code, events, upcoming[code][0].at if upcoming.get(code) else events[-1].at, calib)
        rng = np.random.default_rng(len(code))
        preds = []
        for ev in upcoming.get(code, []):
            raw = {x["key"]: x["p"] for x in model.raw_markets(ev)}
            odds = {k: dm.bookmaker_odds(p, rng) for k, p in raw.items() if not k.startswith(("CS", "PCS", "SER"))} if odds_demo else None
            preds.append(model.predict(ev, odds))
        comps.append({"code": code, "name": comp.name, "kind": comp.kind, "history_events": len(events),
                      "upcoming": preds, "backtest": res["report"][code], "patterns": analyse(comp.kind, events),
                      "journal": [i for i in journal.items if i["competition"] == code][-12:]})
        print(f"  {comp.name}: {len(events)} événements, pick principal observé "
              f"{res['report'][code]['calibre']['pick']['observe']:.1%} (annoncé {res['report'][code]['calibre']['pick']['annonce']:.1%})")
    journal.save()
    return {"generated": datetime.now().isoformat(timespec="minutes"), "simulated": simulated,
            "competitions": comps, "journal_stats": journal.stats()}


def main():
    ap = argparse.ArgumentParser(prog="omniscore.virtual")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo", help="pipeline complet sur données simulées")
    d.add_argument("--events", type=int, default=2000)
    c = sub.add_parser("csv", help="pipeline complet sur un CSV de résultats réels")
    c.add_argument("path", type=Path)
    a = ap.parse_args()
    if a.cmd == "demo":
        hist, up = {}, {}
        for code in COMPETITIONS:
            evs = dm.history(code, a.events + UPCOMING)
            hist[code], up[code] = evs[: a.events], [_hide(e) for e in evs[a.events:]]
        out = build(hist, up, simulated=True, odds_demo=True)
        path = DATA / "demo.json"
    else:
        data = load_csv(a.path)
        hist = {k: [e for e in v if e.played] for k, v in data.items()}
        up = {k: [e for e in v if not e.played] for k, v in data.items()}
        out = build(hist, up, simulated=False, odds_demo=False)
        path = DATA / "latest.json"
    path.write_text(json.dumps(out, ensure_ascii=False))
    print(f"→ {path}")


def _hide(ev):
    """Événement à venir : on retire le résultat."""
    from dataclasses import replace
    if hasattr(ev, "kicks"):
        return replace(ev, kicks=None)
    if hasattr(ev, "player"):
        return replace(ev, player=None, dealer=None)
    return replace(ev, hg=None, ag=None, hthg=None, htag=None, first=None)


if __name__ == "__main__":
    main()
