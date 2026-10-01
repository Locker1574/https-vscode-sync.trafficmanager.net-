"""Générateur de données de DÉMONSTRATION (simulées), pour tester l'app sans fournisseur réel.

Chaque compétition a des forces d'équipes cachées ; les résultats sont tirés au hasard selon
ces forces, comme le ferait un jeu virtuel. Les cotes « bookmaker » sont les vraies
probabilités + 7 % de marge, avec un léger bruit : c'est le cas réaliste où il n'y a
presque jamais de value. Remplacez ces données par l'import CSV (`ingest.py`) en production.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

from . import blackjack as bj
from .competitions import COMPETITIONS, Competition
from .football import VMatch
from .penalty import Shootout
from .twentyone import Hand

T0 = datetime(2026, 9, 1)
NATIONS = ["France", "Espagne", "Angleterre", "Allemagne", "Italie", "Portugal", "Pays-Bas", "Belgique", "Croatie",
           "Brésil", "Argentine", "Uruguay", "Maroc", "Sénégal", "Japon", "Mexique", "États-Unis", "Suisse", "Danemark", "Pologne"]
CLUBS = ["Lions", "Aigles", "Titans", "Faucons", "Loups", "Requins", "Tigres", "Dragons", "Ours", "Panthères",
         "Cobras", "Vikings", "Spartiates", "Corsaires", "Gladiateurs", "Phénix", "Mustangs", "Condors", "Pumas", "Lynx"]


def teams(comp: Competition) -> list[str]:
    base = NATIONS if "world" in comp.code or "nations" in comp.code or comp.kind == "penalty" else CLUBS
    return base[: comp.teams]


def _seed(code: str) -> int:
    return sum(ord(c) * (i + 1) for i, c in enumerate(code))


def football(comp: Competition, n: int, interval_min: int = 4, start: datetime = T0, seed: int | None = None) -> list[VMatch]:
    rng = np.random.default_rng(_seed(comp.code) if seed is None else seed)
    ts = teams(comp)
    k = len(ts)
    att = dict(zip(ts, rng.normal(0, 0.28, k)))
    dfn = dict(zip(ts, rng.normal(0, 0.22, k)))
    mu = np.log(comp.goals / 2) - 0.12
    out = []
    for i in range(n):
        at = start + timedelta(minutes=interval_min * (i // (k // 2)))
        if i % (k // 2) == 0:
            order = rng.permutation(ts)
        h, a = order[2 * (i % (k // 2))], order[2 * (i % (k // 2)) + 1]
        lh, la = np.exp(mu + 0.12 + att[h] + dfn[a]), np.exp(mu + att[a] + dfn[h])
        h1, a1 = rng.poisson(lh * 0.45), rng.poisson(la * 0.45)
        h2, a2 = rng.poisson(lh * 0.55), rng.poisson(la * 0.55)
        hg, ag = int(h1 + h2), int(a1 + a2)
        first = None if hg + ag == 0 else ("H" if rng.random() < hg / (hg + ag) else "A")
        out.append(VMatch(comp.code, f"{comp.code}-{i}", at, str(h), str(a), hg, ag, int(h1), int(a1), first))
    return out


def penalties(comp: Competition, n: int, interval_min: int = 2, start: datetime = T0, seed: int | None = None) -> list[Shootout]:
    rng = np.random.default_rng(_seed(comp.code) if seed is None else seed)
    ts = teams(comp)
    conv = dict(zip(ts, np.clip(rng.beta(16, 5, len(ts)), 0.5, 0.95)))
    out = []
    for i in range(n):
        h, a = rng.choice(ts, 2, replace=False)
        kicks, gh, ga = "", 0, 0
        for k in range(10):
            hit = rng.random() < conv[h if k % 2 == 0 else a]
            kicks += "1" if hit else "0"
            gh += hit and k % 2 == 0; ga += hit and k % 2 == 1
            done = k + 1
            if gh > ga + 5 - done // 2 or ga > gh + 5 - (done + 1) // 2:
                break
        while len(kicks) >= 10 and gh == ga:
            x, y = rng.random() < conv[h], rng.random() < conv[a]
            kicks += f"{int(x)}{int(y)}"; gh += x; ga += y
        out.append(Shootout(comp.code, f"{comp.code}-{i}", start + timedelta(minutes=interval_min * i), str(h), str(a), kicks))
    return out


def hands(comp: Competition, n: int, decks: int = 1, start: datetime = T0, seed: int | None = None) -> list[Hand]:
    rng = np.random.default_rng(_seed(comp.code) if seed is None else seed)
    out = []
    for i in range(n):
        p, d = bj.deal(rng, decks)
        out.append(Hand(comp.code, f"{comp.code}-{i}", start + timedelta(minutes=i), p, d))
    return out


def bookmaker_odds(p: float, rng: np.random.Generator, margin: float = 0.07) -> float:
    """Cote affichée : vraie probabilité × (1 + marge), bruit de ±3 %, arrondie au centième."""
    q = np.clip(p * (1 + margin) * np.exp(rng.normal(0, 0.03)), 0.01, 0.99)
    return round(max(1.01, 1 / q), 2)


def history(code: str, n: int | None = None):
    comp = COMPETITIONS[code]
    if comp.kind == "football":
        return football(comp, n or 3000)
    if comp.kind == "penalty":
        return penalties(comp, n or 3000)
    return hands(comp, n or 3000)
