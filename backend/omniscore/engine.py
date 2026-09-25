"""Moteur : ajuste les modèles par ligue et produit les prédictions des matchs à venir."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np

from .calibration import Calibrator
from .data.openfootball import LEAGUES, Match
from .markets import markets
from .models.dixon_coles import DixonColes
from .models.elo import Elo

CALIB_PATH = Path(__file__).resolve().parents[1] / "data" / "calibration.json"
W_DC = 0.65  # poids de Dixon-Coles dans le 1X2 (réglé par omniscore.tune, reste pour Elo)


def run_elo(matches: list[Match], until: date) -> tuple[Elo, list, list]:
    """Elo séquentiel ; renvoie aussi (écart, résultat) pour ajuster le lien 1X2."""
    elo, diffs, outs = Elo(), [], []
    for m in matches:
        if not m.played or m.date >= until:
            continue
        for t in (m.home, m.away):
            if t not in elo.ratings:
                elo.ratings[t] = (np.mean(list(elo.ratings.values())) - 60) if elo.ratings else 1500.0
        diffs.append(elo.diff(m.home, m.away)); outs.append(0 if m.hg > m.ag else 1 if m.hg == m.ag else 2)
        elo.update(m)
    elo.fit_link(diffs[-2000:], outs[-2000:])
    return elo, diffs, outs


def confidence(p: float, agreement: float, completeness: float, market: float = 1.0, risk: float = 0.0) -> float:
    return 100 * p * agreement ** 0.6 * completeness ** 0.7 * market ** 0.9 * (1 - risk) ** 1.2


class LeagueModel:
    def __init__(self, code: str, matches: list[Match], ref: date, calib: Calibrator | None = None):
        self.code = code
        hist = [m for m in matches if m.league == code]
        self.dc = DixonColes().fit(hist, ref)
        self.elo, _, _ = run_elo(hist, ref)
        self.calib = calib or Calibrator()

    def predict(self, m: Match) -> dict:
        M, HT = self.dc.matrix(m.home, m.away), self.dc.ht_matrix(m.home, m.away)
        lh, la = self.dc.rates(m.home, m.away)
        e1, eX, e2 = self.elo.probs(m.home, m.away)
        i, j = np.indices(M.shape)
        d1, dX, d2 = M[i > j].sum(), np.trace(M), M[i < j].sum()
        agree = 1 - max(abs(d1 - e1), abs(dX - eX), abs(d2 - e2))
        comp = min(1.0, min(self.dc.n_matches.get(m.home, 0), self.dc.n_matches.get(m.away, 0)) / 20)
        mk = markets(M, HT, m.home, m.away)
        # 1X2 : mélange Dixon-Coles / Elo (meilleur RPS en validation), marchés dérivés recalculés
        b1, bX, b2 = (W_DC * d1 + (1 - W_DC) * e1, W_DC * dX + (1 - W_DC) * eX, W_DC * d2 + (1 - W_DC) * e2)
        blend = {"1": b1, "X": bX, "2": b2, "1X": b1 + bX, "X2": bX + b2, "12": b1 + b2, "DNB1": b1 / (b1 + b2), "DNB2": b2 / (b1 + b2)}
        for x in mk:
            if x["key"] in blend:
                x["p"] = float(blend[x["key"]])
        for x in mk:
            x["p_raw"] = x["p"]
            if not x["key"].startswith("CS"):
                x["p"] = self.calib(x["key"], x["p"])
            x["fair_odds"] = round(1 / max(x["p"], 1e-6), 2)
            x["confidence"] = round(confidence(x["p"], agree, max(comp, 0.3)), 1)
        # cohérence 1X2 après calibration
        s = sum(x["p"] for x in mk if x["key"] in ("1", "X", "2"))
        for x in mk:
            if x["key"] in ("1", "X", "2"):
                x["p"] /= s
        return {
            "id": m.id, "league": self.code, "league_name": LEAGUES.get(self.code, self.code),
            "date": m.date.isoformat(), "time": m.time, "round": m.round, "home": m.home, "away": m.away,
            "xg": {"home": round(lh, 2), "away": round(la, 2)},
            "elo": {"home": round(self.elo.ratings.get(m.home, 0)), "away": round(self.elo.ratings.get(m.away, 0)),
                    "p": [round(e1, 3), round(eX, 3), round(e2, 3)]},
            "model_agreement": round(agree, 3), "data_completeness": round(comp, 3),
            "markets": mk,
        }


def upcoming_predictions(matches: list[Match], today: date | None = None, days: int = 14) -> list[dict]:
    today = today or date.today()
    calib = Calibrator.load(CALIB_PATH)
    out = []
    for code in sorted({m.league for m in matches}):
        fut = [m for m in matches if m.league == code and not m.played and today <= m.date <= today + timedelta(days=days)]
        if not fut:
            continue
        lm = LeagueModel(code, matches, today, calib)
        out.extend(lm.predict(m) for m in fut)
    out.sort(key=lambda p: (p["date"], p["time"] or "", p["league"]))
    return out
