"""Jeu 21 : probabilités exactes à partir de la composition du sabot.

Hypothèse de calcul (standard en analyse du 21) : pendant une main, chaque carte suit la
composition actuelle du sabot (tirage « infini » à composition donnée). L'erreur est faible
dès 1 jeu complet ; `simulate` vérifie par Monte-Carlo avec retrait réel des cartes.

Règles par défaut (jeu virtuel automatique) : le joueur et le croupier tirent tant que leur
total est < à leur seuil (17 par défaut), l'As vaut 11 sauf s'il fait dépasser 21.
Égalité = nul (remboursé). Le paramètre `player_stand` permet d'adapter à la variante jouée.
"""
from __future__ import annotations

from functools import lru_cache
from math import comb

import numpy as np

RANKS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11)  # 10 = 10/V/D/R, 11 = As


def shoe(decks: int = 1, seen: list[int] | None = None) -> tuple[float, ...]:
    """Probabilité de chaque valeur dans le sabot, après retrait des cartes déjà vues."""
    c = {r: 4 * decks for r in RANKS}
    c[10] = 16 * decks
    for card in seen or []:
        if c.get(card, 0) > 0:
            c[card] -= 1
    n = sum(c.values())
    return tuple(c[r] / n for r in RANKS)


def add_card(total: int, soft: int, card: int) -> tuple[int, int]:
    """Ajoute une carte ; `soft` = nombre d'As comptés 11."""
    total += card
    soft += card == 11
    while total > 21 and soft:
        total -= 10; soft -= 1
    return total, soft


def hand(cards: list[int]) -> tuple[int, int]:
    t, s = 0, 0
    for c in cards:
        t, s = add_card(t, s, c)
    return t, s


@lru_cache(maxsize=None)
def _final(total: int, soft: int, stand: int, probs: tuple) -> tuple:
    """Loi du total final (17..21, 22 = bust) d'une main qui tire jusqu'à `stand`."""
    out = np.zeros(23)
    if total > 21:
        out[22] = 1
        return tuple(out)
    if total >= stand:
        out[total] = 1
        return tuple(out)
    for card, p in zip(RANKS, probs):
        if p:
            out += p * np.array(_final(*add_card(total, soft, card), stand, probs))
    return tuple(out)


def final_dist(cards: list[int], stand: int, probs: tuple) -> np.ndarray:
    """Loi du total final à partir des cartes déjà reçues (liste vide = avant la donne)."""
    if not cards:
        out = np.zeros(23)
        for c1, p1 in zip(RANKS, probs):
            out += p1 * np.array(_final(*hand([c1]), stand, probs))
        return out
    return np.array(_final(*hand(cards), stand, probs))


def compare(P: np.ndarray, D: np.ndarray) -> tuple[float, float, float]:
    """(joueur gagne, nul, croupier gagne). Le joueur qui dépasse 21 perd, même si le croupier dépasse aussi."""
    win = draw = 0.0
    for t in range(4, 22):
        if P[t]:
            win += P[t] * (D[22] + D[:t].sum())
            draw += P[t] * D[t]
    return win, draw, 1 - win - draw


def markets(probs: tuple, stand_player: int = 17, stand_dealer: int = 17, player_cards=None, dealer_cards=None,
            rounds: int = 1) -> list[dict]:
    P = final_dist(player_cards or [], stand_player, probs)
    D = final_dist(dealer_cards or [], stand_dealer, probs)
    w, d, l = compare(P, D)
    out = []

    def add(group, key, label, p):
        out.append({"group": group, "key": key, "label": label, "p": float(np.clip(p, 0, 1))})

    add("Manche", "W_P", "Le joueur gagne la manche", w)
    add("Manche", "W_D", "Le croupier gagne la manche", l)
    add("Manche", "W_X", "Égalité", d)
    add("Manche", "W_P_DNB", "Joueur (remboursé si égalité)", w / (w + l))
    add("Manche", "W_D_DNB", "Croupier (remboursé si égalité)", l / (w + l))
    for who, name, X in (("P", "Joueur", P), ("D", "Croupier", D)):
        add("Totaux", f"{who}_BUST", f"{name} dépasse 21", X[22])
        add("Totaux", f"{who}_NOBUST", f"{name} ne dépasse pas 21", 1 - X[22])
        add("Totaux", f"{who}_21", f"{name} fait exactement 21", X[21])
        for L in (17.5, 18.5, 19.5):
            po = X[int(L) + 1:22].sum()
            add("Totaux", f"{who}O{L}", f"{name} : total plus de {str(L).replace('.', ',')} (sans dépasser)", po)
    if rounds > 1:
        for k, p in series(w, l, rounds).items():
            a, b = k
            add("Match", f"SER{a}-{b}", f"Score du match {a}-{b}", p)
        pw = sum(p for (a, b), p in series(w, l, rounds).items() if a > b)
        add("Match", "SER_P", f"Le joueur gagne le match (premier à {rounds})", pw)
        add("Match", "SER_D", f"Le croupier gagne le match (premier à {rounds})", 1 - pw)
    return out


