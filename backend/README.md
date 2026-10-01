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
python -m pytest -q                       # 33 tests
```
Cotes réelles : définir `ODDS_API_KEY` ([The Odds API](https://the-odds-api.com), offre gratuite). Les value bets et les mises Kelly apparaissent alors automatiquement.

# Module virtuel : FIFA / EA FC, tirs au but, Jeu 21

`omniscore/virtual/` couvre les 20 compétitions virtuelles (12 de football FC 24/25/26 dont 5x5, 4x4 et 3x3, 5 de tirs au but, 3 de Jeu 21). Il réutilise Dixon-Coles, la calibration isotonique et Kelly du moteur réel.

| Fichier | Rôle |
|---|---|
| `competitions.py` | Catalogue : type, buts attendus, lignes plus/moins, taille de la matrice de scores par format |
| `football.py` | Dixon-Coles par compétition ; 80+ marchés : 1X2, double chance, remboursé si nul, plus/moins, les deux marquent, pair/impair, buts par équipe, clean sheet, 1re équipe à marquer, handicaps asiatiques, écart, 1re MT, mi-temps/fin (convolution exacte), scores exacts |
| `penalty.py` | Séance de tirs au but en chaîne de Markov, résolue exactement : arrêt anticipé, mort subite, taux de réussite Beta-binomial par équipe |
| `blackjack.py` | Jeu 21 : loi exacte des totaux selon la composition du sabot, EV rester/tirer/doubler, course à 3 victoires (binomiale négative), vérification Monte-Carlo |
| `predictor.py` | Prédicteur unifié : calibration, classement par probabilité, pick principal, niveaux 🟢🟡🟠🔴, value et ¼ Kelly si des cotes sont fournies |
| `journal.py` | Picks figés avant l'événement → VALIDÉ ✅ / PERDU ❌ / REMBOURSÉ ↩️ ; stats par compétition, niveau et marché |
| `backtest.py` | Walk-forward, calibration apprise sur la 1re moitié et mesurée sur la 2de |
| `patterns.py` | Tests de régularité du générateur : séquences (Wald-Wolfowitz), Ljung-Box, khi-deux |
| `ingest.py` | Import CSV des résultats réels |
| `demo.py` | Données simulées pour tester sans fournisseur |

## Utilisation
```bash
python -m omniscore.virtual demo        # simulées : backtest + calibration + prédictions + journal (≈ 40 s)
python scripts/export_virtual.py        # → prototype/virtuel.html (Pronostics, Journal, Transparence, Calculette 21)
python -m omniscore.virtual csv mes_resultats.csv && python scripts/export_virtual.py --real
OMNISCORE_VIRTUAL_CSV=mes_resultats.csv uvicorn omniscore.api:app   # API /v1/virtual/...
```
API : `GET /v1/virtual/competitions`, `POST /v1/virtual/{code}/predict` (`{"home", "away", "odds": {clé: cote}}`), `GET /v1/virtual/{code}/patterns`, `POST /v1/virtual/21/decision` (`{"player": [10, 6], "dealer_up": 10, "decks": 1}`), `GET /v1/virtual/backtest`, `GET /v1/virtual/journal`.

Format CSV (une ligne par événement ; sans résultat = à venir) :
```
competition,datetime,home,away,hg,ag,hthg,htag,first          # football (first = H, A ou vide)
competition,datetime,home,away,kicks                          # penalty (kicks = 1101… dans l'ordre réel)
competition,datetime,player,dealer                            # Jeu 21 (cartes 10-6-5, As = 11)
```

## Résultats sur les données de démonstration (2 000 événements par compétition, 600 testés hors échantillon)
| Type | Pick principal annoncé → observé | 🟢 Très forte annoncé → observé |
|---|---|---|
| Football 5x5 / 4x4 / 3x3 | 93-94 % → 94-95 % | 88-90 % → 88-91 % |
| Football 11 contre 11 | 92-93 % → 89-93 % | 87-89 % → 86-89 % |
| Tirs au but | 84-88 % → 84-88 % | 85-87 % → 82-87 % |
| Jeu 21 | 74 % → 72-73 % | (aucune option au-dessus de 80 %) |

**À lire avant d'y croire** : ces données sont générées par un modèle de la même famille que le moteur, donc la calibration y est plus facile que sur un vrai jeu. Les picks à 90 % et plus sont surtout des « plus/moins » à cotes de 1,02 à 1,10 : la marge de l'opérateur (≈ 7 % dans la démo) efface le gain, et la value reste négative la plupart du temps. Au Jeu 21, quand le sabot est remélangé à chaque main, toutes les mains ont les mêmes probabilités avant la donne : seule la Calculette (pendant la main) apporte une décision utile. Seule la mesure sur vos résultats réels (journal + backtest sur CSV) dit ce que vaut le modèle.
