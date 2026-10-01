"""Catalogue des compétitions virtuelles et paramètres de format.

`goals` est la moyenne de buts par match utilisée par le générateur de démonstration
et comme a priori quand l'historique est court ; le modèle réel la réestime sur les données.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Competition:
    code: str
    name: str
    kind: str              # "football" | "penalty" | "21"
    goals: float = 2.7     # buts / match attendus (football)
    teams: int = 16
    ou_lines: tuple = (0.5, 1.5, 2.5, 3.5, 4.5)
    max_goals: int = 10    # taille de la matrice de scores
    rounds: int = 1        # 21 : manches gagnantes nécessaires (« jusqu'à 3 victoires » → 3)


def _lines(lo: float, hi: float) -> tuple:
    out, x = [], lo
    while x <= hi + 1e-9:
        out.append(round(x, 1)); x += 1
    return tuple(out)


COMPETITIONS: dict[str, Competition] = {c.code: c for c in [
    # formats réduits : beaucoup plus de buts, matrice et lignes plus larges
    Competition("fc26-rush-superligue", "FC 26. 5x5 Rush. Superligue", "football", 7.6, 12, _lines(4.5, 11.5), 18),
    Competition("fc24-4x4-angleterre", "FC 24. 4x4. Championnat d'Angleterre", "football", 6.4, 12, _lines(3.5, 9.5), 16),
    Competition("fc25-3x3-conference", "FC 25. 3x3. Ligue de conférence", "football", 5.6, 12, _lines(2.5, 8.5), 15),
    Competition("fc26-england", "FC 26. England Championship", "football", 3.1, 20, _lines(0.5, 5.5), 12),
    Competition("fc26-champions-league", "FC 26. Champions League", "football", 3.2, 16, _lines(0.5, 5.5), 12),
    Competition("fc26-world-cup", "FC 26. Championnat du monde", "football", 2.9, 16, _lines(0.5, 5.5), 12),
    Competition("fc25-italy", "FC 25. Italy Championship", "football", 2.8, 20, _lines(0.5, 5.5), 12),
    Competition("fc25-europa", "FC 25. Ligue européenne", "football", 3.0, 16, _lines(0.5, 5.5), 12),
    Competition("fc26-germany", "FC 26. Germany Championship", "football", 3.3, 18, _lines(0.5, 5.5), 12),
    Competition("fc26-italy", "FC 26. Italy Championship", "football", 2.8, 20, _lines(0.5, 5.5), 12),
    Competition("fc26-spain", "FC 26. Spain Championship", "football", 2.9, 20, _lines(0.5, 5.5), 12),
    Competition("uefa-nations-sim", "UEFA Nations League. Simulation", "football", 2.6, 16, _lines(0.5, 5.5), 12),
    Competition("fc24-penalty", "FC24. Penalty", "penalty", teams=16),
    Competition("fc25-penalty", "FC25. Penalty", "penalty", teams=16),
    Competition("fc26-penalty", "FC26. Penalty", "penalty", teams=16),
    Competition("fifa23-penalty", "FIFA23. Penalty", "penalty", teams=16),
    Competition("penalty", "Penalty", "penalty", teams=16),
    Competition("21-classics", "21 classics", "21", rounds=1),
    Competition("21-dota-bo3", "21 Dota. Jusqu'à 3 victoires", "21", rounds=3),
    Competition("le-21", "Le 21", "21", rounds=1),
]}
