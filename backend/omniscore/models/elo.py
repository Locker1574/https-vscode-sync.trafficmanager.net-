"""Elo football (échelle ClubElo) + logit ordonné pour convertir l'écart en 1X2."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize


@dataclass
class Elo:
    k: float = 20.0
    home_adv: float = 65.0
    ratings: dict[str, float] = field(default_factory=dict)
    # logit ordonné : P(dom) = σ(β·diff − c2), P(ext) = σ(−β·diff − c1)... ajusté sur l'historique
    beta: float = 0.004
    c_away: float = 0.9
    c_home: float = 0.3

    def expected(self, h: str, a: str) -> float:
        rh, ra = self.ratings.get(h, 1450.0), self.ratings.get(a, 1450.0)
        return 1 / (1 + 10 ** (-(rh + self.home_adv - ra) / 400))

    def diff(self, h: str, a: str) -> float:
        return self.ratings.get(h, 1450.0) + self.home_adv - self.ratings.get(a, 1450.0)

    def update(self, m) -> None:
        e = self.expected(m.home, m.away)
        s = 1.0 if m.hg > m.ag else 0.5 if m.hg == m.ag else 0.0
        gd = abs(m.hg - m.ag)
        mult = 1 if gd <= 1 else 1.5 if gd == 2 else (11 + gd) / 8
        delta = self.k * mult * (s - e)
        self.ratings[m.home] = self.ratings.get(m.home, 1450.0) + delta
        self.ratings[m.away] = self.ratings.get(m.away, 1450.0) - delta

    def probs_from_diff(self, d: float) -> tuple[float, float, float]:
        sig = lambda x: 1 / (1 + math.exp(-x))
        p_away = sig(-self.beta * d - self.c_away)
        p_home_or_draw = 1 - p_away
        p_home = sig(self.beta * d - self.c_home)
        p_home = min(p_home, p_home_or_draw - 1e-4)
        return p_home, p_home_or_draw - p_home, p_away

    def probs(self, h: str, a: str) -> tuple[float, float, float]:
        return self.probs_from_diff(self.diff(h, a))

    def fit_link(self, diffs, outcomes) -> None:
        """Ajuste β, c_home, c_away par maximum de vraisemblance (outcome 0=dom, 1=nul, 2=ext)."""
        diffs, outcomes = np.asarray(diffs, float), np.asarray(outcomes)
        if len(diffs) < 100:
            return

        def nll(p):
            b, ch, ca = p
            ph = 1 / (1 + np.exp(-(b * diffs - ch)))
            pa = 1 / (1 + np.exp(-(-b * diffs - ca)))
            pd = np.clip(1 - ph - pa, 1e-6, 1)
            pr = np.where(outcomes == 0, ph, np.where(outcomes == 1, pd, pa))
            return -np.log(np.clip(pr, 1e-9, 1)).sum()

        r = minimize(nll, [self.beta, self.c_home, self.c_away], method="Nelder-Mead", options={"maxiter": 400})
        self.beta, self.c_home, self.c_away = map(float, r.x)
