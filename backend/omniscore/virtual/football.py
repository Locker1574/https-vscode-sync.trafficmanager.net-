"""Football virtuel : Dixon-Coles ajusté par compétition + tous les marchés de paris.

Réutilise le modèle Dixon-Coles du moteur réel (`omniscore.models.dixon_coles`).
Différences propres au virtuel :
- formats réduits (5x5, 4x4, 3x3) : matrice de scores et lignes plus/moins élargies ;
- mi-temps / fin de match : 1re et 2e mi-temps traitées comme deux Poisson indépendants
  (taux × part des buts de 1re MT, estimée par compétition) ;
- 1re équipe à marquer : processus de Poisson, P(dom en premier) = λd / (λd + λe) · (1 − e^−(λd+λe)).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np

from ..data.openfootball import Match
from ..markets import settle as settle_base
from ..models.dixon_coles import DixonColes, score_matrix
from .competitions import Competition


@dataclass(frozen=True)
class VMatch:
    """Un match virtuel joué ou à venir. `first` = 'H', 'A' ou None (aucun but)."""
    comp: str
    id: str
    at: datetime
    home: str
    away: str
    hg: int | None = None
    ag: int | None = None
    hthg: int | None = None
    htag: int | None = None
    first: str | None = None

    @property
    def played(self) -> bool:
        return self.hg is not None

    def as_match(self) -> Match:
        return Match(self.comp, "v", self.at.date(), self.at.strftime("%H:%M"), None, self.home, self.away,
                     self.hg, self.ag, self.hthg, self.htag)


def fit(comp: Competition, history: list[VMatch], ref: datetime) -> DixonColes:
    """Ajuste Dixon-Coles sur l'historique de la compétition (une seule « saison » : pas d'a priori promu)."""
    ms = [m.as_match() for m in history if m.played and m.at < ref]
    # le virtuel joue des centaines de matchs par jour : décroissance plus rapide (demi-vie ≈ 2 semaines)
    dc = DixonColes(xi=0.05, l2=4.0, use_prior=False)
    # le modèle travaille en jours : on décale la référence d'un jour pour inclure les matchs du jour même
    return dc.fit(ms, ref.date().fromordinal(ref.date().toordinal() + 1))


def _fmt(x: float) -> str:
    return str(x).replace(".", ",")


def markets(dc: DixonColes, comp: Competition, home: str, away: str) -> list[dict]:
    lh, la = dc.rates(home, away)
    n = comp.max_goals
    M = score_matrix(lh, la, dc.rho, n)
    s = dc.ht_share
    H1 = score_matrix(lh * s, la * s, 0.0, n)
    H2 = score_matrix(lh * (1 - s), la * (1 - s), 0.0, n)
    i, j = np.indices(M.shape)
    tot, diff = i + j, i - j
    out: list[dict] = []

    def add(group, key, label, p):
        out.append({"group": group, "key": key, "label": label, "p": float(np.clip(p, 0, 1))})

    p1, pX, p2 = M[diff > 0].sum(), M[diff == 0].sum(), M[diff < 0].sum()
    add("Résultat", "1", f"Victoire {home}", p1)
    add("Résultat", "X", "Match nul", pX)
    add("Résultat", "2", f"Victoire {away}", p2)
    add("Résultat", "1X", f"{home} ou nul", p1 + pX)
    add("Résultat", "X2", f"Nul ou {away}", pX + p2)
    add("Résultat", "12", "Pas de match nul", p1 + p2)
    add("Résultat", "DNB1", f"{home} (remboursé si nul)", p1 / (p1 + p2))
    add("Résultat", "DNB2", f"{away} (remboursé si nul)", p2 / (p1 + p2))

    for L in comp.ou_lines:
        po = M[tot > L].sum()
        add("Buts", f"O{L}", f"Plus de {_fmt(L)} buts", po)
        add("Buts", f"U{L}", f"Moins de {_fmt(L)} buts", 1 - po)
    btts = M[1:, 1:].sum()
    add("Buts", "BTTS_Y", "Les deux équipes marquent : oui", btts)
    add("Buts", "BTTS_N", "Les deux équipes marquent : non", 1 - btts)
    odd = M[tot % 2 == 1].sum()
    add("Buts", "ODD", "Total de buts impair", odd)
    add("Buts", "EVEN", "Total de buts pair", 1 - odd)

    ph, pa = M.sum(axis=1), M.sum(axis=0)
    for side, name, marg, lam in (("H", home, ph, lh), ("A", away, pa, la)):
        base = max(0.5, np.floor(lam) - 0.5)
        for L in (base, base + 1, base + 2):
            po = marg[int(L) + 1:].sum()
            add("Équipes", f"{side}O{L}", f"{name} plus de {_fmt(L)} buts", po)
            add("Équipes", f"{side}U{L}", f"{name} moins de {_fmt(L)} buts", 1 - po)
    add("Équipes", "CLEAN_H", f"{home} ne prend pas de but", pa[0])
    add("Équipes", "CLEAN_A", f"{away} ne prend pas de but", ph[0])
    lt = lh + la
    p_none = np.exp(-lt)
    add("Équipes", "FTS_H", f"{home} marque en premier", lh / lt * (1 - p_none))
    add("Équipes", "FTS_A", f"{away} marque en premier", la / lt * (1 - p_none))
    add("Équipes", "FTS_N", "Aucun but", p_none)

    # handicaps asiatiques en demi-lignes (pas de remboursement), autour de l'écart attendu
    centre = np.round(lh - la)
    for k in range(int(centre) - 2, int(centre) + 2):
        L = k + 0.5  # dom −L : il gagne le pari si écart > L
        ph_ = M[diff > L].sum()
        add("Handicap", f"AHH{-L:+}", f"{home} handicap {-L:+}".replace(".", ","), ph_)
        add("Handicap", f"AHA{L:+}", f"{away} handicap {L:+}".replace(".", ","), 1 - ph_)
    for side, name, sgn in (("H", home, 1), ("A", away, -1)):
        d = sgn * diff
        add("Écart", f"MG{side}1", f"{name} gagne par 1 but exactement", M[d == 1].sum())
        add("Écart", f"MG{side}2", f"{name} gagne par 2 buts exactement", M[d == 2].sum())
        add("Écart", f"MG{side}3P", f"{name} gagne par 3 buts ou plus", M[d >= 3].sum())

    hi, hj = np.indices(H1.shape)
    h1 = {"1": H1[hi > hj].sum(), "X": H1[hi == hj].sum(), "2": H1[hi < hj].sum()}
    add("1re mi-temps", "HT1", f"1re MT : victoire {home}", h1["1"])
    add("1re mi-temps", "HTX", "1re MT : nul", h1["X"])
    add("1re mi-temps", "HT2", f"1re MT : victoire {away}", h1["2"])
    for L in comp.ou_lines[:3]:
        po = H1[hi + hj > L].sum()
        add("1re mi-temps", f"HTO{L}", f"1re MT : plus de {_fmt(L)} buts", po)
        add("1re mi-temps", f"HTU{L}", f"1re MT : moins de {_fmt(L)} buts", 1 - po)
    # mi-temps / fin de match : écart final = écart 1re MT + écart 2e MT (convolution par résultat à la pause)
    names = {"1": home, "X": "nul", "2": away}
    off = n - 1
    D2 = np.bincount((hi - hj + off).ravel(), weights=H2.ravel(), minlength=2 * n - 1)
    f = np.arange(4 * n - 3) - 2 * off  # écarts finaux possibles
    htft = {}
    for r, mask in (("1", hi > hj), ("X", hi == hj), ("2", hi < hj)):
        D1 = np.bincount((hi - hj + off)[mask], weights=H1[mask], minlength=2 * n - 1)
        F = np.convolve(D1, D2)
        htft.update({(r, "1"): F[f > 0].sum(), (r, "X"): F[f == 0].sum(), (r, "2"): F[f < 0].sum()})
    for (a, b), p in htft.items():
        add("MT / Fin", f"HF{a}{b}", f"MT {names[a]} / Fin {names[b]}", p)

    flat = sorted(((M[a, b], a, b) for a in range(n) for b in range(n)), reverse=True)[:8]
    for p, a, b in flat:
        add("Score exact", f"CS{a}-{b}", f"Score exact {a}-{b}", p)
    return out


def settle(key: str, m: VMatch) -> str | None:
    """'V' validé, 'P' perdu, 'R' remboursé, None si l'information manque."""
    hg, ag, d, t = m.hg, m.ag, m.hg - m.ag, m.hg + m.ag
    if key == "ODD":
        return "V" if t % 2 else "P"
    if key == "EVEN":
        return "P" if t % 2 else "V"
    if key == "CLEAN_H":
        return "V" if ag == 0 else "P"
    if key == "CLEAN_A":
        return "V" if hg == 0 else "P"
    if key.startswith("FTS_"):
        if t == 0:
            return "V" if key == "FTS_N" else "P"
        if key == "FTS_N":
            return "P"
        if m.first is None:
            return None
        return "V" if m.first == key[-1] else "P"
    if key.startswith("AH"):
        L = float(key[3:])  # handicap appliqué à l'équipe désignée
        return "V" if ((d if key[2] == "H" else -d) + L) > 0 else "P"
    if key.startswith("MG"):
        x = d if key[2] == "H" else -d
        want = key[3:]
        return "V" if (x >= 3 if want == "3P" else x == int(want)) else "P"
    if key.startswith("HF"):
        if m.hthg is None:
            return None
        o = lambda a, b: "1" if a > b else "X" if a == b else "2"
        return "V" if o(m.hthg, m.htag) == key[2] and o(hg, ag) == key[3] else "P"
    return settle_base(key, hg, ag, m.hthg, m.htag)
