from datetime import date, timedelta

import numpy as np
import pytest

from omniscore import coupon
from omniscore.data.openfootball import Match
from omniscore.integrity import analyse
from omniscore.markets import markets, settle
from omniscore.models.dixon_coles import DixonColes, score_matrix
from omniscore.value import devig_multiplicative, devig_shin, kelly, value


def synthetic(n_rounds=60, seed=1):
    rng = np.random.default_rng(seed)
    teams = [f"T{i}" for i in range(10)]
    att = dict(zip(teams, np.linspace(-0.4, 0.4, 10)))
    out, d0 = [], date(2024, 1, 1)
    for r in range(n_rounds):
        order = rng.permutation(teams)
        for h, a in zip(order[::2], order[1::2]):
            lh, la = np.exp(0.1 + 0.25 + att[h] - att[a] * 0.5), np.exp(0.1 + att[a] - att[h] * 0.5)
            out.append(Match("x", "2024-25", d0 + timedelta(days=7 * r), None, None, h, a, int(rng.poisson(lh)), int(rng.poisson(la))))
    return out, att


def test_score_matrix_sums_to_one():
    M = score_matrix(1.6, 1.1, -0.05)
    assert M.sum() == pytest.approx(1.0)
    assert (M >= 0).all()


def test_fit_recovers_team_order_and_home_advantage():
    ms, att = synthetic()
    dc = DixonColes(l2=0.5).fit(ms, date(2026, 1, 1))
    est = sorted(dc.attack, key=dc.attack.get)
    assert est[0] in ("T0", "T1") and est[-1] in ("T8", "T9")
    assert 0.1 < dc.home < 0.45
    assert -0.25 <= dc.rho <= 0.25


def test_fit_ignores_future_matches():
    ms, _ = synthetic()
    cut = ms[len(ms) // 2].date
    a = DixonColes().fit(ms, cut)
    b = DixonColes().fit([m for m in ms if m.date < cut], cut)
    assert a.attack == pytest.approx(b.attack)


def test_markets_are_consistent():
    M = score_matrix(1.5, 1.2, -0.05)
    mk = {m["key"]: m["p"] for m in markets(M, score_matrix(0.66, 0.53), "A", "B")}
    assert mk["1"] + mk["X"] + mk["2"] == pytest.approx(1)
    assert mk["O2.5"] + mk["U2.5"] == pytest.approx(1)
    assert mk["1X"] == pytest.approx(mk["1"] + mk["X"])
    assert mk["O0.5"] > mk["O1.5"] > mk["O2.5"] > mk["O3.5"]


@pytest.mark.parametrize("key,score,ht,expected", [
    ("1", (2, 1), (1, 0), "V"), ("X2", (2, 1), (1, 0), "P"), ("DNB1", (1, 1), (0, 0), "R"),
    ("O2.5", (2, 1), (1, 0), "V"), ("U2.5", (2, 1), (1, 0), "P"), ("BTTS_Y", (2, 0), (1, 0), "P"),
    ("HO1.5", (2, 0), (1, 0), "V"), ("AU0.5", (2, 0), (1, 0), "V"), ("HT1", (2, 1), (1, 0), "V"),
    ("HTO1.5", (2, 1), (1, 0), "P"), ("CS2-1", (2, 1), (1, 0), "V"), ("HTX", (2, 1), (None, None), None),
])
def test_settle(key, score, ht, expected):
    assert settle(key, *score, *ht) == expected


def test_devig_and_kelly():
    odds = [1.9, 3.6, 4.4]
    for f in (devig_multiplicative, devig_shin):
        p = f(odds)
        assert sum(p) == pytest.approx(1)
    assert devig_shin(odds)[0] > devig_multiplicative(odds)[0]  # Shin retire plus de marge aux outsiders
    assert value(0.6, 2.0) == pytest.approx(0.2)
    assert kelly(0.6, 2.0, fraction=1, cap=1) == pytest.approx(0.2)
    assert kelly(0.4, 2.0) == 0


def test_integrity_flags_sudden_drop():
    rng = np.random.default_rng(3)
    calm = list(2.0 * np.exp(np.cumsum(rng.normal(0, 0.005, 48))))
    assert analyse(calm)["risk"] < 25
    moved = calm[:30] + [x * 0.75 for x in calm[30:]]
    r = analyse(moved, bookmaker_spread=0.06, volume_ratio=4)
    assert r["risk"] >= 75 and r["events"]


def _preds():
    mk = lambda k, p: {"key": k, "label": k, "p": p, "confidence": p * 100, "fair_odds": 1 / p}
    return [{"id": f"m{i}", "home": "A", "away": "B", "date": "2026-10-10",
             "markets": [mk("O0.5", 0.90 - i * 0.02), mk("1X", 0.75)]} for i in range(6)]


def test_generate_one_selection_per_match_within_range():
    c = coupon.generate(_preds(), 3, pmin=0.70, pmax=0.98)
    assert c["size"] == 3 and len({s["match_id"] for s in c["selections"]}) == 3
    assert all(0.70 <= s["p"] <= 0.98 for s in c["selections"])
    assert c["combined_probability"] == pytest.approx(np.prod([s["p"] for s in c["selections"]]))


def test_regenerate_keeps_better_selections():
    preds = _preds()
    cur = coupon.generate(preds, 3)["selections"]
    res = coupon.regenerate(preds, cur, 3)
    assert res["replaced"] == 0 and "optimal" in res["message"]
    assert [s["match_id"] for s in res["selections"]] == [s["match_id"] for s in sorted(cur, key=lambda s: -s["p"])]
    weak = [{**s, "p": 0.71} for s in cur]
    res2 = coupon.regenerate(preds, weak, 3)
    assert res2["replaced"] == 3 and all(s["p"] > 0.71 for s in res2["selections"])
