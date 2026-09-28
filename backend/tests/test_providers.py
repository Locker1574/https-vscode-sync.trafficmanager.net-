"""Connecteurs d'API testés sur des réponses enregistrées (aucun appel réseau, aucune clé réelle)."""
from datetime import date, datetime, timezone

from omniscore.data.openfootball import Match
from omniscore.providers import allsports, api_football, football_data, odds_api
from omniscore.providers.names import same_team

FD_MATCHES = {"matches": [
    {"utcDate": "2026-10-03T14:00:00Z", "status": "FINISHED", "homeTeam": {"name": "Arsenal FC"}, "awayTeam": {"name": "Chelsea FC"},
     "score": {"fullTime": {"home": 2, "away": 1}, "halfTime": {"home": 1, "away": 0}}},
    {"utcDate": "2026-10-10T14:00:00Z", "status": "TIMED", "homeTeam": {"name": "Liverpool FC"}, "awayTeam": {"name": "Everton FC"},
     "score": {"fullTime": {"home": None, "away": None}, "halfTime": {"home": None, "away": None}}},
]}
FD_TABLE = {"standings": [{"type": "TOTAL", "table": [
    {"position": i + 1, "team": {"name": n}, "playedGames": 7, "points": 20 - i, "goalDifference": 5 - i, "form": "W,W,D"}
    for i, n in enumerate(["Arsenal FC", "Chelsea FC", "Liverpool FC", "Aston Villa FC", "Newcastle United FC", "Brighton & Hove Albion FC",
                           "Fulham FC", "Everton FC", "Brentford FC", "Wolverhampton Wanderers FC", "West Ham United FC", "Leeds United FC",
                           "Burnley FC", "Sunderland AFC", "Nottingham Forest FC", "Crystal Palace FC", "Tottenham Hotspur FC",
                           "Manchester United FC", "AFC Bournemouth", "Manchester City FC"])]}]}


def test_same_team_matches_provider_spellings():
    assert same_team("Manchester City FC", "Manchester City")
    assert same_team("Sporting Clube de Braga", "SC Braga")
    assert not same_team("Manchester City FC", "Manchester United FC")


def test_football_data_fills_score_and_half_time(monkeypatch):
    monkeypatch.setenv("FOOTBALL_DATA_KEY", "test")
    monkeypatch.setattr(football_data, "get_json", lambda *a, **k: FD_MATCHES)
    ms = [Match("en.1", "2026-27", date(2026, 10, 3), "15:00", None, "Arsenal FC", "Chelsea FC"),
          Match("en.1", "2026-27", date(2026, 10, 10), "15:00", None, "Liverpool FC", "Everton FC")]
    out, n = football_data.enrich(ms)
    assert n == 1 and (out[0].hg, out[0].ag, out[0].hthg, out[0].htag) == (2, 1, 1, 0) and not out[1].played


def test_football_data_stakes_from_real_table(monkeypatch):
    monkeypatch.setenv("FOOTBALL_DATA_KEY", "test")
    monkeypatch.setattr(football_data, "get_json", lambda *a, **k: FD_TABLE)
    preds = [{"league": "en.1", "home": "Arsenal FC", "away": "Manchester City FC"},
             {"league": "en.1", "home": "Fulham FC", "away": "Everton FC"}]
    assert football_data.attach_context(preds) == 2
    assert preds[0]["stake"]["label"] in ("Course au titre", "Maintien") and preds[0]["stake"]["home"]["pos"] == 1
    assert preds[1]["stake"]["label"] == "Milieu de tableau"


def test_odds_attach_value_and_history(monkeypatch, tmp_path):
    monkeypatch.setenv("ODDS_API_KEY", "test")
    monkeypatch.setattr(odds_api, "HISTORY", tmp_path / "h.json")
    ev = [{"home_team": "Arsenal", "away_team": "Chelsea", "bookmakers": [
        {"title": "Book A", "markets": [{"key": "h2h", "outcomes": [{"name": "Arsenal", "price": 2.1}, {"name": "Chelsea", "price": 3.6}, {"name": "Draw", "price": 3.4}]},
                                        {"key": "totals", "outcomes": [{"name": "Over", "point": 2.5, "price": 1.9}, {"name": "Under", "point": 2.5, "price": 1.95}]}]}]}]
    monkeypatch.setattr(odds_api, "get_json", lambda *a, **k: ev)
    preds = [{"id": "m1", "league": "en.1", "home": "Arsenal FC", "away": "Chelsea FC",
              "markets": [{"key": "1", "p": 0.55}, {"key": "O2.5", "p": 0.5}, {"key": "BTTS_Y", "p": 0.5}]}]
    assert odds_api.attach_odds(preds) == 1
    mk = {m["key"]: m for m in preds[0]["markets"]}
    assert mk["1"]["odds"] == 2.1 and abs(mk["1"]["value"] - (0.55 * 2.1 - 1)) < 1e-9 and "odds" not in mk["BTTS_Y"]
    assert (tmp_path / "h.json").exists()


