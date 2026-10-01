"""Journal des pronostics : chaque pick est figé AVANT l'événement, puis réglé avec le résultat.

Un pronostic n'est jamais réécrit après coup : c'est la preuve en conditions réelles,
distincte du backtest. Statuts : VALIDÉ ✅, PERDU ❌, REMBOURSÉ ↩️, EN ATTENTE ⏳.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from .predictor import DATA, STATUS, settle, vfamily

PATH = DATA / "journal.json"


class Journal:
    def __init__(self, path: Path = PATH):
        self.path = path
        self.items: list[dict] = json.loads(path.read_text()) if path.exists() else []

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.items, ensure_ascii=False, indent=1))

    def freeze(self, pred: dict, options: int = 1) -> list[dict]:
        """Enregistre le pick principal (et les `options` - 1 suivants) d'une prédiction."""
        known = {(i["event"], i["key"]) for i in self.items}
        picks = [pred["pick"]] + [m for m in pred["markets"] if m is not pred["pick"] and m["p"] <= pred["pick"]["p"]][: options - 1]
        added = []
        for m in picks:
            if (pred["id"], m["key"]) in known:
                continue
            item = {"event": pred["id"], "competition": pred["competition"], "competition_name": pred["competition_name"],
                    "at": pred["at"], "match": f'{pred["home"]} – {pred["away"]}', "key": m["key"], "label": m["label"],
                    "p": m["p"], "tier": m["tier"], "odds": m.get("odds"), "result": None, "status": STATUS[None]}
            self.items.append(item); added.append(item)
        return added

    def settle(self, code: str, event) -> int:
        n = 0
        for i in self.items:
            if i["event"] == event.id and i["result"] is None:
                r = settle(code, i["key"], event)
                if r is not None:
                    i["result"], i["status"] = r, STATUS[r]
                    n += 1
        return n

    def stats(self) -> dict:
        done = [i for i in self.items if i["result"] in ("V", "P")]

        def summary(xs):
            if not xs:
                return {"n": 0}
            hit = [i["result"] == "V" for i in xs]
            out = {"n": len(xs), "valides": int(sum(hit)), "perdus": len(xs) - int(sum(hit)),
                   "reussite": round(float(np.mean(hit)), 3), "annonce": round(float(np.mean([i["p"] for i in xs])), 3)}
            with_odds = [i for i in xs if i.get("odds")]
            if with_odds:
                profit = sum((i["odds"] - 1) if i["result"] == "V" else -1 for i in with_odds)
                out["roi"] = round(profit / len(with_odds), 3)
            return out

        streak, last = 0, None
        for i in reversed(done):
            if last is None or i["result"] == last:
                streak += 1; last = i["result"]
            else:
                break
        groups = lambda f: {k: summary(v) for k, v in _group(done, f).items()}
        return {"global": summary(done), "en_attente": sum(i["result"] is None for i in self.items),
                "serie": {"type": STATUS.get(last, ""), "longueur": streak},
                "par_competition": groups(lambda i: i["competition_name"]),
                "par_niveau": groups(lambda i: f'{i["tier"]["icon"]} {i["tier"]["name"]}'),
                "par_marche": groups(lambda i: vfamily(i["key"]))}


def _group(xs, f):
    g = defaultdict(list)
    for x in xs:
        g[f(x)].append(x)
    return g
