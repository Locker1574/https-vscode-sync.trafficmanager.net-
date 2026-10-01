# Prompt v2 (expert) : SaaS de prédictions football virtuel FIFA / EA FC et Jeu 21

Cette version va plus loin que `PROMPT_APP_PREDICTIONS_FIFA_JEU21.md` :
- **toutes les formules sont écrites en entier**, pour que l'IA ne puisse pas les inventer ni les simplifier ;
- **le travail est découpé en 7 prompts à envoyer l'un après l'autre**, chacun avec des critères de réussite vérifiables ;
- **un prototype fonctionnel existe déjà dans ce dépôt** (`backend/omniscore/virtual/` et `prototype/virtuel.html`, 33 tests). L'IA peut s'en servir comme référence : chaque formule ci-dessous y est implémentée et testée.

**Mode d'emploi** : envoie d'abord le **Prompt 0** (le cadre). Envoie ensuite les prompts 1 à 7 un par un. Ne passe au suivant que lorsque les critères de réussite du précédent sont remplis.

---

## Prompt 0 : cadre (à envoyer en premier)

```
Tu vas construire avec moi, étape par étape, « OMNISCORE Virtuel » : un SaaS de prédictions pour le football virtuel (FIFA / EA FC) et le Jeu 21. Tu es à la fois architecte logiciel, statisticien du sport, ingénieur ML et designer produit.

RÈGLES ABSOLUES
1. Chaque probabilité affichée est CALIBRÉE et VÉRIFIÉE : un « 80 % » doit se réaliser ≈ 80 % du temps sur des données jamais vues par le modèle. Jamais « 100 % sûr », jamais « gain garanti ».
2. Les jeux virtuels sont tirés au hasard par l'opérateur, qui garde une marge. Tu dois mesurer ce que le modèle vaut réellement (backtest + journal) et l'afficher tel quel.
3. Chaque compétition a son propre modèle et ses propres paramètres. Ne mélange jamais les ligues ni les formats.
4. Chaque prédiction est figée AVANT l'événement, puis réglée automatiquement : VALIDÉ ✅, PERDU ❌ ou REMBOURSÉ ↩️. Jamais réécrite.
5. Toutes les options de pari sont proposées, triées par probabilité décroissante. Le « pick principal » est l'option la plus probable dont la probabilité est ≤ 95 % (au-delà, la cote ≈ 1,0x n'a pas d'intérêt ; ces options restent visibles mais marquées comme telles).
6. Interface en français, mobile-first, mode sombre, section Jeu responsable (18+, limites, auto-exclusion, liens d'aide).
7. Tu écris des tests automatiques pour chaque formule. Tu ne passes à l'étape suivante que quand ils passent.

COMPÉTITIONS (20)
Football virtuel (12) — format, buts/match attendus à titre d'a priori, lignes plus/moins :
- FC 26. 5x5 Rush. Superligue — 5 contre 5, ≈ 7,5 buts, lignes 4,5 → 11,5, matrice de scores 18×18
- FC 24. 4x4. Championnat d'Angleterre — ≈ 6,5 buts, lignes 3,5 → 9,5, matrice 16×16
- FC 25. 3x3. Ligue de conférence — ≈ 5,5 buts, lignes 2,5 → 8,5, matrice 15×15
- FC 26. England Championship / FC 26. Champions League / FC 26. Championnat du monde / FC 25. Italy Championship / FC 25. Ligue européenne / FC 26. Germany Championship / FC 26. Italy Championship / FC 26. Spain Championship / UEFA Nations League. Simulation — 11 contre 11, ≈ 2,6 à 3,3 buts, lignes 0,5 → 5,5, matrice 12×12
Tirs au but (5) : FC24. Penalty, FC25. Penalty, FC26. Penalty, FIFA23. Penalty, Penalty
Jeu 21 (3) : 21 classics, 21 Dota. Jusqu'à 3 victoires (premier à 3 manches), Le 21

STACK : Next.js + TypeScript + Tailwind + shadcn/ui (front), FastAPI + numpy/scipy (moteur), PostgreSQL + TimescaleDB, Redis, Celery, Stripe, Docker.

Réponds seulement « Cadre compris » et un résumé de 10 lignes. Attends le prompt suivant.
```

