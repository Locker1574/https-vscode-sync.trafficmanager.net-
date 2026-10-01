"""Routes REST du module virtuel, montées par omniscore.api sous /v1/virtual."""
from __future__ import annotations

import json
import os
from datetime import timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import blackjack as bj
from . import demo as dm
from .competitions import COMPETITIONS
from .football import VMatch
from .ingest import load_csv
from .journal import Journal
from .patterns import analyse
from .penalty import Shootout
from .predictor import DATA, VirtualModel
from .twentyone import Hand

router = APIRouter(prefix="/v1/virtual", tags=["virtuel"])
_hist: dict[str, list] = {}


def history(code: str) -> list:
    if code not in COMPETITIONS:
        raise HTTPException(404, "Compétition inconnue")
    if code not in _hist:
        csv = os.environ.get("OMNISCORE_VIRTUAL_CSV")
        if csv:
            _hist.update({k: [e for e in v if e.played] for k, v in load_csv(Path(csv)).items()})
        _hist.setdefault(code, dm.history(code))  # repli : données de démonstration
    return _hist[code]


class PredictIn(BaseModel):
    home: str | None = None
    away: str | None = None
    odds: dict[str, float] = Field(default_factory=dict, description="cotes du bookmaker par clé de marché")


class DecisionIn(BaseModel):
    player: list[int] = Field(..., description="cartes du joueur (As = 11, figures = 10)")
    dealer_up: int
    decks: int = 1
    seen: list[int] = Field(default_factory=list, description="autres cartes déjà sorties du sabot")


@router.get("/competitions")
def competitions():
    return [{"code": c.code, "name": c.name, "kind": c.kind} for c in COMPETITIONS.values()]


@router.post("/{code}/predict")
def predict(code: str, body: PredictIn):
    h = history(code)
    comp = COMPETITIONS[code]
    now = h[-1].at
    if comp.kind == "21":
        ev = Hand(code, "next", now)
    else:
        if not body.home or not body.away:
            raise HTTPException(422, "home et away sont requis")
        ev = (VMatch if comp.kind == "football" else Shootout)(code, "next", now, body.home, body.away)
    return VirtualModel(code, h, now + timedelta(seconds=1)).predict(ev, body.odds)


@router.get("/{code}/patterns")
def patterns(code: str):
    return analyse(COMPETITIONS[code].kind, history(code))


@router.post("/21/decision")
def decision(body: DecisionIn):
    probs = bj.shoe(body.decks, body.player + [body.dealer_up] + body.seen)
    return bj.decision(body.player, body.dealer_up, probs)


@router.get("/backtest")
def backtest():
    p = DATA / "backtest.json"
    if not p.exists():
        raise HTTPException(404, "Lancez d'abord : python -m omniscore.virtual demo")
    return json.loads(p.read_text())


@router.get("/journal")
def journal(demo: bool = False):
    j = Journal(DATA / ("journal_demo.json" if demo else "journal.json"))
    return {"stats": j.stats(), "items": j.items[-200:]}