def test_api_football_live_parsing(monkeypatch):
    monkeypatch.setenv("API_FOOTBALL_KEY", "test")
    resp = {"response": [
        {"league": {"id": 39}, "fixture": {"status": {"elapsed": 63, "short": "2H"}}, "teams": {"home": {"name": "Arsenal"}, "away": {"name": "Chelsea"}},
         "goals": {"home": 1, "away": 1}, "events": [{"time": {"elapsed": 12}, "type": "Goal", "detail": "Normal Goal", "team": {"name": "Arsenal"}}]},
        {"league": {"id": 999}, "fixture": {}, "teams": {}, "goals": {}}]}
    monkeypatch.setattr(api_football, "get_json", lambda *a, **k: resp)
    live = api_football.live()
    assert len(live) == 1 and live[0]["minute"] == 63 and live[0]["events"][0]["team"] == "h"


def test_allsports_live_parsing(monkeypatch):
    monkeypatch.setenv("ALLSPORTS_KEY", "test")
    resp = {"result": [{"league_name": "Premier League", "country_name": "England", "event_home_team": "Arsenal",
                        "event_away_team": "Chelsea", "event_final_result": "2 - 0", "event_status": "71", "goalscorers": []},
                       {"league_name": "Premier League", "country_name": "Egypt", "event_home_team": "X", "event_away_team": "Y",
                        "event_final_result": "0 - 0", "event_status": "10"}]}
    monkeypatch.setattr(allsports, "get_json", lambda *a, **k: resp)
    live = allsports.live()
    assert len(live) == 1 and (live[0]["hg"], live[0]["ag"], live[0]["minute"]) == (2, 0, 71)


def test_no_keys_means_no_calls(monkeypatch):
    for k in ("ODDS_API_KEY", "FOOTBALL_DATA_KEY", "API_FOOTBALL_KEY", "ALLSPORTS_KEY"):
        monkeypatch.delenv(k, raising=False)
    boom = lambda *a, **k: (_ for _ in ()).throw(AssertionError("appel réseau sans clé"))  # noqa: E731
    for mod in (odds_api, football_data, api_football, allsports):
        monkeypatch.setattr(mod, "get_json", boom)
    assert odds_api.fetch_odds("en.1") == [] and api_football.live() == [] and allsports.live() == []
    assert football_data.enrich([])[1] == 0
    assert datetime.now(timezone.utc)


FDUK_CSV = """Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,HS,AS,HST,AST,HF,AF,HC,AC,HY,AY,HR,AR
E0,03/10/2026,15:00,Man City,Nott'm Forest,3,0,21,6,9,2,8,12,11,2,1,3,0,1
E0,03/10/2026,17:30,Arsenal,Chelsea,2,1,14,10,6,4,10,11,7,5,2,2,0,0
"""


def test_match_stats_reads_football_data_co_uk_csv():
    from omniscore.providers import match_stats
    rows = match_stats.parse_fduk(FDUK_CSV)
    assert rows[0]["h"] == {"corners": 11, "shots": 21, "sot": 9, "fouls": 8, "cards": 1}
    assert rows[0]["a"]["cards"] == 4  # 3 jaunes + 1 rouge
    assert match_stats.team_match("Man City", "Manchester City FC")
    assert match_stats.team_match("Nott'm Forest", "Nottingham Forest FC")
    assert not match_stats.team_match("Man City", "Manchester United FC")


def test_match_stats_collect_pairs_rows_and_respects_quota(monkeypatch):
    from omniscore.providers import match_stats
    monkeypatch.setattr(match_stats, "_fetch_csv", lambda url, ttl_s: FDUK_CSV if "2627/E0" in url else None)
    g = Match("en.1", "2026/27", date(2026, 10, 3), "15:00", None, "Manchester City FC", "Nottingham Forest FC", 3, 0)
    calls = []
    monkeypatch.setenv("API_FOOTBALL_KEY", "test")

    def fake_get(url, params=None, headers=None, ttl_s=0, secret_params=()):
        calls.append(url)
        if url.endswith("/fixtures"):
            return {"response": [{"fixture": {"id": 7, "date": "2026-10-03T14:00:00+00:00"},
                                  "teams": {"home": {"name": "Manchester City"}, "away": {"name": "Nottingham Forest"}}}]}
        return {"response": [{"statistics": [{"type": "Offsides", "value": 2}, {"type": "expected_goals", "value": "2.71"}]},
                             {"statistics": [{"type": "Offsides", "value": None}, {"type": "expected_goals", "value": "0.40"}]}]}
    monkeypatch.setattr(match_stats, "get_json", fake_get)
    monkeypatch.setattr(match_stats, "CACHE", match_stats.Path("/nonexistent-omniscore-cache"))
    out = match_stats.collect([g], today=date(2026, 10, 5))
    assert out[g.id]["h"] == {"corners": 11, "shots": 21, "sot": 9, "fouls": 8, "cards": 1, "offsides": 2, "xg": 2.71}
    assert out[g.id]["a"]["offsides"] == 0 and out[g.id]["a"]["xg"] == 0.4
    calls.clear()
    assert match_stats.collect([g], today=date(2026, 10, 5), max_calls=1)[g.id]["h"].get("xg") is None
    assert len(calls) == 1  # une seule requête autorisée : la liste des matchs, pas les statistiques