---

## Prompt 1 : données et schéma

```
ÉTAPE 1 — Données.

Crée le schéma PostgreSQL (migrations) :
- competitions(code PK, name, kind ∈ {football, penalty, 21}, goals_prior, ou_lines numeric[], max_goals, rounds)
- teams(id, competition_code, name)
- events(id, competition_code, starts_at timestamptz, home_team_id, away_team_id, status ∈ {scheduled, live, finished})
- football_results(event_id PK, hg, ag, hthg, htag, first_scorer ∈ {H, A, NULL}, goal_minutes jsonb)
- shootout_results(event_id PK, kicks text)          -- '1101…' dans l'ordre réel des tirs, domicile d'abord
- card_results(event_id PK, player int[], dealer int[], round_no, series_score)   -- As = 11, figures = 10
- odds(event_id, market_key, bookmaker, odds, captured_at)   -- hypertable TimescaleDB
- predictions(id, event_id, market_key, label, p_raw, p_cal, tier, odds_at_freeze, frozen_at, model_version)
- settlements(prediction_id PK, status ∈ {V, P, R}, settled_at)
- users, subscriptions, alerts, audit_log

Ingestion :
- connecteur générique (URL et clé du fournisseur en variables d'environnement), import CSV, saisie admin ;
- format CSV : football competition,datetime,home,away,hg,ag,hthg,htag,first ; penalty competition,datetime,home,away,kicks ; 21 competition,datetime,player,dealer (cartes « 10-6-5 ») ;
- dédoublonnage par (competition, starts_at, home, away), rejet des lignes incohérentes (score MT > score final, séquence de tirs impossible, carte hors 2..11).
- générateur de données de démonstration réaliste (forces d'équipes cachées, tirages de Poisson, 2 000 événements par compétition), clairement marqué « simulé ».

CRITÈRES DE RÉUSSITE : migrations appliquées, 20 compétitions en base, import CSV de démo OK, tests de validation des lignes incohérentes.
```

---

## Prompt 2 : moteur football virtuel

```
ÉTAPE 2 — Moteur football. Implémente EXACTEMENT ces formules.

Modèle de Dixon-Coles par compétition :
  log λ_dom = μ + H + a_dom + d_ext        log λ_ext = μ + a_ext + d_dom
  P(X = x, Y = y) = τ(x, y) · Poisson(x; λ_dom) · Poisson(y; λ_ext)
  τ(0,0) = 1 − λ_dom·λ_ext·ρ ; τ(0,1) = 1 + λ_dom·ρ ; τ(1,0) = 1 + λ_ext·ρ ; τ(1,1) = 1 − ρ ; sinon 1
- Pondération temporelle w = exp(−ξ · jours écoulés) ; en virtuel ξ ≈ 0,05/jour (demi-vie ≈ 2 semaines), à régler par validation.
- Rétrécissement L2 (λ ≈ 4) des forces a et d vers 0.
- Ajustement par Newton-Raphson pondéré (IRLS) sur (μ, H, a, d), puis ρ par maximum de vraisemblance 1D sur [−0,25 ; 0,25].
- Matrice de scores de taille propre au format (12, 15, 16 ou 18), renormalisée à 1.

Mi-temps : part des buts de 1re MT s estimée par compétition. 1re MT ~ Poisson(λ·s), 2e MT ~ Poisson(λ·(1 − s)), indépendantes.
Mi-temps / fin de match : pour chaque résultat à la pause r, loi de l'écart final = (loi de l'écart en 1re MT restreinte à r) ⊛ (loi de l'écart en 2e MT) (convolution).
1re équipe à marquer : P(dom) = λ_dom / (λ_dom + λ_ext) · (1 − e^−(λ_dom+λ_ext)) ; P(aucun but) = e^−(λ_dom+λ_ext).

Marchés à dériver de la matrice M (i = buts dom, j = buts ext) :
1X2 (Σ i>j, i=j, i<j), double chance, remboursé si nul (p1 / (p1 + p2)), plus/moins sur toutes les lignes du format, les deux marquent (Σ i≥1, j≥1), pair/impair, buts par équipe (3 lignes autour de λ), clean sheet, 1re équipe à marquer, handicaps asiatiques en demi-lignes autour de round(λ_dom − λ_ext), écart exact (1, 2, 3+), 1re MT (1X2 et plus/moins), mi-temps/fin (9 issues), 8 scores exacts les plus probables.
Règlement automatique de chaque marché (fonction settle(key, résultat) → V / P / R / indéterminé).

CRITÈRES DE RÉUSSITE (tests) :
- 1X2 = 100 % ; les 9 issues mi-temps/fin = 100 % ; pair + impair = 100 % ; handicap dom + handicap ext complémentaire = 100 %.
- Sur données simulées 5x5, le total de buts attendu est du même ordre que la moyenne observée (et 2 à 3 fois celui du 11 contre 11).
- Règlement correct sur des cas écrits à la main (ex. 3-1 avec 0-1 à la pause : MT ext / fin dom = VALIDÉ, handicap dom −1,5 = VALIDÉ, −2,5 = PERDU).
```

