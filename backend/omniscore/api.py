"""API REST OMNISCORE (FastAPI). Lancer : uvicorn omniscore.api:app --reload"""
from __future__ import annotations

import json
import time
from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import coupon as cp
from .backtest import OUT as BACKTEST_PATH
from .data.openfootball import LEAGUES, load
from .engine import upcoming_predictions
from .providers.odds_api import attach_odds

app = FastAPI(title="OMNISCORE API", version="0.1.0",
              description="Prédictions football calibrées (Dixon-Coles + Elo). Aucune prédiction n'est garantie.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])

_cache: dict = {"t": 0.0, "preds": []}


def preds(days: int = 30) -> list[dict]:
    if time.time() - _cache["t"] > 900 or _cache.get("days") != days:
        p = upcoming_predictions(load(first=2021), date.today(), days)
        attach_odds(p)
        _cache.update(t=time.time(), preds=p, days=days)
    return _cache["preds"]


@app.get("/v1/leagues")
def leagues():
    return LEAGUES


@app.get("/v1/matches")
def matches(league: str | None = None, days: int = Query(30, ge=1, le=45)):
    return [{k: v for k, v in p.items() if k != "markets"} | {"top": top(p)} for p in preds(days) if not league or p["league"] == league]


def top(p, pmin=0.70, pmax=0.98):
    ok = [m for m in p["markets"] if pmin <= m["p"] <= pmax and not m["key"].startswith("CS")]
    return max(ok, key=lambda m: m["confidence"]) if ok else None


@app.get("/v1/matches/{match_id:path}")
def match(match_id: str):
    for p in preds():
        if p["id"] == match_id:
            return p
    raise HTTPException(404, "Match introuvable")


@app.get("/v1/value-bets")
def value_bets(min_value: float = 0.03, min_p: float = 0.40):
    out = [{"match": f'{p["home"]} – {p["away"]}', "id": p["id"], "date": p["date"], **m}
           for p in preds() for m in p["markets"] if m.get("value", -1) >= min_value and m["p"] >= min_p]
    return sorted(out, key=lambda x: -x["value"] * x["confidence"])


@app.post("/v1/coupons/generate")
def generate(size: int = Query(3, ge=1, le=20), pmin: float = Query(0.70, ge=0.5, le=0.98),
             mode: str = Query("surete", pattern="^(surete|equilibre|rendement)$"), days: int = Query(2, ge=1, le=45)):
    today = [p for p in preds() if (date.fromisoformat(p["date"]) - date.today()).days < days]
    return cp.generate(today, size, pmin=pmin, mode=mode)


@app.post("/v1/coupons/regenerate")
def regenerate(current: list[dict], size: int = Query(3, ge=1, le=20), pmin: float = 0.70, mode: str = "surete"):
    return cp.regenerate(preds(), current, size, pmin=pmin, mode=mode)


@app.get("/v1/backtest")
def backtest():
    if not BACKTEST_PATH.exists():
        raise HTTPException(404, "Lancez d'abord : python -m omniscore.backtest")
    return json.loads(BACKTEST_PATH.read_text())
