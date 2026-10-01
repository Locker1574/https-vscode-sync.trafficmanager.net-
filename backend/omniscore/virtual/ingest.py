"""Import des résultats réels au format CSV (une ligne par événement, séparateur virgule).

Football : competition,datetime,home,away,hg,ag,hthg,htag,first
Penalty  : competition,datetime,home,away,kicks          (kicks = '1101...' dans l'ordre réel des tirs)
Jeu 21   : competition,datetime,player,dealer             (cartes séparées par '-', As = 11, figures = 10)
`competition` = code du catalogue (voir competitions.py). Une ligne sans résultat = événement à venir.
"""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .competitions import COMPETITIONS
from .football import VMatch
from .penalty import Shootout
from .twentyone import Hand


def _int(x: str):
    return int(x) if x not in ("", None) else None


def _cards(x: str):
    return [int(c) for c in x.split("-")] if x else None


def load_csv(path: Path) -> dict[str, list]:
    out: dict[str, list] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            code = row["competition"].strip()
            comp = COMPETITIONS[code]
            at = datetime.fromisoformat(row["datetime"].strip())
            eid = row.get("id") or f"{code}-{at.isoformat()}-{i}"
            if comp.kind == "football":
                ev = VMatch(code, eid, at, row["home"], row["away"], _int(row["hg"]), _int(row["ag"]),
                            _int(row.get("hthg", "")), _int(row.get("htag", "")), row.get("first") or None)
            elif comp.kind == "penalty":
                ev = Shootout(code, eid, at, row["home"], row["away"], row.get("kicks") or None)
            else:
                ev = Hand(code, eid, at, _cards(row.get("player", "")), _cards(row.get("dealer", "")))
            out.setdefault(code, []).append(ev)
    for evs in out.values():
        evs.sort(key=lambda e: e.at)
    return out
