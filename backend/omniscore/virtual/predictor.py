"""Prédicteur unifié : ajuste le bon modèle selon la compétition, classe les options, règle les paris.

Classement : toutes les options sont triées par probabilité calibrée décroissante.
Le « pick principal » est l'option la plus probable dont la probabilité reste ≤ P_MAX :
au-delà (ex. « plus de 0,5 but » en 5x5 à 99,9 %), la cote vaudrait ≈ 1,00 et le pari n'a pas d'intérêt.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np

from ..calibration import Calibrator
from ..value import kelly, value
from . import blackjack as bj
from . import football as fb
from . import penalty as pen
from .competitions import COMPETITIONS

P_MAX = 0.95
DATA = Path(__file__).resolve().parents[2] / "data" / "virtual"
TIERS = ((0.80, "🟢", "Très forte"), (0.65, "🟡", "Forte"), (0.50, "🟠", "Moyenne"), (0.0, "🔴", "Faible"))


def tier(p: float) -> dict:
    for lo, icon, name in TIERS:
        if p >= lo:
            return {"icon": icon, "name": name}
    raise AssertionError


def vfamily(key: str) -> str:
    """Famille de marché pour la calibration (chaque famille a sa propre courbe)."""
    for prefix, fam in (("HF", "HTFT"), ("HT", "HT"), ("CS", "CS"), ("PCS", "CS"), ("AH", "AH"), ("MG", "MARGIN"),
                        ("FTS", "FIRST"), ("CLEAN", "CLEAN"), ("BTTS", "BTTS"), ("DNB", "DNB"), ("SD_", "SD"),
                        ("SER", "SERIES"), ("W_", "ROUND")):
        if key.startswith(prefix):
            return fam
    if key in ("1", "X", "2"):
        return "1X2"
    if key in ("1X", "X2", "12"):
        return "DC"
    if key in ("ODD", "EVEN"):
        return "PARITY"
    if key in ("P1", "P2"):
        return "WINNER"
    if key[0] in "HA" and key[1] in "OU" or key[:2] in ("PH", "PA"):
        return "TEAM"
    return "OU"


class VCalibrator(Calibrator):
    """Calibrateur isotonique du moteur réel, avec les familles de marchés du virtuel."""

    def fit(self, rows):
        by: dict = {}
        for k, p, y in rows:
            by.setdefault(vfamily(k), ([], []))
            by[vfamily(k)][0].append(p); by[vfamily(k)][1].append(y)
        from ..calibration import pav
        for f, (ps, ys) in by.items():
            if len(ps) >= 400:
                x, yy = pav(np.array(ps), np.array(ys, float))
                self.maps[f] = [x.tolist(), yy.tolist()]
        return self

    def __call__(self, key: str, p: float) -> float:
        m = self.maps.get(vfamily(key))
        if not m:
            return p
        return float(np.clip(0.5 * p + 0.5 * np.interp(p, m[0], m[1]), 0.001, 0.999))


def load_calibrator(code: str) -> VCalibrator:
    path = DATA / "calibration.json"
    maps = json.loads(path.read_text()).get(COMPETITIONS[code].kind, {}) if path.exists() else {}
    return VCalibrator(maps)


class VirtualModel:
    def __init__(self, code: str, history: list, ref: datetime, calib: VCalibrator | None = None, decks: int = 1):
        self.comp = COMPETITIONS[code]
        self.calib = calib if calib is not None else load_calibrator(code)
        self.n_hist = sum(1 for e in history if e.played and e.at < ref)
        if self.comp.kind == "football":
            self.dc = fb.fit(self.comp, history, ref)
        elif self.comp.kind == "penalty":
            self.rates = pen.rates(history, ref)
        else:
            self.probs = bj.shoe(decks)

    def raw_markets(self, ev) -> list[dict]:
        if self.comp.kind == "football":
            return fb.markets(self.dc, self.comp, ev.home, ev.away)
        if self.comp.kind == "penalty":
            return pen.markets(pen.rate(self.rates, ev.home), pen.rate(self.rates, ev.away), ev.home, ev.away)
        return bj.markets(self.probs, rounds=self.comp.rounds)

    def predict(self, ev, odds: dict[str, float] | None = None) -> dict:
        mk = self.raw_markets(ev)
        for x in mk:
            x["p_raw"] = x["p"]
            if not x["key"].startswith(("CS", "PCS")):
                x["p"] = self.calib(x["key"], x["p"])
            x["p"] = round(x["p"], 4)
            x["fair_odds"] = round(1 / max(x["p"], 1e-6), 2)
            x["tier"] = tier(x["p"])
            o = (odds or {}).get(x["key"])
            if o:
                x["odds"] = o
                x["implied"] = round(1 / o, 4)
                x["value"] = round(value(x["p"], o), 4)
                x["kelly"] = round(kelly(x["p"], o), 4) if x["value"] > 0 else 0.0
        for group in (("1", "X", "2"), ("W_P", "W_X", "W_D"), ("P1", "P2"), ("SER_P", "SER_D")):
            xs = [x for x in mk if x["key"] in group]
            tot = sum(x["p"] for x in xs)
            for x in xs:  # les issues complémentaires restent à 100 % après calibration
                x["p"] = round(x["p"] / tot, 4)
                x["fair_odds"], x["tier"] = round(1 / max(x["p"], 1e-6), 2), tier(x["p"])
        mk.sort(key=lambda x: -x["p"])
        pick = next((x for x in mk if x["p"] <= P_MAX), mk[-1])
        out = {"id": ev.id, "competition": self.comp.code, "competition_name": self.comp.name, "kind": self.comp.kind,
               "at": ev.at.isoformat(timespec="minutes"), "home": ev.home, "away": ev.away,
               "history_events": self.n_hist, "pick": pick, "markets": mk}
        if self.comp.kind == "football":
            lh, la = self.dc.rates(ev.home, ev.away)
            out["expected_goals"] = {"home": round(lh, 2), "away": round(la, 2)}
        if self.comp.kind == "penalty":
            out["conversion"] = {"home": round(pen.rate(self.rates, ev.home), 3), "away": round(pen.rate(self.rates, ev.away), 3)}
        if self.comp.kind == "21":
            out["note"] = ("Sabot remélangé à chaque main : les probabilités sont les mêmes pour chaque main "
                           "tant qu'aucune carte n'est visible. Utilisez /decision pendant la main.")
        return out


def settle(code: str, key: str, ev) -> str | None:
    kind = COMPETITIONS[code].kind
    if kind == "football":
        return fb.settle(key, ev)
    if kind == "penalty":
        return pen.settle(key, ev)
    return bj.settle_hand(key, ev.player, ev.dealer) if not key.startswith("SER") else None


STATUS = {"V": "VALIDÉ ✅", "P": "PERDU ❌", "R": "REMBOURSÉ ↩️", None: "EN ATTENTE ⏳"}
