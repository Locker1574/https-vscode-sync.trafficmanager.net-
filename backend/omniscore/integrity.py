"""Détection d'anomalies de marché sur une série de cotes (signaux, pas des preuves)."""
from __future__ import annotations

import numpy as np

LEVELS = ["Normal", "À surveiller", "Suspect", "Très suspect"]


def analyse(odds_series: list[float], bookmaker_spread: float = 0.0, volume_ratio: float = 1.0) -> dict:
    s = np.asarray(odds_series, float)
    if len(s) < 5:
        return {"risk": 0, "level": LEVELS[0], "events": [], "max_z": 0.0}
    r = np.diff(np.log(s))
    mad = np.median(np.abs(r - np.median(r))) or 1e-3
    z = (r - np.median(r)) / (1.4826 * mad)
    events = [
        {"index": int(k + 1), "pct": float((np.exp(r[k]) - 1) * 100), "z": float(abs(z[k])),
         "severity": 1 if abs(z[k]) < 5 else 2 if abs(z[k]) < 9 else 3 if abs(z[k]) < 15 else 4}
        for k in range(len(r)) if abs(z[k]) > 3.2
    ]
    mz = float(np.abs(z).max())
    risk = min(70, max(0, (mz - 3.2) * 6)) + (bookmaker_spread * 160 if bookmaker_spread > 0.04 else 0)
    risk += 12 if volume_ratio > 3 else 0
    risk = int(round(min(100, risk)))
    return {"risk": risk, "level": LEVELS[0 if risk < 25 else 1 if risk < 50 else 2 if risk < 75 else 3],
            "events": events, "max_z": mz}
