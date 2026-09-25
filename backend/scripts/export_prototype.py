"""Injecte les vraies prédictions et le rapport de backtest dans prototype/omniscore.html.

Usage : python -m omniscore.cli predict && python scripts/export_prototype.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT.parent / "prototype" / "omniscore.html"
KEEP = {"1", "X", "2", "1X", "X2", "12", "O1.5", "U1.5", "O2.5", "U2.5", "O3.5", "U3.5", "BTTS_Y", "BTTS_N",
        "HO0.5", "AO0.5", "HT1", "HTX", "HT2", "HTO0.5", "HTU0.5", "HTU1.5", "O0.5", "U4.5", "DNB1", "DNB2"}

pred = json.loads((ROOT / "data" / "predictions.json").read_text())
bt = json.loads((ROOT / "data" / "backtest.json").read_text())
matches = [{
    "id": m["id"], "lg": m["league"], "d": m["date"], "t": m["time"], "h": m["home"], "a": m["away"],
    "xg": [m["xg"]["home"], m["xg"]["away"]], "elo": [m["elo"]["home"], m["elo"]["away"]], "ag": m["model_agreement"], "dc": m["data_completeness"],
    "mk": [[x["key"], x["label"], round(x["p"], 4), x["confidence"]] + ([x["odds"], round(x["value"], 4)] if "odds" in x else []) for x in m["markets"] if x["key"] in KEEP or x["key"].startswith("CS")],
} for m in pred["matches"]]
t = bt["test_calibrated"]
report = {
    "leagues": bt["leagues"], "train": bt["train_seasons"], "test": bt["test_seasons"], "n": bt["all_seasons"]["n"],
    "models": {k: bt["all_seasons"][k] for k in ("base", "elo", "dc", "blend")},
    "calib": bt["all_seasons"]["calibration_all_markets"], "per_league": bt["per_league"],
    "top": t["top_picks"], "coupons": t["coupons"], "n_test": t["n"],
}
blob = json.dumps({"generated": pred["generated"], "with_odds": pred["with_odds"], "matches": matches, "report": report}, ensure_ascii=False, separators=(",", ":"))
blob = blob.replace("</", "<\\/")
html = HTML.read_text()
new = re.sub(r'(<script id="realdata" type="application/json">).*?(</script>)', lambda m: m.group(1) + blob + m.group(2), html, flags=re.S)
if new == html and '<script id="realdata"' not in html:
    raise SystemExit("marqueur <script id=\"realdata\"> absent du prototype")
HTML.write_text(new)
print(f"{len(matches)} matchs réels injectés ({len(blob)//1024} Ko)")
