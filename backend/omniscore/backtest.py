"""Backtest walk-forward sur données réelles : le modèle ne voit jamais le futur.

Pour chaque ligue et chaque semaine des saisons testées, on ajuste Dixon-Coles et Elo
uniquement sur les matchs antérieurs, puis on prédit les matchs de la semaine.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

import numpy as np

from .calibration import Calibrator, brier, buckets, log_loss, rps
from .data.openfootball import LEAGUES, load
from .engine import CALIB_PATH, confidence, run_elo
from .markets import markets, settle
from .models.dixon_coles import DixonColes

OUT = Path(__file__).resolve().parents[1] / "data" / "backtest.json"


def walk_forward(matches, test_from_season: str):
    rows = []
    for code in sorted({m.league for m in matches}):
        hist = [m for m in matches if m.league == code]
        tests = [m for m in hist if m.played and m.season >= test_from_season]
        weeks = defaultdict(list)
        for m in tests:
            weeks[m.date - timedelta(days=m.date.weekday())].append(m)
        for wk in sorted(weeks):
            try:
                dc = DixonColes().fit(hist, wk)
            except ValueError:
                continue
            elo, _, _ = run_elo(hist, wk)
            base = [m for m in hist if m.played and m.date < wk][-760:]
            fb = np.array([np.mean([m.hg > m.ag for m in base]), np.mean([m.hg == m.ag for m in base]), np.mean([m.hg < m.ag for m in base])])
            for m in weeks[wk]:
                M, HT = dc.matrix(m.home, m.away), dc.ht_matrix(m.home, m.away)
                i, j = np.indices(M.shape)
                pdc = np.array([M[i > j].sum(), np.trace(M), M[i < j].sum()])
                pel = np.array(elo.probs(m.home, m.away))
                comp = min(1.0, min(dc.n_matches.get(m.home, 0), dc.n_matches.get(m.away, 0)) / 20)
                rows.append({
                    "league": code, "season": m.season, "date": m.date.isoformat(), "home": m.home, "away": m.away,
                    "score": [m.hg, m.ag], "ht": [m.hthg, m.htag],
                    "dc": pdc.tolist(), "elo": pel.tolist(), "base": fb.tolist(),
                    "agree": float(1 - np.abs(pdc - pel).max()), "comp": comp,
                    "mk": {x["key"]: x["p"] for x in markets(M, HT, m.home, m.away) if not x["key"].startswith("CS")},
                })
    return rows


def evaluate(rows, calib: Calibrator | None = None):
    Y = np.array([[r["score"][0] > r["score"][1], r["score"][0] == r["score"][1], r["score"][0] < r["score"][1]] for r in rows], float)
    res = {"n": len(rows)}
    for name in ("base", "elo", "dc"):
        P = np.array([r[name] for r in rows])
        res[name] = {"log_loss": log_loss(P, Y), "brier": brier(P, Y), "rps": rps(P, Y), "accuracy": float((P.argmax(1) == Y.argmax(1)).mean())}
    Pb = np.array([0.75 * np.array(r["dc"]) + 0.25 * np.array(r["elo"]) for r in rows])
    res["blend"] = {"log_loss": log_loss(Pb, Y), "brier": brier(Pb, Y), "rps": rps(Pb, Y), "accuracy": float((Pb.argmax(1) == Y.argmax(1)).mean())}
    # marchés binaires
    bin_rows = []
    for r in rows:
        for k, p in r["mk"].items():
            s = settle(k, r["score"][0], r["score"][1], r["ht"][0], r["ht"][1])
            if s in ("V", "P"):
                pc = calib(k, p) if calib else p
                bin_rows.append((k, pc, 1 if s == "V" else 0, r))
    res["calibration_all_markets"] = buckets([(p, y) for _, p, y, _ in bin_rows])
    # la meilleure sélection 70-98 % de chaque match (comme le coupon de l'app)
    per = defaultdict(list)
    for k, p, y, rr in bin_rows:
        if 0.70 <= p <= 0.98 and not k.startswith("DNB"):
            per[id(rr)].append((k, p, y))
    picks = []
    for r in rows:
        cand = per.get(id(r))
        if cand:
            k, p, y = max(cand, key=lambda c: confidence(c[1], r["agree"], max(r["comp"], 0.3)))
            picks.append((p, y, k, r["date"]))
    res["top_picks"] = {"n": len(picks), "hit_rate": float(np.mean([y for _, y, _, _ in picks])) if picks else None,
                        "mean_p": float(np.mean([p for p, _, _, _ in picks])) if picks else None,
                        "by_bucket": buckets([(p, y) for p, y, _, _ in picks], (0.7, 0.8, 0.9, 0.98)),
                        "by_market": _by_market(picks)}
    res["coupons"] = _coupons(picks)
    return res, bin_rows


def _by_market(picks):
    d = defaultdict(list)
    for p, y, k, _ in picks:
        d[k].append((p, y))
    return sorted([{"market": k, "n": len(v), "mean_p": float(np.mean([a for a, _ in v])), "hit_rate": float(np.mean([b for _, b in v]))}
                   for k, v in d.items() if len(v) >= 20], key=lambda x: -x["n"])[:12]


def _coupons(picks):
    """Un coupon par jour avec les N sélections les plus probables du jour (hors mêmes marchés rares)."""
    by_day = defaultdict(list)
    for p, y, k, d in picks:
        by_day[d].append((p, y))
    out = {}
    for n in (2, 3, 5):
        exp, won = [], []
        for d, v in by_day.items():
            if len(v) >= n:
                top = sorted(v, reverse=True)[:n]
                exp.append(math.prod(p for p, _ in top)); won.append(all(y for _, y in top))
        out[str(n)] = {"coupons": len(won), "predicted_win_rate": float(np.mean(exp)) if exp else None,
                       "observed_win_rate": float(np.mean(won)) if won else None}
    return out


def main():
    cache = OUT.with_name("backtest_rows.json")
    if cache.exists():
        rows = json.loads(cache.read_text())
    else:
        rows = walk_forward(load(first=2020), "2023-24")
        cache.write_text(json.dumps(rows))
    last = max(r["season"] for r in rows if r["season"] < "2026-27")
    train = [r for r in rows if r["season"] < last]
    test = [r for r in rows if r["season"] >= last]
    # calibration apprise sur les saisons antérieures, évaluée sur la dernière saison complète et la saison en cours
    tmp_eval, bin_train = evaluate(train)
    calib = Calibrator().fit((k, p, y) for k, p, y, _ in bin_train)
    raw, _ = evaluate(test)
    cal, _ = evaluate(test, calib)
    # calibration finale apprise sur tout l'historique, utilisée en production
    _, bin_all = evaluate(rows)
    Calibrator().fit((k, p, y) for k, p, y, _ in bin_all).save(CALIB_PATH)
    report = {"leagues": {k: LEAGUES[k] for k in sorted({r["league"] for r in rows})},
              "train_seasons": sorted({r["season"] for r in train}), "test_seasons": sorted({r["season"] for r in test}),
              "all_seasons": evaluate(rows)[0], "test_raw": raw, "test_calibrated": cal,
              "per_league": {code: evaluate([r for r in rows if r["league"] == code])[0]["dc"] for code in sorted({r["league"] for r in rows})}}
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False, default=float))
    t = report["test_calibrated"]
    print(f"Matchs testés : {report['all_seasons']['n']} (test final {t['n']})")
    for name in ("base", "elo", "dc", "blend"):
        a = report["all_seasons"][name]
        print(f"  {name:6s} log-loss {a['log_loss']:.4f}  RPS {a['rps']:.4f}  Brier {a['brier']:.4f}  précision {a['accuracy']:.1%}")
    tp = t["top_picks"]
    print(f"Sélections 70-98 % (test calibré) : {tp['n']}, proba moyenne {tp['mean_p']:.1%}, réussite {tp['hit_rate']:.1%}")
    for n, c in t["coupons"].items():
        print(f"  coupon de {n} : prévu {c['predicted_win_rate']:.1%}, observé {c['observed_win_rate']:.1%} sur {c['coupons']}")


if __name__ == "__main__":
    main()
