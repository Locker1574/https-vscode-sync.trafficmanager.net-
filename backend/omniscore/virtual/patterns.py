"""Tests statistiques de régularité du générateur (« y a-t-il un motif exploitable ? »).

Un jeu virtuel honnête est une suite de tirages indépendants : on s'attend à ce que tous ces tests
passent (p-valeur > 0,01). Si l'un échoue de façon répétée sur beaucoup de données, cela signale
une dépendance à examiner — jamais une garantie de gain.
- Test des séquences de Wald-Wolfowitz (runs test) sur une suite binaire.
- Autocorrélation et test de Ljung-Box (retards 1 à 5) sur une série numérique.
- Khi-deux d'ajustement (ex. valeurs des cartes contre la composition du sabot).
"""
from __future__ import annotations

import numpy as np
from scipy import stats

ALPHA = 0.01


def runs_test(x) -> dict:
    x = np.asarray(x, bool)
    n1, n2 = int(x.sum()), int((~x).sum())
    n = n1 + n2
    if n1 == 0 or n2 == 0:
        return {"test": "séquences", "p": 1.0}
    runs = 1 + int((x[1:] != x[:-1]).sum())
    mu = 2 * n1 * n2 / n + 1
    var = 2 * n1 * n2 * (2 * n1 * n2 - n) / (n ** 2 * (n - 1))
    z = (runs - mu) / np.sqrt(var)
    return {"test": "séquences (Wald-Wolfowitz)", "z": round(float(z), 3), "p": round(float(2 * stats.norm.sf(abs(z))), 4)}


def ljung_box(x, lags: int = 5) -> dict:
    x = np.asarray(x, float) - np.mean(x)
    n = len(x)
    den = (x ** 2).sum()
    ac = [float((x[k:] * x[:-k]).sum() / den) for k in range(1, lags + 1)]
    q = n * (n + 2) * sum(r ** 2 / (n - k) for k, r in enumerate(ac, 1))
    return {"test": f"autocorrélation (Ljung-Box, {lags} retards)", "acf": [round(a, 4) for a in ac],
            "p": round(float(stats.chi2.sf(q, lags)), 4)}


def chi2_fit(observed, expected_p) -> dict:
    o = np.asarray(observed, float)
    e = np.asarray(expected_p, float) * o.sum()
    chi, p = stats.chisquare(o, e)
    return {"test": "khi-deux d'ajustement", "chi2": round(float(chi), 2), "p": round(float(p), 4)}


def analyse(kind: str, events: list) -> dict:
    ev = [e for e in events if e.played]
    if kind == "football":
        tests = [runs_test([e.hg > e.ag for e in ev]) | {"serie": "victoires à domicile"},
                 ljung_box([e.hg + e.ag for e in ev]) | {"serie": "total de buts"}]
    elif kind == "penalty":
        kicks = "".join(e.kicks for e in ev)
        tests = [runs_test([c == "1" for c in kicks]) | {"serie": "tirs réussis / ratés"},
                 ljung_box([sum(e.score) for e in ev]) | {"serie": "tirs réussis par séance"}]
    else:
        cards = [c for e in ev for c in e.player + e.dealer]
        firsts = [e.player[0] for e in ev]
        ranks = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
        exp = [4 / 52] * 8 + [16 / 52, 4 / 52]
        tests = [chi2_fit([firsts.count(r) for r in ranks], exp) | {"serie": "1re carte du joueur vs sabot"},
                 ljung_box([min(sum(e.player), 30) for e in ev]) | {"serie": "total du joueur"},
                 {"test": "fréquence globale des cartes", "serie": f"{len(cards)} cartes", "p": None}]
    ok = all(t["p"] is None or t["p"] > ALPHA for t in tests)
    return {"events": len(ev), "tests": tests,
            "verdict": "Aucun motif exploitable détecté : les tirages se comportent comme du hasard indépendant."
            if ok else "Écart statistique détecté : à surveiller sur plus de données (ce n'est pas une garantie de gain)."}
