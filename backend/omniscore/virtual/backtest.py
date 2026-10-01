"""Backtest walk-forward par compétition : le modèle ne voit jamais que le passé.

1. Les 40 % premiers événements servent d'historique initial.
2. Le reste est découpé en blocs ; avant chaque bloc, le modèle est réajusté sur tout ce qui précède,
   puis il prédit chaque événement du bloc. Chaque option est réglée avec le vrai résultat.
3. La calibration est apprise sur la 1re moitié des prédictions et évaluée sur la 2de moitié
   (hors échantillon) : les taux de réussite publiés par niveau de confiance sont donc honnêtes.
"""
from __future__ import annotations

import json
from collections import defaultdict

import numpy as np

from ..calibration import brier, buckets
from .competitions import COMPETITIONS
from .predictor import DATA, P_MAX, VCalibrator, VirtualModel, settle, tier, vfamily


def run(code: str, events: list, block: int = 150, start_frac: float = 0.4) -> list[dict]:
    """Renvoie une ligne par (événement, option) : p brute, résultat 0/1."""
    rows = []
    start = int(len(events) * start_frac)
    empty = VCalibrator({})
    for b in range(start, len(events), block):
        model = VirtualModel(code, events[:b], events[b].at, calib=empty)
        for ev in events[b:b + block]:
            for x in model.raw_markets(ev):
                r = settle(code, x["key"], ev)
                if r in ("V", "P"):
                    rows.append({"ev": ev.id, "key": x["key"], "p": x["p"], "y": int(r == "V")})
    return rows


def evaluate(rows: list[dict], calib: VCalibrator) -> dict:
    """Mesures hors échantillon : calibration, Brier, réussite par niveau et du pick principal."""
    ps = np.array([calib(r["key"], r["p"]) if not r["key"].startswith(("CS", "PCS")) else r["p"] for r in rows])
    ys = np.array([r["y"] for r in rows])
    by_tier: dict = defaultdict(lambda: [0, 0, 0.0])
    for p, y in zip(ps, ys):
        t = tier(p)["name"]
        by_tier[t][0] += 1; by_tier[t][1] += y; by_tier[t][2] += p
    picks: dict = {}
    for r, p in zip(rows, ps):  # pick principal = option la plus probable ≤ P_MAX
        if p <= P_MAX and (r["ev"] not in picks or p > picks[r["ev"]][0]):
            picks[r["ev"]] = (p, r["y"], r["key"])
    pk = np.array([v[:2] for v in picks.values()]) if picks else np.zeros((0, 2))
    fam: dict = defaultdict(lambda: [0, 0])
    for v in picks.values():
        fam[vfamily(v[2])][0] += 1; fam[vfamily(v[2])][1] += v[1]
    return {
        "predictions": int(len(rows)), "events": len({r["ev"] for r in rows}),
        "brier": round(brier(ps, ys), 4),
        "calibration": buckets(list(zip(ps, ys)), edges=(0.0, 0.5, 0.65, 0.8, 0.9, P_MAX, 1.0001)),
        "by_tier": {k: {"n": n, "annonce": round(s / n, 3), "observe": round(h / n, 3)} for k, (n, h, s) in by_tier.items()},
        "pick": {"n": int(len(pk)), "annonce": round(float(pk[:, 0].mean()), 3) if len(pk) else None,
                 "observe": round(float(pk[:, 1].mean()), 3) if len(pk) else None,
                 "marches": {k: {"n": n, "observe": round(h / n, 3)} for k, (n, h) in sorted(fam.items(), key=lambda kv: -kv[1][0])}},
    }


def backtest_all(histories: dict[str, list], block: int = 150) -> dict:
    report, calib_rows = {}, defaultdict(list)
    per_code = {}
    for code, events in histories.items():
        rows = run(code, events, block)
        per_code[code] = rows
        half = len({r["ev"] for r in rows}) // 2
        evs = list(dict.fromkeys(r["ev"] for r in rows))[:half]
        first = set(evs)
        calib_rows[COMPETITIONS[code].kind] += [(r["key"], r["p"], r["y"]) for r in rows if r["ev"] in first]
    calibs = {k: VCalibrator({}).fit(v) for k, v in calib_rows.items()}
    for code, rows in per_code.items():
        evs = list(dict.fromkeys(r["ev"] for r in rows))
        second = set(evs[len(evs) // 2:])
        test = [r for r in rows if r["ev"] in second]
        report[code] = {"name": COMPETITIONS[code].name, "kind": COMPETITIONS[code].kind,
                        "brut": evaluate(test, VCalibrator({})), "calibre": evaluate(test, calibs[COMPETITIONS[code].kind])}
    return {"report": report, "calibration": {k: c.maps for k, c in calibs.items()}}


def save(result: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "calibration.json").write_text(json.dumps(result["calibration"]))
    (DATA / "backtest.json").write_text(json.dumps(result["report"], ensure_ascii=False, indent=1))
