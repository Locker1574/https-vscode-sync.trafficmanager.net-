"""Modèle de Dixon-Coles (1997) : Poisson bivarié corrigé, pondéré dans le temps.

log λ_dom = μ + H + a_dom + d_ext        log λ_ext = μ + a_ext + d_dom
a = force offensive, d = faiblesse défensive (centrées par pénalité L2),
poids w = exp(-ξ · jours écoulés), correction τ(x, y, λ, μ, ρ) sur 0-0, 1-0, 0-1, 1-1.
L'ajustement Poisson se fait par Newton-Raphson (IRLS), puis ρ par recherche 1D.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import poisson

MAX_GOALS = 10


def tau(x, y, lh, la, rho):
    t = np.ones_like(lh, dtype=float)
    t = np.where((x == 0) & (y == 0), 1 - lh * la * rho, t)
    t = np.where((x == 0) & (y == 1), 1 + lh * rho, t)
    t = np.where((x == 1) & (y == 0), 1 + la * rho, t)
    t = np.where((x == 1) & (y == 1), 1 - rho, t)
    return t


def score_matrix(lh: float, la: float, rho: float = 0.0, n: int = MAX_GOALS) -> np.ndarray:
    g = np.arange(n)
    M = np.outer(poisson.pmf(g, lh), poisson.pmf(g, la))
    M[0, 0] *= 1 - lh * la * rho
    M[0, 1] *= 1 + lh * rho
    M[1, 0] *= 1 + la * rho
    M[1, 1] *= 1 - rho
    M = np.clip(M, 0, None)
    return M / M.sum()


@dataclass
class DixonColes:
    xi: float = 0.0019          # décroissance temporelle par jour (demi-vie ≈ 1 an)
    l2: float = 2.0             # rétrécissement vers la moyenne (équipes promues, petits échantillons)
    teams: list[str] = field(default_factory=list)
    mu: float = 0.0
    home: float = 0.25
    attack: dict[str, float] = field(default_factory=dict)
    defence: dict[str, float] = field(default_factory=dict)
    rho: float = -0.05
    n_matches: dict[str, float] = field(default_factory=dict)
    ht_share: float = 0.44      # part des buts marqués en 1re mi-temps (estimée)
    promoted_prior: tuple = (-0.20, 0.20)  # a priori (attaque, défense) d'une équipe promue
    use_prior: bool = True

    def fit(self, matches, ref: date):
        ms = [m for m in matches if m.played and m.date < ref]
        if len(ms) < 30:
            raise ValueError("pas assez de matchs pour ajuster le modèle")
        self.teams = sorted({m.home for m in ms} | {m.away for m in ms})
        idx = {t: i for i, t in enumerate(self.teams)}
        n, N = len(self.teams), len(ms)
        w = np.array([np.exp(-self.xi * (ref - m.date).days) for m in ms])
        hi = np.array([idx[m.home] for m in ms])
        ai = np.array([idx[m.away] for m in ms])
        y = np.concatenate([[m.hg for m in ms], [m.ag for m in ms]]).astype(float)
        W = np.concatenate([w, w])
        # matrice de conception : [μ, H, a_0..a_n-1, d_0..d_n-1]
        P = 2 + 2 * n
        X = np.zeros((2 * N, P))
        r = np.arange(N)
        X[r, 0] = 1; X[r, 1] = 1; X[r, 2 + hi] = 1; X[r, 2 + n + ai] = 1
        X[N + r, 0] = 1; X[N + r, 2 + ai] = 1; X[N + r, 2 + n + hi] = 1
        pen = np.zeros(P); pen[2:] = self.l2
        centre = np.zeros(P)
        latest = max(m.season for m in ms)
        if self.use_prior and any(m.season < latest for m in ms):
            seen_before = {m.home for m in ms if m.season < latest} | {m.away for m in ms if m.season < latest}
            for t, i in idx.items():
                if t not in seen_before:  # promue cette saison : rétrécie vers le profil type d'un promu
                    centre[2 + i], centre[2 + n + i] = self.promoted_prior
        theta = centre.copy(); theta[0] = np.log(max(y.mean(), 0.1))
        for _ in range(50):
            lam = np.exp(X @ theta)
            g = X.T @ (W * (y - lam)) - pen * (theta - centre)
            Hm = (X * (W * lam)[:, None]).T @ X + np.diag(pen) + 1e-9 * np.eye(P)
            step = np.linalg.solve(Hm, g)
            theta += step
            if np.abs(step).max() < 1e-7:
                break
        self.mu, self.home = float(theta[0]), float(theta[1])
        self.attack = {t: float(theta[2 + i]) for t, i in idx.items()}
        self.defence = {t: float(theta[2 + n + i]) for t, i in idx.items()}
        lam = np.exp(X @ theta)
        lh, la = lam[:N], lam[N:]
        xs, ys = y[:N], y[N:]

        def nll(rho):
            t = tau(xs, ys, lh, la, rho)
            if (t <= 0).any():
                return 1e12
            return -float((w * np.log(t)).sum())

        self.rho = float(minimize_scalar(nll, bounds=(-0.25, 0.25), method="bounded").x)
        self.n_matches = {t: 0.0 for t in self.teams}
        for m, wi in zip(ms, w):
            self.n_matches[m.home] += wi; self.n_matches[m.away] += wi
        ht = [(m.hthg + m.htag, m.hg + m.ag) for m in ms if m.hthg is not None]
        if len(ht) > 50 and sum(b for _, b in ht):
            self.ht_share = sum(a for a, _ in ht) / sum(b for _, b in ht)
        return self

    def rates(self, home: str, away: str) -> tuple[float, float]:
        a, d = self.attack, self.defence
        # une équipe inconnue (promue sans historique) reçoit un léger malus
        pa, pd = self.promoted_prior
        ah, aa = a.get(home, pa), a.get(away, pa)
        dh, da = d.get(home, pd), d.get(away, pd)
        return float(np.exp(self.mu + self.home + ah + da)), float(np.exp(self.mu + aa + dh))

    def matrix(self, home: str, away: str) -> np.ndarray:
        lh, la = self.rates(home, away)
        return score_matrix(lh, la, self.rho)

    def ht_matrix(self, home: str, away: str) -> np.ndarray:
        lh, la = self.rates(home, away)
        return score_matrix(lh * self.ht_share, la * self.ht_share, 0.0)
