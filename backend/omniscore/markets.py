"""Dérivation de tous les marchés à partir des matrices de scores, et règlement."""
from __future__ import annotations

import numpy as np


def _outcome(h, a):
    return "1" if h > a else "2" if h < a else "X"


def markets(M: np.ndarray, HT: np.ndarray, home: str, away: str) -> list[dict]:
    n = M.shape[0]
    i, j = np.indices(M.shape)
    tot = i + j
    p1, pX, p2 = M[i > j].sum(), M[i == j].sum(), M[i < j].sum()
    out = []

    def add(group, key, label, p):
        out.append({"group": group, "key": key, "label": label, "p": float(np.clip(p, 0, 1))})

    add("Résultat", "1", f"Victoire {home}", p1)
    add("Résultat", "X", "Match nul", pX)
    add("Résultat", "2", f"Victoire {away}", p2)
    add("Résultat", "1X", f"{home} ou nul", p1 + pX)
    add("Résultat", "X2", f"Nul ou {away}", pX + p2)
    add("Résultat", "12", "Pas de match nul", p1 + p2)
    add("Résultat", "DNB1", f"{home} (remboursé si nul)", p1 / (p1 + p2))
    add("Résultat", "DNB2", f"{away} (remboursé si nul)", p2 / (p1 + p2))
    for L in (0.5, 1.5, 2.5, 3.5, 4.5):
        po = M[tot > L].sum()
        add("Buts", f"O{L}", f"Plus de {str(L).replace('.', ',')} buts", po)
        add("Buts", f"U{L}", f"Moins de {str(L).replace('.', ',')} buts", 1 - po)
    btts = M[1:, 1:].sum()
    add("Buts", "BTTS_Y", "Les deux équipes marquent : oui", btts)
    add("Buts", "BTTS_N", "Les deux équipes marquent : non", 1 - btts)
    ph, pa = M.sum(axis=1), M.sum(axis=0)
    for side, name, marg in (("H", home, ph), ("A", away, pa)):
        for L in (0.5, 1.5):
            po = marg[int(L) + 1:].sum()
            add("Équipes", f"{side}O{L}", f"{name} plus de {str(L).replace('.', ',')} but{'s' if L > 1 else ''}", po)
            add("Équipes", f"{side}U{L}", f"{name} moins de {str(L).replace('.', ',')} but{'s' if L > 1 else ''}", 1 - po)
    hi, hj = np.indices(HT.shape)
    add("1re mi-temps", "HT1", f"1re MT : victoire {home}", HT[hi > hj].sum())
    add("1re mi-temps", "HTX", "1re MT : nul", HT[hi == hj].sum())
    add("1re mi-temps", "HT2", f"1re MT : victoire {away}", HT[hi < hj].sum())
    for L in (0.5, 1.5):
        po = HT[hi + hj > L].sum()
        add("1re mi-temps", f"HTO{L}", f"1re MT : plus de {str(L).replace('.', ',')} but{'s' if L > 1 else ''}", po)
        add("1re mi-temps", f"HTU{L}", f"1re MT : moins de {str(L).replace('.', ',')} but{'s' if L > 1 else ''}", 1 - po)
    flat = [(M[a, b], a, b) for a in range(min(n, 7)) for b in range(min(n, 7))]
    for p, a, b in sorted(flat, reverse=True)[:6]:
        add("Score exact", f"CS{a}-{b}", f"Score exact {a}-{b}", p)
    return out


def settle(key: str, hg: int, ag: int, hthg: int | None = None, htag: int | None = None) -> str | None:
    """'V' validé, 'P' perdu, 'R' remboursé, None si non réglable (ex. MT inconnue)."""
    o, t = _outcome(hg, ag), hg + ag
    if key in ("1", "X", "2"):
        return "V" if o == key else "P"
    if key in ("1X", "X2", "12"):
        return "V" if o in key else "P"
    if key.startswith("DNB"):
        return "R" if o == "X" else "V" if o == key[-1] else "P"
    if key == "BTTS_Y":
        return "V" if hg > 0 and ag > 0 else "P"
    if key == "BTTS_N":
        return "P" if hg > 0 and ag > 0 else "V"
    if key.startswith("CS"):
        a, b = key[2:].split("-")
        return "V" if (hg, ag) == (int(a), int(b)) else "P"
    if key.startswith("HT"):
        if hthg is None:
            return None
        rest = key[2:]
        if rest in ("1", "X", "2"):
            return "V" if _outcome(hthg, htag) == rest else "P"
        L = float(rest[1:])
        return "V" if ((hthg + htag > L) == (rest[0] == "O")) else "P"
    if key[0] in "HA" and key[1] in "OU":
        g = hg if key[0] == "H" else ag
        return "V" if ((g > float(key[2:])) == (key[1] == "O")) else "P"
    if key[0] in "OU":
        return "V" if ((t > float(key[1:])) == (key[0] == "O")) else "P"
    raise ValueError(key)
