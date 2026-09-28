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
    "mk": [[x["key"], x["label"], round(x["p"], 4), x["confidence"]] + ([x["odds"], round(x["value"], 4), x.get("bookmaker")] if "odds" in x else [])
           for x in m["markets"] if x["key"] in KEEP or x["key"].startswith("CS")],
    **({"stake": m["stake"]} if m.get("stake") else {}), **({"abs": m["absences"]} if m.get("absences") else {}),
} for m in pred["matches"]]
t = bt["test_calibrated"]
report = {
    "leagues": bt["leagues"], "train": bt["train_seasons"], "test": bt["test_seasons"], "n": bt["all_seasons"]["n"],
    "models": {k: bt["all_seasons"][k] for k in ("base", "elo", "dc", "blend")},
    "calib": bt["all_seasons"]["calibration_all_markets"], "per_league": bt["per_league"],
    "top": t["top_picks"], "coupons": t["coupons"], "n_test": t["n"],
}
track_path = ROOT / "data" / "track_summary.json"
track = json.loads(track_path.read_text()) if track_path.exists() else None
# Scores finaux par match (journal réel) : servent à régler les coupons enregistrés dans la page.
full_track_path = ROOT / "data" / "track.json"
full_track = json.loads(full_track_path.read_text()) if full_track_path.exists() else {}
results = {mid: t["result"] + (t.get("ht") or []) for mid, t in full_track.items() if t.get("result")}
# Journal réel complet : la sélection figée de chaque match (onglet Journal).
picks = {mid: {"lg": t["league"], "d": t["date"], "h": t["home"], "a": t["away"], "fz": t["frozen"], **t["pick"]}
         for mid, t in full_track.items() if t.get("pick")}
live_path = ROOT / "data" / "live.json"
live = json.loads(live_path.read_text()) if live_path.exists() else None
hist_path = ROOT / "data" / "odds_history.json"
odds_hist = json.loads(hist_path.read_text()) if hist_path.exists() else {}
odds_hist = {mid: h for mid, h in odds_hist.items() if any(m["id"] == mid for m in matches)}
# Statistiques réelles par équipe : les 10 derniers matchs joués (résultats officiels).
import sys  # noqa: E402
sys.path.insert(0, str(ROOT))
from omniscore.cli import load_matches  # noqa: E402

from omniscore.providers import match_stats  # noqa: E402

team_ids = {f'{m["lg"]}|{t}' for m in matches for t in (m["h"], m["a"])}
games: dict[str, list] = {}
for g in load_matches(first=2024):
    if not g.played:
        continue
    for team in (g.home, g.away):
        if f"{g.league}|{team}" in team_ids:
            games.setdefault(f"{g.league}|{team}", []).append(g)
last10 = {tid: sorted(v, key=lambda g: g.date)[-10:] for tid, v in games.items()}
# Statistiques de match réelles (corners, tirs, cartons… ; hors-jeux et xG) des seuls matchs affichés.
mstats = match_stats.collect({g.id: g for v in last10.values() for g in v}.values())
# Ligne : [date, 'H'|'A', adversaire, bp, bc, bp_mt, bc_mt, {stat: [pour, contre]}]
team_stats = {}
for tid, v in last10.items():
    rows = []
    for g in v:
        side = "H" if f"{g.league}|{g.home}" == tid else "A"
        gf, ga = (g.hg, g.ag) if side == "H" else (g.ag, g.hg)
        hgf, hga = (g.hthg, g.htag) if side == "H" else (g.htag, g.hthg)
        st = mstats.get(g.id)
        me, op = (st["h"], st["a"]) if st and side == "H" else ((st["a"], st["h"]) if st else ({}, {}))
        extra = {k: [me[k], op[k]] for k in match_stats.METRICS if k in me and k in op}
        rows.append([g.date.isoformat(), side, g.away if side == "H" else g.home, gf, ga, hgf, hga] + ([extra] if extra else []))
    team_stats[tid] = rows
print(f"statistiques de match : {len(mstats)} matchs (football-data.co.uk / API-Football)")

blob = json.dumps({"generated": pred["generated"], "with_odds": pred["with_odds"], "matches": matches, "report": report, "track": track,
                   "results": results, "picks": picks, "standings": pred.get("standings") or {}, "live": live,
                   "odds_history": odds_hist, "team_stats": team_stats, "w_dc": 0.65}, ensure_ascii=False, separators=(",", ":"))
blob = blob.replace("</", "<\\/")
html = HTML.read_text()
new = re.sub(r'(<script id="realdata" type="application/json">).*?(</script>)', lambda m: m.group(1) + blob + m.group(2), html, flags=re.S)
if new == html and '<script id="realdata"' not in html:
    raise SystemExit("marqueur <script id=\"realdata\"> absent du prototype")
HTML.write_text(new)
print(f"{len(matches)} matchs réels injectés ({len(blob)//1024} Ko)")