def series(w: float, l: float, n: int) -> dict[tuple[int, int], float]:
    """Course à n victoires, égalités rejouées : chaîne de Markov ⇒ loi binomiale négative."""
    q = w / (w + l)
    out = {}
    for k in range(n):
        out[(n, k)] = comb(n - 1 + k, k) * q ** n * (1 - q) ** k
        out[(k, n)] = comb(n - 1 + k, k) * (1 - q) ** n * q ** k
    return out


def decision(player_cards: list[int], dealer_up: int, probs: tuple, stand_dealer: int = 17) -> dict:
    """Pour une main en cours : EV de rester, de tirer (puis jouer au mieux) et de doubler."""
    D = final_dist([dealer_up], stand_dealer, probs)

    def ev_stand(t):
        if t > 21:
            return -1.0
        w, d, l = compare(np.eye(23)[t], D)
        return w - l

    @lru_cache(maxsize=None)
    def best(t, s):
        if t > 21:
            return -1.0
        return max(ev_stand(t), ev_hit(t, s))

    @lru_cache(maxsize=None)
    def ev_hit(t, s):
        return sum(p * best(*add_card(t, s, c)) for c, p in zip(RANKS, probs) if p)

    t, s = hand(player_cards)
    ev_double = 2 * sum(p * ev_stand(add_card(t, s, c)[0]) for c, p in zip(RANKS, probs) if p)
    evs = {"rester": float(ev_stand(t)), "tirer": float(ev_hit(t, s)), "doubler": float(ev_double)}
    bust_next = sum(p for c, p in zip(RANKS, probs) if add_card(t, s, c)[0] > 21)
    return {"total": t, "souple": bool(s), "ev": {k: round(v, 4) for k, v in evs.items()},
            "conseil": max(evs, key=evs.get), "p_depasse_si_tire": round(float(bust_next), 4),
            "croupier_final": {str(k): round(float(D[k]), 4) for k in (17, 18, 19, 20, 21)} | {"dépasse": round(float(D[22]), 4)}}


def deal(rng: np.random.Generator, decks: int = 1, stand_player: int = 17, stand_dealer: int = 17) -> tuple[list, list]:
    """Une main réelle, cartes retirées du sabot (sabot remélangé à chaque main)."""
    cards = np.array(([2, 3, 4, 5, 6, 7, 8, 9, 11] * 4 + [10] * 16) * decks)
    rng.shuffle(cards)
    it = iter(cards.tolist())
    p, d = [next(it), next(it)], [next(it), next(it)]
    while hand(p)[0] < stand_player:
        p.append(next(it))
    if hand(p)[0] <= 21:
        while hand(d)[0] < stand_dealer:
            d.append(next(it))
    return p, d


def simulate(n: int, decks: int = 1, seed: int = 0, **kw) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    w = dr = 0
    for _ in range(n):
        p, d = deal(rng, decks, **kw)
        r = outcome(p, d)
        w += r == "P"; dr += r == "X"
    return w / n, dr / n, 1 - (w + dr) / n


def outcome(p: list[int], d: list[int]) -> str:
    tp, td = hand(p)[0], hand(d)[0]
    if tp > 21:
        return "D"
    if td > 21 or tp > td:
        return "P"
    return "X" if tp == td else "D"


def settle_hand(key: str, p: list[int], d: list[int]) -> str | None:
    r, tp, td = outcome(p, d), hand(p)[0], hand(d)[0]
    if key in ("W_P", "W_D", "W_X"):
        return "V" if r == key[-1] else "P"
    if key.endswith("_DNB"):
        return "R" if r == "X" else "V" if r == key[2] else "P"
    who_t = {"P": tp, "D": td}
    who = key[0]
    if key.endswith("_NOBUST"):
        return "V" if who_t[who] <= 21 else "P"
    if key.endswith("_BUST"):
        return "V" if who_t[who] > 21 else "P"
    if key.endswith("_21"):
        return "V" if who_t[who] == 21 else "P"
    if key[1] == "O":
        t = who_t[who]
        return "V" if float(key[2:]) < t <= 21 else "P"
    raise ValueError(key)
