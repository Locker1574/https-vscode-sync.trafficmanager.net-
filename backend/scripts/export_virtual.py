"""Injecte data/virtual/demo.json (ou latest.json) dans prototype/virtuel.html.

Usage : python -m omniscore.virtual demo && python scripts/export_virtual.py [--real]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT.parent / "prototype" / "virtuel.html"
src = ROOT / "data" / "virtual" / ("latest.json" if "--real" in sys.argv else "demo.json")
d = json.loads(src.read_text())


def ev(p):
    return {"id": p["id"], "at": p["at"], "h": p["home"], "a": p["away"], "xg": p.get("expected_goals"),
            "conv": p.get("conversion"), "n": p["history_events"], "note": p.get("note"), "pick": p["pick"]["key"],
            "mk": [[x["key"], x["label"], x["group"], x["p"], x.get("odds"), x.get("value"), x.get("kelly")] for x in p["markets"]]}


def bt(b):
    c = b["calibre"]
    return {"n": c["events"], "brier": c["brier"], "brier_brut": b["brut"]["brier"], "tiers": c["by_tier"], "pick": c["pick"]}


comps = [{"code": c["code"], "name": c["name"], "kind": c["kind"], "n": c["history_events"], "up": [ev(p) for p in c["upcoming"]],
          "bt": bt(c["backtest"]), "pat": c["patterns"],
          "jr": [[i["at"], i["match"], i["label"], i["p"], i["status"]] for i in c["journal"]]} for c in d["competitions"]]
blob = json.dumps({"generated": d["generated"], "simulated": d["simulated"], "comps": comps, "stats": d["journal_stats"]},
                  ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = HTML.read_text()
new = re.sub(r'(<script id="vdata" type="application/json">).*?(</script>)', lambda m: m.group(1) + blob + m.group(2), html, flags=re.S)
if '<script id="vdata"' not in html:
    raise SystemExit('marqueur <script id="vdata"> absent de virtuel.html')
HTML.write_text(new)
print(f"{len(comps)} compétitions injectées ({len(blob) // 1024} Ko) → {HTML}")
