"""Séances de tirs au but : modèle de Markov tir par tir, résolu exactement.

Chaque équipe a un taux de réussite p estimé par un a priori Beta(a, b) mis à jour par
ses tirs passés (pondérés dans le temps) : p̂ = (a + réussis) / (a + b + tentés).
Séance : 5 tirs chacun en alternance (dom d'abord), arrêt dès qu'une équipe ne peut plus
être rattrapée, puis mort subite par paires jusqu'à ce qu'une seule équipe marque.
La loi exacte du score final s'obtient par programmation dynamique sur (tir, buts dom, buts ext).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from math import comb

import numpy as np

PRIOR_A, PRIOR_B = 7.5, 2.5   # a priori : 75 % de réussite, poids de 10 tirs
SD_ROUNDS = 15                # tours de mort subite modélisés (le reste est négligeable)


@dataclass(frozen=True)
class Shootout:
    """`kicks` : suite de '1'/'0' dans l'ordre réel des tirs (dom, ext, dom, ext, ...)."""
    comp: str
    id: str
    at: datetime
    home: str
    away: str
    kicks: str | None = None

    @property
    def played(self) -> bool:
        return self.kicks is not None

    @property
    def score(self) -> tuple[int, int]:
        k = self.kicks or ""
        return k[0::2].count("1"), k[1::2].count("1")


def rates(history: list[Shootout], ref: datetime, half_life_days: float = 14.0) -> dict[str, float]:
    made, taken = defaultdict(float), defaultdict(float)
    for s in history:
        if not s.played or s.at >= ref:
            continue
        w = 0.5 ** ((ref - s.at).total_seconds() / 86400 / half_life_days)
        for team, seq in ((s.home, s.kicks[0::2]), (s.away, s.kicks[1::2])):
            made[team] += w * seq.count("1"); taken[team] += w * len(seq)
    return {t: (PRIOR_A + made[t]) / (PRIOR_A + PRIOR_B + taken[t]) for t in taken}


def rate(r: dict[str, float], team: str) -> float:
    return r.get(team, PRIOR_A / (PRIOR_A + PRIOR_B))


def distribution(pa: float, pb: float) -> dict[tuple[int, int], float]:
    """Loi exacte du score final (dom, ext). Les scores de mort subite vont jusqu'à 5+SD_ROUNDS."""
    out: dict[tuple[int, int], float] = defaultdict(float)
    state = {(0, 0): 1.0}  # (buts dom, buts ext) après k tirs
    for k in range(10):
        nxt: dict = defaultdict(float)
        home_kicks = k % 2 == 0
        p = pa if home_kicks else pb
        for (a, b), q in state.items():
            for hit, w in ((1, p), (0, 1 - p)):
                na, nb = (a + hit, b) if home_kicks else (a, b + hit)
                done = k + 1
                ra, rb = 5 - (done + 1) // 2, 5 - done // 2  # tirs restants dom / ext
                if na > nb + rb or nb > na + ra:
                    out[(na, nb)] += q * w
                else:
                    nxt[(na, nb)] += q * w
        state = nxt
    both, none_ = pa * pb, (1 - pa) * (1 - pb)
    for (a, b), q in state.items():  # égalité après 5 tirs → mort subite
        for extra in range(SD_ROUNDS):
            # `extra` tours où les deux marquent ou ratent, dont j où les deux marquent
            for j in range(extra + 1):
                c = q * _binom(extra, j) * both ** j * none_ ** (extra - j)
                out[(a + j + 1, b + j)] += c * pa * (1 - pb)
                out[(a + j, b + j + 1)] += c * (1 - pa) * pb
    return dict(out)


def _binom(n: int, k: int) -> float:
    return float(comb(n, k))


def markets(pa: float, pb: float, home: str, away: str) -> list[dict]:
    D = distribution(pa, pb)
    tot = sum(D.values())
    D = {k: v / tot for k, v in D.items()}
    out = []

    def add(group, key, label, p):
        out.append({"group": group, "key": key, "label": label, "p": float(np.clip(p, 0, 1))})

    ph = sum(v for (a, b), v in D.items() if a > b)
    add("Vainqueur", "P1", f"{home} gagne la séance", ph)
    add("Vainqueur", "P2", f"{away} gagne la séance", 1 - ph)
    sd = _sudden_death(pa, pb)  # mort subite ⇔ égalité après 5 tirs chacun
    add("Déroulé", "SD_Y", "Mort subite : oui", sd)
    add("Déroulé", "SD_N", "Mort subite : non", 1 - sd)
    for L in (5.5, 6.5, 7.5, 8.5):
        po = sum(v for (a, b), v in D.items() if a + b > L)
        add("Tirs réussis", f"PO{L}", f"Plus de {str(L).replace('.', ',')} tirs réussis", po)
        add("Tirs réussis", f"PU{L}", f"Moins de {str(L).replace('.', ',')} tirs réussis", 1 - po)
    for side, name, idx in (("H", home, 0), ("A", away, 1)):
        for L in (3.5, 4.5):
            po = sum(v for k, v in D.items() if k[idx] > L)
            add("Équipes", f"P{side}O{L}", f"{name} plus de {str(L).replace('.', ',')} tirs réussis", po)
            add("Équipes", f"P{side}U{L}", f"{name} moins de {str(L).replace('.', ',')} tirs réussis", 1 - po)
    for (a, b), p in sorted(D.items(), key=lambda kv: -kv[1])[:6]:
        add("Score exact", f"PCS{a}-{b}", f"Score exact {a}-{b}", p)
    return out


def _sudden_death(pa: float, pb: float) -> float:
    # égalité après 5 tirs chacun, sans arrêt anticipé possible dans ce cas
    return float(sum(comb(5, k) ** 2 * pa ** k * (1 - pa) ** (5 - k) * pb ** k * (1 - pb) ** (5 - k) for k in range(6)))


def settle(key: str, s: Shootout) -> str | None:
    a, b = s.score
    n = len(s.kicks)
    if key in ("P1", "P2"):
        return "V" if (a > b) == (key == "P1") else "P"
    if key in ("SD_Y", "SD_N"):
        return "V" if (n > 10) == (key == "SD_Y") else "P"
    if key.startswith("PCS"):
        x, y = key[3:].split("-")
        return "V" if (a, b) == (int(x), int(y)) else "P"
    if key[:2] in ("PO", "PU"):
        return "V" if ((a + b > float(key[2:])) == (key[1] == "O")) else "P"
    if key[:3] in ("PHO", "PHU", "PAO", "PAU"):
        g = a if key[1] == "H" else b
        return "V" if ((g > float(key[3:])) == (key[2] == "O")) else "P"
    raise ValueError(key)
