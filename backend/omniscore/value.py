"""Retrait de la marge bookmaker, value, Kelly."""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq


def devig_multiplicative(odds: list[float]) -> list[float]:
    inv = np.array([1 / o for o in odds])
    return list(inv / inv.sum())


def devig_shin(odds: list[float]) -> list[float]:
    """Méthode de Shin (1993) : tient compte des parieurs initiés, corrige le biais favori/outsider."""
    pi = np.array([1 / o for o in odds])
    B = pi.sum()
    if B <= 1:
        return list(pi / B)

    def f(z):
        p = (np.sqrt(z ** 2 + 4 * (1 - z) * pi ** 2 / B) - z) / (2 * (1 - z))
        return p.sum() - 1

    z = brentq(f, 0, 0.4)
    p = (np.sqrt(z ** 2 + 4 * (1 - z) * pi ** 2 / B) - z) / (2 * (1 - z))
    return list(p / p.sum())


def value(p: float, odds: float) -> float:
    return p * odds - 1


def kelly(p: float, odds: float, fraction: float = 0.25, cap: float = 0.05) -> float:
    if odds <= 1:
        return 0.0
    f = (p * odds - 1) / (odds - 1)
    return float(np.clip(f * fraction, 0, cap))
