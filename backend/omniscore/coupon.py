"""Coupons : Générer / Régénérer (on ne remplace une sélection que par une meilleure)."""
from __future__ import annotations

import math


def score(sel: dict, mode: str) -> float:
    p, ic, odds = sel["p"], sel.get("confidence", 50), sel.get("odds") or sel.get("fair_odds", 1 / sel["p"])
    if mode == "rendement":
        return odds * ic
    if mode == "equilibre":
        return math.sqrt(p) * p * odds * ic
    return p * ic


def candidates(preds: list[dict], pmin=0.70, pmax=0.98, mode="surete", exclude=(), max_risk_level=1) -> list[dict]:
    out = []
    for m in preds:
        if m["id"] in exclude or m.get("integrity_level", 0) > max_risk_level:
            continue
        ok = [x for x in m["markets"] if pmin <= x["p"] <= pmax and not x["key"].startswith("CS")]
        if ok:
            best = max(ok, key=lambda x: score(x, mode))
            out.append({**best, "match_id": m["id"], "match": f'{m["home"]} – {m["away"]}', "date": m["date"], "time": m.get("time")})
    return sorted(out, key=lambda x: score(x, mode), reverse=True)


def generate(preds, size, **kw) -> dict:
    sel = candidates(preds, **kw)[:size]
    return summarize(sel)


def regenerate(preds, current: list[dict], size, **kw) -> dict:
    """Garde chaque sélection sauf si une nouvelle a un pourcentage plus élevé ; les verrouillées restent."""
    fresh = candidates(preds, exclude={c["match_id"] for c in current}, **kw)
    locked = [c for c in current if c.get("locked")]
    free = sorted([c for c in current if not c.get("locked")], key=lambda c: c["p"], reverse=True)
    final, replaced = list(locked), 0
    for old in free:
        k = next((i for i, n in enumerate(fresh) if n["p"] > old["p"]), None)
        if k is None:
            final.append(old)
        else:
            final.append({**fresh.pop(k), "new": True}); replaced += 1
    while len(final) < size and fresh:
        final.append({**fresh.pop(0), "new": True}); replaced += 1
    res = summarize(final[:size])
    res["replaced"] = replaced
    res["message"] = (f"{replaced} sélection(s) remplacée(s) par un pourcentage plus élevé." if replaced
                      else "Coupon déjà optimal : les nouvelles sélections ont un pourcentage plus faible.")
    res["alternative"] = summarize(fresh[:size])
    return res


def summarize(sel: list[dict]) -> dict:
    p = math.prod(s["p"] for s in sel) if sel else 0.0
    odds = math.prod(s.get("odds") or s["fair_odds"] for s in sel) if sel else 0.0
    return {"selections": sel, "combined_probability": p, "total_odds": round(odds, 2), "size": len(sel)}
