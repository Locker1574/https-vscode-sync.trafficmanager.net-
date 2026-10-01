from datetime import datetime

import numpy as np
import pytest
from fastapi.testclient import TestClient

from omniscore.virtual import blackjack as bj
from omniscore.virtual import demo, football as fb, penalty as pen
from omniscore.virtual.competitions import COMPETITIONS
from omniscore.virtual.journal import Journal
from omniscore.virtual.patterns import ljung_box, runs_test
from omniscore.virtual.predictor import P_MAX, VCalibrator, VirtualModel


def test_catalogue_covers_all_requested_competitions():
    assert len(COMPETITIONS) == 20
    assert {c.kind for c in COMPETITIONS.values()} == {"football", "penalty", "21"}
    assert COMPETITIONS["21-dota-bo3"].rounds == 3


@pytest.fixture(scope="module")
def rush():
    code = "fc26-rush-superligue"
    h = demo.history(code, 1200)
    return code, h, VirtualModel(code, h[:1000], h[1000].at, VCalibrator({}))


def test_football_markets_are_coherent(rush):
    code, h, m = rush
    mk = {x["key"]: x["p"] for x in m.raw_markets(h[1000])}
    assert mk["1"] + mk["X"] + mk["2"] == pytest.approx(1)
    assert sum(v for k, v in mk.items() if k.startswith("HF")) == pytest.approx(1, abs=1e-6)
    assert mk["ODD"] + mk["EVEN"] == pytest.approx(1)
    assert mk["FTS_H"] + mk["FTS_A"] + mk["FTS_N"] == pytest.approx(1)
    for k, p in mk.items():
        if k.startswith("AHH"):
            assert p + mk["AHA" + f"{-float(k[3:]):+}"] == pytest.approx(1)


def test_football_scoring_rate_matches_format(rush):
    code, h, m = rush
    lh, la = m.dc.rates(h[1000].home, h[1000].away)
    observed = np.mean([e.hg + e.ag for e in h[:1000]])
    assert 0.6 * observed < lh + la < 1.6 * observed  # 5x5 : bien plus de buts qu'au 11 contre 11


def test_football_settlement():
    ev = fb.VMatch("x", "e", datetime(2026, 1, 1), "A", "B", 3, 1, 0, 1, "A")
    assert fb.settle("AHH-1.5", ev) == "V" and fb.settle("AHH-2.5", ev) == "P"
    assert fb.settle("AHA+1.5", ev) == "P" and fb.settle("AHA+2.5", ev) == "V"
    assert fb.settle("HF21", ev) == "V" and fb.settle("HFX1", ev) == "P"
    assert fb.settle("EVEN", ev) == "V" and fb.settle("MGH2", ev) == "V"
    assert fb.settle("FTS_A", ev) == "V" and fb.settle("CLEAN_H", ev) == "P"
    assert fb.settle("O3.5", ev) == "V" and fb.settle("1", ev) == "V"


def test_penalty_exact_model_matches_simulation():
    pa, pb = 0.78, 0.70
    D = pen.distribution(pa, pb)
    assert sum(D.values()) == pytest.approx(1, abs=1e-3)
    comp = COMPETITIONS["penalty"]
    rng = np.random.default_rng(3)
    sims = demo.penalties(comp, 1, seed=0)  # vérifie juste le format
    assert set(sims[0].kicks) <= {"0", "1"}
    # Monte-Carlo de la mort subite et du vainqueur
    n, sd, win = 40000, 0, 0
    for _ in range(n):
        a = rng.random(5) < pa; b = rng.random(5) < pb
        if a.sum() == b.sum():
            sd += 1
            while True:
                x, y = rng.random() < pa, rng.random() < pb
                if x != y:
                    win += x; break
        else:
            win += a.sum() > b.sum()
    mk = {x["key"]: x["p"] for x in pen.markets(pa, pb, "A", "B")}
    assert mk["SD_Y"] == pytest.approx(sd / n, abs=0.01)
    assert mk["P1"] == pytest.approx(win / n, abs=0.01)


def test_penalty_settlement():
    s = pen.Shootout("p", "e", datetime(2026, 1, 1), "A", "B", "1111111111" + "10")
    assert s.score == (6, 5) and pen.settle("SD_Y", s) == "V" and pen.settle("P1", s) == "V"


def test_blackjack_reference_values():
    probs = bj.shoe(1)
    assert bj.final_dist([], 17, probs)[22] == pytest.approx(0.2816, abs=0.002)  # croupier dépasse 21
    w, d, l = bj.compare(bj.final_dist([], 17, probs), bj.final_dist([], 17, probs))
    sw, sd, sl = bj.simulate(30000, 1, seed=1)
    assert w == pytest.approx(sw, abs=0.012) and d == pytest.approx(sd, abs=0.012)
    assert bj.decision([10, 6], 10, probs)["conseil"] == "tirer"
    assert bj.decision([5, 6], 6, probs)["conseil"] == "doubler"
    assert bj.decision([10, 8], 7, probs)["conseil"] == "rester"


def test_series_race_to_three():
    s = bj.series(0.45, 0.45, 3)
    assert sum(s.values()) == pytest.approx(1)
    assert s[(3, 0)] == pytest.approx(0.125)
    assert bj.hand([11, 11, 9])[0] == 21


def test_predict_ranks_and_picks(rush):
    code, h, m = rush
    p = m.predict(h[1000], {"1": 2.0})
    ps = [x["p"] for x in p["markets"]]
    assert ps == sorted(ps, reverse=True)
    assert p["pick"]["p"] <= P_MAX and p["pick"]["p"] == max(x for x in ps if x <= P_MAX)
    one = next(x for x in p["markets"] if x["key"] == "1")
    assert one["value"] == pytest.approx(one["p"] * 2 - 1, abs=1e-3)


def test_journal_freezes_and_settles(tmp_path, rush):
    code, h, m = rush
    j = Journal(tmp_path / "j.json")
    pred = m.predict(h[1000])
    assert len(j.freeze(pred, options=3)) == 3
    assert len(j.freeze(pred, options=3)) == 0  # jamais en double
    assert j.settle(code, h[1000]) >= 2
    assert {i["status"] for i in j.items} <= {"VALIDÉ ✅", "PERDU ❌", "REMBOURSÉ ↩️", "EN ATTENTE ⏳"}
    assert j.stats()["global"]["n"] >= 2


def test_patterns_detect_dependence():
    rng = np.random.default_rng(0)
    assert runs_test(rng.random(2000) < 0.5)["p"] > 0.01
    assert runs_test(np.arange(2000) % 2 == 0)["p"] < 1e-6
    ar = np.zeros(2000)
    for i in range(1, 2000):
        ar[i] = 0.6 * ar[i - 1] + rng.normal()
    assert ljung_box(ar)["p"] < 1e-6


def test_api():
    from omniscore.api import app
    c = TestClient(app)
    assert len(c.get("/v1/virtual/competitions").json()) == 20
    r = c.post("/v1/virtual/21/decision", json={"player": [10, 6], "dealer_up": 10}).json()
    assert r["conseil"] == "tirer"
    t = demo.teams(COMPETITIONS["fc26-spain"])
    r = c.post("/v1/virtual/fc26-spain/predict", json={"home": t[0], "away": t[1], "odds": {"1": 2.1}}).json()
    assert r["pick"]["p"] <= P_MAX and any("value" in x for x in r["markets"])
    assert c.post("/v1/virtual/21-dota-bo3/predict", json={}).json()["markets"]
