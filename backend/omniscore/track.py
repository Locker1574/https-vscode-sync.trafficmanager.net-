"""Journal réel : chaque prédiction est figée avant le match, puis réglée avec le résultat officiel.

C'est la preuve en conditions réelles (pas de backtest) : rien n'est modifié après coup.
Usage : python -m omniscore.track   (après python -m omniscore.cli predict)
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np

from .calibration import rps
from .data.openfootball import load
from .markets import settle

DATA = Path(__file__).resolve().parents[1] / "data"
TRACK = DATA / "track.json"
TRIVIAL = {"O0.5", "U4.5", "HO0.5", "AO0.5"}
KEYS = ("1", "X", "2", "O1.5", "O2.5", "U2.5", "BTTS_Y", "BTTS_N", "1X", "X2")


def pick(markets, trivial=False):
    ok = [x for x in markets if 0.70 <= x["p"] <= 0.98 and not x["key"].startswith(("CS", "DNB")) and (trivial or x["key"] not in TRIVIAL)]
    return max(ok, key=lambda x: x["confidence"]) if ok else None


def freeze(preds: list[dict], track: dict, today: date) -> int:
    """Ajoute les nouveaux matchs à venir ; une prédiction déjà figée n'est jamais réécrite."""
    n = 0
    for p in preds:
        if p["id"] in track or date.fromisoformat(p["date"]) < today:
            continue
        mk = {x["key"]: x for x in p["markets"]}
        pk = pick(p["markets"])
        track[p["id"]] = {"league": p["league"], "date": p["date"], "home": p["home"], "away": p["away"], "frozen": today.isoformat(),
                          "p": {k: round(mk[k]["p"], 4) for k in KEYS if k in mk},
                          "pick": {"key": pk["key"], "label": pk["label"], "p": round(pk["p"], 4)} if pk else None,
                          "result": None, "status": None}
        n += 1
    return n


def settle_all(track: dict, matches) -> int:
    res = {m.id: m for m in matches if m.played}
    n = 0
    for mid, t in track.items():
        m = res.get(mid)
        if not m or t["result"]:
            continue
        t["result"] = [m.hg, m.ag]
        t["status"] = {k: settle(k, m.hg, m.ag) for k in t["p"]}
        if t["pick"]:
            t["pick"]["status"] = settle(t["pick"]["key"], m.hg, m.ag, m.hthg, m.htag)
        n += 1
    return n


def summary(track: dict) -> dict:
    done = [t for t in track.values() if t["result"]]
    picks = [t["pick"] for t in done if t["pick"] and t["pick"].get("status") in ("V", "P")]
    out = {"frozen": len(track), "settled": len(done), "pending": len(track) - len(done),
           "picks": len(picks), "picks_won": sum(p["status"] == "V" for p in picks),
           "picks_mean_p": float(np.mean([p["p"] for p in picks])) if picks else None}
    if done:
        P = np.array([[t["p"]["1"], t["p"]["X"], t["p"]["2"]] for t in done])
        Y = np.array([[t["result"][0] > t["result"][1], t["result"][0] == t["result"][1], t["result"][0] < t["result"][1]] for t in done], float)
        out["rps"], out["accuracy"] = rps(P, Y), float((P.argmax(1) == Y.argmax(1)).mean())
    out["recent"] = sorted(
        [{"date": t["date"], "league": t["league"], "match": f'{t["home"]} – {t["away"]}', "result": t["result"],
          "pick": t["pick"]} for t in done], key=lambda x: x["date"], reverse=True)[:30]
    return out


def main():
    track = json.loads(TRACK.read_text()) if TRACK.exists() else {}
    preds = json.loads((DATA / "predictions.json").read_text())["matches"]
    today = date.today()
    a = freeze(preds, track, today)
    b = settle_all(track, load(first=today.year - 1))
    TRACK.write_text(json.dumps(track, ensure_ascii=False, indent=0))
    s = summary(track)
    (DATA / "track_summary.json").write_text(json.dumps(s, ensure_ascii=False, indent=1))
    print(f"{a} prédictions figées, {b} réglées ; total {s['frozen']} dont {s['settled']} réglées, sélections {s['picks_won']}/{s['picks']}")


if __name__ == "__main__":
    main()