---

## Prompt 3 : moteurs tirs au but et Jeu 21

```
ÉTAPE 3 — Penalty et Jeu 21.

TIRS AU BUT (chaîne de Markov exacte)
- Taux de réussite par équipe : p̂ = (a + réussis_pondérés) / (a + b + tentés_pondérés), a priori Beta(a = 7,5 ; b = 2,5), demi-vie 14 jours.
- 5 tirs chacun en alternance (domicile d'abord). Après le tir k, arrêt si buts_dom > buts_ext + tirs_restants_ext ou l'inverse.
- Égalité après 5 tirs chacun → mort subite par paires : la paire est décisive avec prob. p_d(1−p_e) + p_e(1−p_d).
- P(mort subite) = Σ_{k=0..5} C(5,k)² · p_d^k (1−p_d)^(5−k) · p_e^k (1−p_e)^(5−k).
- Programmation dynamique sur (tir, buts dom, buts ext) → loi exacte du score final (15 tours de mort subite modélisés).
Marchés : vainqueur, mort subite oui/non, total de tirs réussis plus/moins 5,5 → 8,5, tirs réussis par équipe, 6 scores exacts.
Test : la probabilité de mort subite et celle du vainqueur égalent une simulation Monte-Carlo de 40 000 séances à ±1 point.

JEU 21
- Composition du sabot : 4·N cartes de chaque valeur 2..9 et As, 16·N cartes valant 10 (N jeux), moins les cartes déjà vues.
- Loi exacte du total final d'une main qui tire jusqu'à un seuil (17 par défaut) : récurrence mémoïsée sur (total, nombre d'As comptés 11). L'As vaut 11 sauf s'il fait dépasser 21.
- Comparaison joueur / croupier : le joueur qui dépasse 21 perd, même si le croupier dépasse aussi ; égalité = remboursé.
- EV pendant la main : EV(rester) = P(gagne) − P(perd) ; EV(tirer) = Σ_c p_c · max(EV rester, EV tirer) de la nouvelle main ; EV(doubler) = 2 · Σ_c p_c · EV(rester après 1 carte). Conseil = action d'EV maximale.
- « Jusqu'à 3 victoires » : égalités rejouées, q = P(gagne) / (P(gagne) + P(perd)), P(3-k) = C(2+k, k) · q³ · (1−q)^k (binomiale négative).
Marchés : vainqueur de la manche, égalité, remboursé si égalité, dépasse 21 oui/non, 21 exact, totaux plus de 17,5 / 18,5 / 19,5, score du match et vainqueur (premier à 3).
Si le sabot est remélangé à chaque main, l'app l'écrit : toutes les mains ont alors les mêmes probabilités avant la donne, et seule l'aide à la décision pendant la main est utile.

CRITÈRES DE RÉUSSITE (tests) :
- 1 jeu, croupier tire jusqu'à 17 : P(croupier dépasse 21) = 28,2 % ± 0,2.
- Probabilités analytiques = Monte-Carlo (30 000 mains, retrait réel des cartes) à ±1,2 point.
- Conseils de référence : 10+6 contre 10 → tirer ; 5+6 contre 6 → doubler ; 10+8 contre 7 → rester.
- Course à 3 à 50/50 : P(3-0) = 12,5 %, somme des scores = 100 %.
```

