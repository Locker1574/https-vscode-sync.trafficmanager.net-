# OMNISCORE : moteur Python

Moteur de prédiction sur **données réelles** : résultats officiels des 5 grands championnats depuis 2020 ([openfootball/football.json](https://github.com/openfootball/football.json), domaine public, sans clé).

## Modèles
- **Dixon-Coles** (Poisson bivarié corrigé, pondération temporelle ξ = 0,0019/jour, rétrécissement L2 pour les promus), ajusté par Newton-Raphson, ρ par maximum de vraisemblance.
- **Elo** (échelle ClubElo, multiplicateur d'écart de buts) + logit ordonné ajusté pour produire des probabilités 1X2.
- **Calibration isotonique** (PAV) par famille de marchés, apprise sur le backtest.
- Marchés : 1X2, double chance, remboursé si nul, plus/moins 0,5 à 4,5, les deux marquent, buts par équipe, 1re mi-temps (part des buts de 1re MT estimée par ligue), scores exacts.
- Value (`p × cote − 1`), retrait de marge multiplicatif et de Shin, Kelly fractionné, score d'intégrité (z-score robuste).

## Résultats du backtest walk-forward (9 211 matchs réels, 8 ligues, saisons 2023-24 à 2026-27)
Ligues : Premier League, LaLiga, Serie A, Bundesliga, Ligue 1, Eredivisie, Liga Portugal, Championship.

| Modèle | RPS | Log-loss | Précision 1X2 |
|---|---|---|---|
| Fréquences de la ligue | 0,2301 | 1,0766 | 43,2 % |
| Elo | 0,2026 | 0,9958 | 50,8 % |
| Dixon-Coles | 0,2013 | 0,9922 | 51,1 % |
| Mélange 65 % DC + 35 % Elo (production) | 0,2009 | 0,9903 | 51,2 % |

Calibration sur 145 210 prédictions de marchés : 70-80 % annoncé → 74 % observé ; 80-90 % → 85 % ; 90-98 % → 93 %.
Coupons testés sur la dernière saison : coupon de 3 prévu à 87 %, observé à 85 % ; coupon de 5 prévu à 79 %, observé à 80 %.

**Réglage** (`python -m omniscore.tune`, validation 2023-24 et 2024-25 uniquement) : 18 combinaisons testées (décroissance temporelle, rétrécissement, a priori pour les promus, poids du mélange). Les écarts de RPS sont inférieurs à 0,0002 : avec les seuls résultats, le modèle est à son plafond. Les prochains gains viendront des cotes, des xG et des compositions.

**À retenir** : les sélections à 90 % et plus sont presque toutes « plus de 0,5 but » ou « moins de 4,5 buts », avec des cotes de 1,03 à 1,10. La marge du bookmaker annule le gain : pour être rentable, il faut les cotes réelles (value).

## Journal réel
`python -m omniscore.track` fige chaque prédiction avant le match (jamais réécrite) et la règle avec le résultat officiel. C'est la preuve en conditions réelles, distincte du backtest.

## Mise à jour automatique
`.github/workflows/omniscore-daily.yml` : tous les jours, tests → prédictions → journal réel → export vers le prototype, puis commit. Backtest et recalibration le lundi. Les workflows planifiés ne tournent que sur la branche par défaut du dépôt ; lancement manuel possible depuis l'onglet Actions. Secret optionnel : `ODDS_API_KEY`.

## Utilisation
```bash
pip install -r requirements.txt
python -m omniscore.cli backtest          # backtest + calibration (≈ 30 s)
python -m omniscore.cli predict           # prédictions des 30 prochains jours → data/predictions.json
python scripts/export_prototype.py        # injecte les vraies données dans prototype/omniscore.html
uvicorn omniscore.api:app --reload        # API : /v1/matches, /v1/matches/{id}, /v1/value-bets, /v1/coupons/generate, /v1/coupons/regenerate, /v1/backtest
python -m omniscore.tune                  # réglage des hyperparamètres
python -m omniscore.track                 # journal réel
python -m pytest -q                       # 21 tests
```
Cotes réelles : définir `ODDS_API_KEY` ([The Odds API](https://the-odds-api.com), offre gratuite). Les value bets et les mises Kelly apparaissent alors automatiquement.
