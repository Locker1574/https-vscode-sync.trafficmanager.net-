"""Événements du Jeu 21 : une main (ou une manche) jouée ou à venir."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Hand:
    comp: str
    id: str
    at: datetime
    player: list = field(default=None, hash=False)   # cartes du joueur (None si à venir)
    dealer: list = field(default=None, hash=False)

    @property
    def played(self) -> bool:
        return self.player is not None

    @property
    def home(self) -> str:
        return "Joueur"

    @property
    def away(self) -> str:
        return "Croupier"