---

## Prompt 4 : calibration, classement, valeur

```
ÉTAPE 4 — Calibration et classement.

Calibration isotonique (algorithme PAV) par type de jeu et par famille de marché (1X2, double chance, plus/moins, équipes, handicap, écart, mi-temps, mi-temps/fin, 1re équipe à marquer, pair/impair, vainqueur, mort subite, manche, match…), apprise seulement si la famille a ≥ 400 observations.
p_cal = 0,5 · p_brut + 0,5 · isotone(p_brut), bornée à [0,001 ; 0,999]. Les issues complémentaires (1X2, vainqueur, manche) sont renormalisées à 100 % après calibration.

Niveaux : 🟢 Très forte ≥ 80 % · 🟡 Forte 65-79 % · 🟠 Moyenne 50-64 % · 🔴 Faible < 50 %.

Pour chaque option, quand une cote o est connue :
- probabilité implicite = 1/o ; marge retirée par la méthode multiplicative et par la méthode de Shin :
  p_i = (√(z² + 4(1−z)·π_i²/B) − z) / (2(1−z)), avec π_i = 1/o_i, B = Σ π_i, z résolu tel que Σ p_i = 1 ;
- value = p_cal · o − 1 ;
- mise = ¼ Kelly = 0,25 · (p·o − 1)/(o − 1), plafonnée à 5 % de la bankroll, affichée seulement si value > 0.

Tri : toutes les options par p_cal décroissante. Pick principal = la plus probable avec p_cal ≤ 95 %.
Générateur de combinés : produit des probabilités (indépendance entre événements différents seulement, jamais deux options du même événement), affiché honnêtement.

CRITÈRES DE RÉUSSITE : options triées, pick principal correct, value et Kelly vérifiés sur un cas calculé à la main, 1X2 = 100 % après calibration.
```

---

## Prompt 5 : backtest, journal, tests du générateur

```
ÉTAPE 5 — Preuve.

Backtest walk-forward par compétition :
- les 40 % premiers événements forment l'historique initial ; le reste est découpé en blocs de 150-200 ;
- avant chaque bloc, réajustement sur tout ce qui précède, puis prédiction de chaque événement du bloc (aucune fuite du futur) ;
- calibration apprise sur la 1re moitié des prédictions, mesurée sur la 2de moitié ;
- rapport : Brier, log-loss, RPS (1X2), courbe annoncé/observé par tranche (0-50, 50-65, 65-80, 80-90, 90-95, 95-100 %), réussite par niveau et réussite du pick principal par compétition et par famille de marché ; comparaison avec un modèle de base qui suit les cotes du marché.

Journal réel : chaque pick principal est figé avant l'événement (avec sa cote), réglé dès que le résultat arrive, jamais modifié. Statistiques : réussite par compétition, par niveau, par marché, ROI à cote figée, série en cours.
Dérive : si la réussite observée d'un niveau passe sous l'annoncé de plus de 3 points sur les 300 derniers picks, ce niveau est rétrogradé et une alerte admin est créée.

Tests de régularité du générateur (« y a-t-il un motif exploitable ? ») sur chaque compétition :
- séquences de Wald-Wolfowitz : z = (R − μ)/σ, μ = 2n₁n₂/n + 1, σ² = 2n₁n₂(2n₁n₂ − n)/(n²(n − 1)), sur victoires à domicile, tirs réussis ;
- Ljung-Box (5 retards) : Q = n(n+2) Σ_k r_k²/(n − k), comparé à χ²(5), sur total de buts, tirs réussis par séance, total du joueur ;
- khi-deux d'ajustement des cartes à la composition du sabot.
Verdict affiché : « Aucun motif exploitable détecté » si toutes les p-valeurs > 0,01, sinon « Écart à surveiller (ce n'est pas une garantie de gain) ».

CRITÈRES DE RÉUSSITE : sur données de démo, écart annoncé/observé < 3 points pour chaque niveau ; le runs test détecte une suite alternée (p < 10⁻⁶) et accepte une suite aléatoire ; Ljung-Box détecte un AR(1) de coefficient 0,6.
```

---

## Prompt 6 : API et interface

```
ÉTAPE 6 — API et interface.

API FastAPI (documentée OpenAPI) :
GET /v1/virtual/competitions · POST /v1/virtual/{code}/predict {home, away, odds{clé: cote}} · GET /v1/virtual/{code}/upcoming
GET /v1/virtual/{code}/patterns · POST /v1/virtual/21/decision {player[], dealer_up, decks, seen[]}
GET /v1/virtual/backtest · GET /v1/virtual/journal · WebSocket /ws/live (nouveaux événements, règlements)

Interface (Next.js, mobile-first, mode sombre/clair) :
1. Pronostics : compétitions groupées (Football virtuel / Tirs au but / Jeu 21), carte par événement avec le PICK PRINCIPAL en grand (libellé, probabilité, niveau, cote juste, cote bookmaker, value), puis toutes les options triées avec barre de probabilité, cote, value, mise ¼ Kelly ; filtres (confiance min., marché, value positive) ; 12 options visibles puis « Voir les N options ».
2. Journal : compteurs VALIDÉ ✅ / PERDU ❌ / REMBOURSÉ ↩️, réussite annoncée contre observée par niveau, tableau par compétition.
3. Transparence (page publique) : backtest hors échantillon par compétition, courbe de calibration, verdict des tests du générateur.
4. Calculette 21 : boutons de cartes, nombre de jeux, cartes déjà sorties → conseil (rester / tirer / doubler), EV de chaque action, risque de dépasser 21, loi du total final du croupier.
5. Alertes (push, Telegram, e-mail) quand un pick 🟢 apparaît sur une compétition suivie.
6. Bandeau « Données simulées » tant que la source est la démo ; pied de page Jeu responsable.

CRITÈRES DE RÉUSSITE : aucune erreur console, pas de défilement horizontal à 390 px de large, tests de bout en bout (Playwright) sur les 4 onglets.
```

---

## Prompt 7 : SaaS, production, conformité

```
ÉTAPE 7 — SaaS et mise en production.
- Authentification e-mail + Google, rôles Admin / Abonné / Gratuit ; Stripe : Gratuit (3 pronostics/jour, pick principal seulement), Premium (tous les marchés, journal, alertes), VIP (API, export CSV, Calculette 21 avancée multi-jeux).
- Tâches planifiées : ingestion en continu, réglement des paris, réentraînement nocturne par compétition, backtest + recalibration hebdomadaires, contrôle de dérive.
- Panneau admin : sources de données, compétitions, paramètres des modèles (ξ, L2, a priori), versions de modèle, utilisateurs.
- Docker Compose (web, api, worker, postgres/timescale, redis), CI (lint + tests + build), logs structurés, monitoring.
- Conformité : RGPD (consentement, export et suppression des données), 18+, limites de dépôt/perte, auto-exclusion, liens d'aide, mentions « aucun gain garanti » ; vérifie la légalité selon le pays de diffusion.
- README d'installation, de déploiement et d'import des données réelles.

CRITÈRES DE RÉUSSITE : `docker compose up` démarre tout ; parcours inscription → abonnement test Stripe → pronostics → journal fonctionne ; CI verte.
```

---

## Ce que tu peux attendre (et ce que tu ne peux pas attendre)

- **Ce qu'on peut attendre** : des probabilités honnêtes et calibrées. Un pick « 🟢 88 % » se réalise environ 88 fois sur 100 sur des données jamais vues. C'est ce que mesure le prototype de ce dépôt sur ses données de démonstration (voir `backend/README.md`, section « Module virtuel »).
- **Ce qu'on ne peut pas attendre** : un gain garanti. Les options les plus sûres (90 % et plus) sont surtout des « plus/moins » avec des cotes de 1,02 à 1,10. La marge de l'opérateur efface généralement l'avantage. Le seul vrai juge, ce sont tes résultats réels : importe-les en CSV, et le journal et la page Transparence te diront ce que le modèle vaut vraiment.
