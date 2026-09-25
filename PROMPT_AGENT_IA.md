# Prompt pour l'agent IA : construire « OMNISCORE », une application SaaS d'analyse et de prédiction football

> **Mode d'emploi** : copiez tout ce qui se trouve sous la ligne « PROMPT » et collez-le dans votre agent IA (agent de développement autonome).
> Le texte d'origine a été corrigé, réorganisé et complété avec le modèle de données, l'architecture, les algorithmes et les critères d'acceptation.

---

## PROMPT

### 0. Rôle et mission

Tu es une équipe complète à toi seul : **architecte SaaS senior, data scientist spécialisé en modélisation sportive, ingénieur machine learning, ingénieur temps réel, designer UI/UX et analyste en intégrité sportive**.

Ta mission : **concevoir, coder et livrer une application SaaS d'analyse et de prédiction football de niveau professionnel**, la plus précise et la plus fiable possible, avec une interface moderne, responsive et fluide, et des données mises à jour en temps réel sans perte.

Nom de l'application : **OMNISCORE** (autres noms possibles : *PitchMind*, *Oraclix Football*, *XGenius*, *Predicta Elite*). Propose un logo, une identité visuelle et un slogan (ex. : « Les données voient le match avant vous »).

Tu peux ajouter toute technologie, logique ou analyse qui améliore le produit, **à l'intérieur du cadre défini à la section 24** (légalité, licences des données, honnêteté des probabilités, jeu responsable).

---

### 1. Sources de données (à intégrer sous licence ou via API officielles)

Utilise les meilleures sources disponibles, avec une couche d'abstraction (`DataProvider`) pour pouvoir en changer ou en combiner plusieurs :

| Besoin | Sources recommandées |
|---|---|
| Calendrier, résultats, compositions, événements en direct | API-Football, Sportmonks, Opta / Stats Perform, Sportradar, football-data.org |
| Statistiques avancées (xG, xA, PPDA, tracking) | Opta, StatsBomb (données ouvertes + payantes), Wyscout, FBref (via licence) |
| Cotes et mouvements de cotes (pré-match et live) | The Odds API, Betfair Exchange API, Pinnacle (référence « sharp »), OddsJam, agrégateurs sous licence |
| Contexte (blessures, suspensions, météo, arbitres, déplacements) | API des fournisseurs ci-dessus, API météo (OpenWeather), données arbitres |
| Classements, enjeux, primes | API des compétitions, règlements officiels (UEFA, FIFA, ligues nationales) |

Chaque donnée est horodatée, rattachée à sa source et versionnée. Aucune donnée inventée : si une donnée manque, l'interface l'indique.

---

### 2. Moteur de prédiction (le cœur de l'application)

#### 2.1 Modèles statistiques et ML (en ensemble)
1. **Poisson bivarié + correction Dixon-Coles** (scores exacts, 1X2, over/under, BTTS).
2. **Ratings Elo / Glicko-2** dynamiques par équipe (domicile/extérieur séparés).
3. **Modèle xG** (buts attendus) et **xGA**, avec pondération temporelle (décroissance exponentielle des matchs anciens).
4. **Gradient boosting** (XGBoost / LightGBM / CatBoost) entraîné sur des centaines de variables : forme, xG, possession, pressing (PPDA), absences, fatigue (jours de repos, voyages), météo, arbitre, historique des confrontations, cotes d'ouverture.
5. **Modèles bayésiens hiérarchiques** (PyMC / Stan) pour les forces attaque/défense et l'incertitude.
6. **Réseaux de neurones séquentiels** (LSTM / Transformer) pour le live (séquence des événements minute par minute).
7. **Modèles de comptage** (Poisson, binomiale négative) pour corners, cartons, fautes, tirs, hors-jeux, touches.
8. **Simulation Monte-Carlo** (≥ 10 000 simulations par match) pour dériver toutes les probabilités de marchés.
9. **Stacking / méta-modèle** combinant tous les modèles ci-dessus.

#### 2.2 Calibration et honnêteté des pourcentages
- Calibration obligatoire (**Platt scaling / régression isotonique**) : quand l'app affiche 80 %, l'événement doit se produire ~80 % du temps sur l'historique.
- Mesures publiées dans l'app : **Brier score, log-loss, ROI historique, courbe de calibration, taux de réussite par tranche de confiance**.
- Backtesting walk-forward sur plusieurs saisons ; aucun « data leakage ».

#### 2.3 Contexte et enjeux (« pourquoi les équipes s'affrontent »)
Pour chaque match, calcule un **indice d'enjeu** : titre, qualification européenne, maintien, derby/rivalité, match à élimination directe, prime financière (droits TV, primes UEFA, relégation = perte de revenus), rotation probable (match de coupe entre deux matchs importants), motivation d'un entraîneur menacé. Cet indice est une variable du modèle et est affiché dans la fiche match.

#### 2.4 Marchés prédits
1X2, double chance, draw no bet, handicap asiatique et européen, over/under (0.5 à 5.5), BTTS, score exact, mi-temps/fin de match, résultat 1re mi-temps, buteur, premier but, corners (total, par équipe, handicap), cartons, fautes, tirs, tirs cadrés, hors-jeux, touches, tacles, passes décisives, clean sheet, minute du premier but.

Chaque prédiction affiche : **probabilité modèle (%)**, **cote juste** (1/p), **meilleure cote du marché**, **value (%)**, **indice de confiance** et **explication** (top facteurs via SHAP).

#### 2.5 Value bets
- `value = probabilité_modèle × cote_bookmaker − 1`. Value bet si `value > seuil` (ex. 3 %) et si la confiance est suffisante.
- Comparaison avec la probabilité « sans marge » du marché (dé-vigging, méthode de Shin ou puissance) et avec Pinnacle comme référence.
- Mise conseillée : **critère de Kelly fractionné** (¼ Kelly), plafonnée.
- Suivi du **CLV (Closing Line Value)** pour mesurer la qualité réelle des prédictions.

---

### 3. Menus et fonctionnalités

#### 3.1 Tableau de bord (Accueil)
Matchs du jour, meilleures prédictions (tri par confiance décroissante : **la plus forte confiance est toujours affichée en premier**), value bets du jour, alertes intégrité, performance du modèle.

#### 3.2 Calendrier des matchs
Vue jour / semaine / mois, filtres (compétition, pays, heure, statut, niveau de confiance), fiche match détaillée.

#### 3.3 Recherche
Recherche globale instantanée (équipes, joueurs, compétitions, matchs, marchés), avec autocomplétion et filtres avancés.

#### 3.4 Favoris et suivi
Ajout d'équipes, compétitions, matchs et prédictions en favoris ; notifications (push, e-mail, Telegram) : début de match, but, prédiction validée/perdue, mouvement de cote important, alerte intégrité.

#### 3.5 Statut des prédictions
Chaque prédiction a un statut mis à jour automatiquement : **En attente → En cours → Validé ✅ / Perdu ❌ / Remboursé (push) ↩ / Annulé**.

#### 3.6 Menu « Coupon du jour »
- Coupons de **2, 3, 5, 8 et 10 sélections**.
- Seules les sélections avec une **probabilité calibrée entre 70 % et 98 %** sont éligibles.
- Affiche : probabilité de chaque sélection, **probabilité combinée réelle** (produit des probabilités, en tenant compte des corrélations), cote totale, value.
- Recherche et filtres à l'intérieur du menu.
- Indicateurs de tendance : mouvements de cotes, changements récents, forme.

> ⚠️ Règle mathématique à afficher clairement : la probabilité d'un combiné diminue avec le nombre de sélections (ex. 10 sélections à 90 % ≈ 35 % de réussite globale). L'app ne doit jamais présenter un combiné comme « sûr ».

#### 3.7 Bouton « Générer » / « Régénérer »
- **Générer** : sélectionne automatiquement les matchs et marchés ayant la plus forte probabilité (70-98 %) selon les critères choisis.
- **Régénérer** : propose une nouvelle sélection, avec la logique suivante :
  1. Calculer la nouvelle sélection.
  2. Pour chaque position du coupon, comparer la sélection actuelle avec la nouvelle.
  3. **Garder la sélection au pourcentage le plus élevé** ; si la nouvelle est plus faible, conserver l'ancienne ; si elle est supérieure, la remplacer.
  4. Si aucune nouvelle sélection n'est meilleure, réafficher le coupon actuel et l'indiquer (« Coupon déjà optimal »).
  5. Éviter les doublons et les sélections trop corrélées.
- Historique des générations conservé.

#### 3.8 Menu « Combo »
- Périmètre : matchs du jour / matchs à venir.
- **Réglette de 1 à 20** (nombre de matchs) + **sélecteur rapide 2, 3, 5, 8, 10**.
- **Curseur de confiance 70 % → 98 %**.
- Modes : **Rendement** (maximise la cote/value), **Sûreté** (maximise la probabilité), **Équilibré**.
- Option « cotes simples » (paris simples plutôt que combinés).

#### 3.9 Menu « Live » (en direct)
Sous-onglets : **Matchs en direct, Recherche, Prédictions live, À venir, Terminés, 1re mi-temps**.
- Mise à jour en temps réel (WebSocket, cible ≤ 1 s de latence d'affichage).
- Analyse de tout le match : momentum, pression offensive, xG live, tirs, corners, cartons, possession, changements, cartons rouges.
- Prédictions live recalculées à chaque événement : prochain but, total de buts, corners, cartons, résultat final, 1re mi-temps, avec pourcentage pour chaque option.
- **Auto-suivi** : chaque prédiction live passe automatiquement en **Validé / Perdu** dès que l'événement est tranché.
- Graphique de momentum et timeline des événements.

#### 3.10 Menu « Journal »
Historique complet et filtrable (jour, semaine, mois, saison, compétition, marché) : **Tous / En cours / Validés / Perdus / Push / Annulés**, avec tous les détails (cote prise, cote de clôture, probabilité, value, résultat, CLV). Statistiques : taux de réussite par tranche de confiance, ROI, profit/perte, séries. Export CSV/PDF.

#### 3.11 Menu « Intégrité » (détection d'anomalies de marché)
Objectif : **repérer les matchs présentant des signaux statistiques inhabituels**, comme le font les services d'intégrité professionnels (Sportradar UFDS, IBIA).
- Surveillance des **mouvements de cotes** anormaux (amplitude, vitesse, moment, divergence entre bookmakers et exchange, volumes Betfair).
- Détection d'**événements brusques** (cotes qui bougent sans information publique : blessure, composition…).
- Algorithmes : z-scores, **Isolation Forest**, détection de ruptures (CUSUM, Bayesian changepoint), comparaison cotes attendues vs observées, historique des équipes/arbitres/compétitions à risque.
- **Score de risque 0-100** avec code couleur : 🟢 normal, 🟡 à surveiller, 🟠 suspect, 🔴 très suspect.
- **Journal horodaté de chaque changement** avec degré d'importance, suivi continu des matchs signalés et alertes.
- Impact sur les prédictions : un match à risque élevé voit sa confiance réduite et est **exclu par défaut des coupons**.

> ⚖️ L'app présente des **signaux statistiques et un niveau de risque**, jamais une accusation : « anomalie de marché détectée », pas « match truqué ». Toute suspicion réelle se signale aux autorités compétentes (fédérations, ANJ/régulateurs, IBIA).

#### 3.12 Menu « Stats équipes »
Sous-menus : **Corners, Tirs, Tirs cadrés, Cartons, Fautes, Hors-jeux, Passes décisives, Tacles, Touches** (+ xG, xGA, possession, PPDA, duels, centres, arrêts du gardien).
- Moyennes pour/contre, domicile/extérieur, 5/10 derniers matchs, tendances, écart-type, classement.
- Prédiction des marchés correspondants pour chaque match à venir.
- Détection des valeurs aberrantes et lien vers le menu Intégrité si anomalie.
- Graphiques : tendances, radars, heatmaps, comparaison de deux équipes.
- Historique des changements horodaté avec niveau d'importance et code couleur.

#### 3.13 Menu « Value Bets »
Liste en temps réel des value bets de tous les marchés, triée par value et confiance, avec mise Kelly conseillée et suivi CLV.

#### 3.14 Compte et abonnement (SaaS)
Inscription/connexion (e-mail, Google, Apple), 2FA, profils, plans **Free / Pro / Elite** (Stripe), limites par plan, espace admin (utilisateurs, sources de données, santé des modèles, logs).

---

### 4. Architecture technique

- **Frontend** : Next.js (React, TypeScript), Tailwind CSS, shadcn/ui, Framer Motion, TanStack Query, Recharts/ECharts ; PWA installable ; mode sombre/clair ; multilingue (FR, EN, ES, PT, AR).
- **Mobile** : React Native (Expo) partageant la logique.
- **Backend API** : FastAPI (Python) pour le ML + Node.js (NestJS) ou FastAPI pour l'API métier ; GraphQL ou REST + **WebSocket** pour le temps réel.
- **Temps réel / streaming** : Redis Streams ou Apache Kafka ; workers d'ingestion ; recalcul des prédictions à chaque événement.
- **Bases de données** : PostgreSQL (données métier) + **TimescaleDB** (séries temporelles de cotes et événements live) + Redis (cache, pub/sub) + stockage objet (S3) pour les modèles.
- **ML Ops** : MLflow (suivi des modèles), réentraînement planifié (Airflow/Prefect), monitoring de la dérive.
- **Infra** : Docker, Kubernetes, CI/CD GitHub Actions, observabilité (Prometheus, Grafana, Sentry).
- **Aucune perte de données** : écritures idempotentes, files de messages persistantes, reprise après coupure, sauvegardes automatiques, reconnexion WebSocket avec rattrapage des événements manqués.

---

### 5. Modèle de données (tables principales)

```sql
-- Référentiel
countries(id, name, code)
competitions(id, country_id, name, type, season, level, prize_info_json)
seasons(id, competition_id, year_start, year_end)
teams(id, name, short_name, country_id, stadium_id, logo_url, elo_rating, founded)
players(id, team_id, name, position, birth_date, nationality, market_value, status)
stadiums(id, name, city, capacity, surface, altitude, lat, lon)
referees(id, name, country_id, avg_cards, avg_fouls, avg_penalties)
coaches(id, team_id, name, since, win_rate)

-- Matchs et événements
matches(id, competition_id, season_id, home_team_id, away_team_id, referee_id,
        stadium_id, kickoff_utc, status, round, home_score, away_score,
        ht_home_score, ht_away_score, stake_index, stake_context_json, weather_json)
lineups(id, match_id, team_id, player_id, is_starter, position, minutes_played)
injuries_suspensions(id, player_id, type, start_date, expected_return, source)
match_events(id, match_id, minute, second, type, team_id, player_id, detail_json, created_at)
match_stats(id, match_id, team_id, period, possession, shots, shots_on_target, xg,
            corners, fouls, yellow_cards, red_cards, offsides, tackles, throw_ins,
            assists, passes, pass_accuracy, ppda, saves, updated_at)
live_snapshots(time, match_id, minute, stats_json, momentum, xg_home, xg_away)  -- hypertable

-- Cotes et marchés
bookmakers(id, name, type, is_sharp)
markets(id, code, name, category)            -- 1X2, OU25, BTTS, CORNERS_OU95...
odds(time, match_id, bookmaker_id, market_id, selection, price, volume, is_live) -- hypertable
odds_movements(id, match_id, market_id, selection, from_price, to_price, pct_change,
               window_seconds, detected_at, severity)

-- Prédictions
models(id, name, version, type, trained_at, metrics_json, is_active)
predictions(id, match_id, market_id, selection, model_id, probability, fair_odds,
            best_odds, value_pct, confidence, is_live, minute, explanation_json,
            status, created_at, settled_at)
prediction_history(id, prediction_id, probability, odds, changed_at, reason)
value_bets(id, prediction_id, bookmaker_id, odds, value_pct, kelly_stake, clv, status)

-- Coupons et combos
coupons(id, user_id, type, size, min_confidence, mode, combined_probability,
        total_odds, status, generated_at, generation_round)
coupon_selections(id, coupon_id, prediction_id, position, locked, replaced_by)

-- Intégrité
integrity_alerts(id, match_id, risk_score, level, signals_json, status, created_at, updated_at)
integrity_signals(id, alert_id, type, market_id, description, severity, detected_at)
integrity_watchlist(id, match_id, reason, followed_since)

-- Utilisateurs / SaaS
users(id, email, password_hash, locale, timezone, plan_id, created_at)
plans(id, name, price, features_json, limits_json)
subscriptions(id, user_id, plan_id, stripe_id, status, renews_at)
favorites(id, user_id, entity_type, entity_id, created_at)
notifications(id, user_id, type, payload_json, read, created_at)
user_bet_journal(id, user_id, prediction_id, stake, odds_taken, result, profit)
audit_logs(id, actor, action, entity, entity_id, diff_json, created_at)

-- Modules avancés
predicted_lineups(id, match_id, team_id, player_id, start_probability, confirmed, updated_at)
player_match_features(id, match_id, player_id, expected_minutes, xg90, xa90, shots90, cards90)
confidence_scores(id, prediction_id, p_cal, agreement, completeness, market_agreement,
                  integrity_risk, volatility, ic, computed_at)
news_items(id, source, url, published_at, team_id, player_id, category, sentiment, summary)
bankrolls(id, user_id, initial_amount, current_amount, kelly_fraction, max_stake_pct)
alert_rules(id, user_id, name, conditions_json, channels_json, active)
assistant_conversations(id, user_id, messages_json, created_at)
model_performance(id, model_id, market_id, competition_id, period, brier, log_loss,
                  hit_rate, roi, clv_avg, calibration_json)
ws_event_log(seq, channel, payload_json, created_at)   -- rattrapage après reconnexion
```

---

### 6. Formules clés

- **Poisson** : `P(k buts) = λ^k · e^(−λ) / k!`, avec `λ_dom = attaque_dom × défense_ext × avantage_domicile`.
- **Dixon-Coles** : facteur de correction `τ(x, y, λ, μ, ρ)` pour les scores 0-0, 1-0, 0-1, 1-1.
- **Elo** : `R' = R + K × (S − E)`, `E = 1 / (1 + 10^((R_adv − R)/400))`.
- **Probabilité implicite sans marge** : `p_i = (1/cote_i) / Σ(1/cote_j)` (ou méthode de Shin).
- **Value** : `EV = p × cote − 1`.
- **Kelly** : `f* = (p × cote − 1) / (cote − 1)`, appliqué en fraction (¼).
- **Combiné** : `P = Π p_i` (ajusté des corrélations).
- **Brier** : `(1/N) Σ (p − o)²` ; **log-loss** : `−(1/N) Σ [o·ln p + (1−o)·ln(1−p)]`.
- **Anomalie de cote** : `z = (Δcote − μ_Δ) / σ_Δ` sur une fenêtre glissante.

---

### 7. Interface utilisateur

- Design moderne, sombre par défaut, style « terminal de trading » : cartes, badges de confiance colorés, jauges circulaires, graphiques animés.
- Code couleur de confiance : 🟢 ≥ 85 %, 🟡 70-84 %, 🟠 55-69 %, 🔴 < 55 %.
- Navigation : barre latérale (desktop) / barre inférieure (mobile).
- Accessibilité WCAG AA, responsive de 320 px au 4K, temps de chargement < 2 s.
- Mise à jour fluide sans rechargement de page (optimistic UI, skeletons, animations discrètes).

---

### 8. Temps réel et fiabilité

- Pré-match : rafraîchissement des cotes toutes les 30-60 s ; live : push à chaque événement (latence cible ≤ 1 s).
- Tout changement est enregistré (historique complet, jamais d'écrasement sans trace).
- Tolérance aux pannes : reprise automatique des flux, file d'attente persistante, bascule vers une source secondaire.

---

### 9. Sécurité et conformité

Authentification sécurisée (JWT + refresh, 2FA), chiffrement TLS, RGPD (consentement, export et suppression des données), limitation de débit, protection OWASP Top 10, secrets dans un coffre (Vault / variables d'environnement).

---

### 10. Livrables attendus

1. Code source complet (monorepo) avec README d'installation.
2. Schéma de base de données + migrations + données de démonstration.
3. Pipelines d'ingestion, d'entraînement et d'inférence.
4. API documentée (OpenAPI).
5. Interface web + PWA (+ app mobile en phase 2).
6. Tests (unitaires, intégration, E2E) et rapport de backtesting.
7. Docker Compose (local) + manifestes Kubernetes (production).

### 11. Plan de réalisation

1. **MVP** : ingestion calendrier + cotes, modèle Poisson/Elo, calendrier, fiche match, prédictions, recherche, favoris, journal.
2. **V2** : ML avancé + calibration, coupons, bouton Générer/Régénérer, combo, value bets.
3. **V3** : live temps réel, 1re mi-temps, auto-validation.
4. **V4** : intégrité, stats équipes avancées, abonnements, app mobile.

---

### 12. Indice de confiance OMNISCORE (formule détaillée)

La probabilité seule ne suffit pas : deux prédictions à 80 % ne se valent pas si l'une repose sur des données incomplètes. Calcule un **indice de confiance (IC) de 0 à 100** :

```
IC = 100 × p_cal^α × A^β × D^γ × M^δ × (1 − R)^ε × (1 − V)^ζ
```

| Facteur | Signification | Calcul |
|---|---|---|
| `p_cal` | Probabilité calibrée de l'ensemble de modèles | sortie du méta-modèle après calibration isotonique |
| `A` | Accord entre modèles | `1 − écart-type des probabilités des modèles / 0,5` |
| `D` | Complétude des données | part des variables clés disponibles (compos confirmées, xG, absences, arbitre…) |
| `M` | Accord avec le marché | `1 − |p_modèle − p_marché_sans_marge|`, avec Pinnacle comme référence |
| `R` | Risque intégrité | score du menu Intégrité ramené entre 0 et 1 |
| `V` | Volatilité | instabilité de la prédiction sur les dernières heures (live : dernières minutes) |

Les exposants `α…ζ` sont **appris par optimisation** (maximisation de la réussite par tranche d'IC en backtest) et non fixés à la main. Seules les sélections avec `p_cal ∈ [0,70 ; 0,98]` **et** `IC ≥ seuil utilisateur` entrent dans les coupons.

---

### 13. Algorithme « Générer / Régénérer » (pseudo-code)

```python
def generer(date_scope, taille, conf_min=0.70, conf_max=0.98, mode="surete"):
    candidats = [
        p for p in predictions(date_scope)
        if conf_min <= p.p_cal <= conf_max
        and p.integrity_level in ("vert", "jaune")
        and p.match.kickoff > now() + marge_minutes
    ]
    # une seule sélection par match (la meilleure selon le mode)
    meilleurs = best_per_match(candidats, key=score(mode))
    coupon = []
    for c in sorted(meilleurs, key=score(mode), reverse=True):
        if len(coupon) == taille: break
        if max_correlation(c, coupon) < 0.3:   # évite les sélections liées
            coupon.append(c)
    return Coupon(coupon, p_combinee=proba_jointe(coupon))  # via Monte-Carlo si corrélations

def regenerer(coupon_actuel, **params):
    nouveau = generer(**params, exclure=ids(coupon_actuel))
    final = []
    for ancien, neuf in zip_longest(coupon_actuel.sorted(), nouveau.sorted()):
        final.append(max(ancien, neuf, key=lambda s: (s.p_cal, s.ic)) if neuf else ancien)
    if final == coupon_actuel.selections:
        return coupon_actuel.with_message("Coupon déjà optimal")
    return Coupon(dedupe(final), p_combinee=proba_jointe(final))
```

Score selon le mode :
- **Sûreté** : `p_cal × IC`
- **Rendement** : `EV × IC` (EV = p × cote − 1)
- **Équilibré** : `√(p_cal) × (1 + EV) × IC`

Les sélections verrouillées par l'utilisateur (🔒) ne sont jamais remplacées. Chaque génération est enregistrée (`generation_round`) avec les sélections remplacées et la raison.

---

### 14. Moteur live avancé

- **Modèle d'intensité de but variable dans le temps** : `λ(t) = λ₀ × f(minute) × g(score) × h(cartons rouges) × k(momentum)`. Les buts sont plus fréquents en fin de mi-temps. Une équipe menée attaque davantage. Un carton rouge réduit fortement l'intensité de l'équipe réduite.
- **Mise à jour bayésienne** à chaque événement (but, carton, tir, corner, changement) de la force offensive et défensive estimée.
- **Indice de momentum** sur une fenêtre de 5 à 10 minutes : attaques dangereuses, tirs, xG, corners, possession dans le dernier tiers.
- **Probabilité du prochain but** et du prochain corner/carton, recalculées à chaque événement.
- **Modèle de minute du prochain événement** (analyse de survie : Cox / Weibull).
- **Détection d'écart live** : la cote live s'écarte fortement du modèle sans événement visible → signal envoyé au menu Intégrité.
- **Suspension automatique** de l'affichage des prédictions pendant les phases de VAR, de penalty ou de coupure du flux, pour éviter des pourcentages faux.

---

### 15. Analyse de marché avancée (mouvements de cotes)

- **Steam move** : mouvement rapide et simultané chez plusieurs bookmakers.
- **Reverse line movement** : la cote bouge à l'inverse de la majorité des paris publics.
- **Écart d'ouverture à clôture** et **CLV** par marché, compétition et bookmaker.
- **Écart sharp/soft** : différence entre Pinnacle/Betfair et les bookmakers grand public.
- **Liquidité** : volumes appariés sur l'exchange et profondeur du carnet.
- **Efficience par ligue** : identifier les championnats où le modèle bat le plus le marché.
- Chaque mouvement est classé par importance (**faible / moyen / fort / critique**), coloré et historisé.

---

### 16. Modules supplémentaires

1. **Assistant IA conversationnel** : l'utilisateur pose ses questions (« Pourquoi 78 % sur Over 2.5 ? », « Compare Arsenal et Liverpool sur les corners »). L'assistant répond à partir des données de l'app, cite les chiffres et n'invente rien.
2. **Gestionnaire de bankroll** : capital, mises Kelly fractionnées, plafonds, courbe de profit, drawdown et alertes de perte.
3. **Compositions probables** : prédiction des onze de départ (historique de rotation, calendrier, blessures) avant l'annonce officielle, puis recalcul automatique à l'annonce.
4. **Module arbitres** : moyennes de cartons, fautes et penalties par arbitre, tendance domicile/extérieur, impact sur les marchés cartons.
5. **Props joueurs** : buteur, tirs, tirs cadrés, passes décisives, cartons par joueur (modèles par minute jouée).
6. **Contexte physique** : fatigue (minutes cumulées, jours de repos), distance parcourue, décalage horaire, altitude, météo, état de la pelouse.
7. **Effet entraîneur et mercato** : ajustement des ratings après un changement d'entraîneur ou un transfert majeur.
8. **Analyse de l'actualité (NLP)** : analyse des sources d'information sous licence (communiqués officiels, conférences de presse) pour détecter blessures, tensions et rotations.
9. **Simulateur « et si »** : l'utilisateur modifie un paramètre (absence du buteur, carton rouge à la 30ᵉ minute) et voit les probabilités évoluer.
10. **Comparateur d'équipes** : radars, confrontations directes, styles de jeu (pressing, jeu direct, possession).
11. **Constructeur d'alertes** : règles personnalisées, par ex. « préviens-moi si une value > 5 % apparaît en Ligue 1 avec IC ≥ 80 ».
12. **Tableau de transparence** : performances réelles publiques du modèle (réussite, ROI, calibration) par marché et par ligue.
13. **API B2B** : accès payant aux prédictions et signaux pour médias et partenaires.

---

### 17. Variables du modèle (feature store)

Toutes les variables sont versionnées et calculées **uniquement avec les données connues avant le coup d'envoi**, pour éviter le « data leakage ».

- **Forme** : points, buts et xG sur 3/5/10 matchs (pondérés dans le temps), séparés domicile/extérieur.
- **Force** : Elo, Glicko, ratings bayésiens attaque/défense, valeur marchande de l'effectif aligné.
- **Style** : possession, PPDA, passes progressives, centres, jeu aérien, pressing haut.
- **Effectif** : absences pondérées par l'importance du joueur (minutes et contribution xG/xA), gardien titulaire.
- **Calendrier** : jours de repos, match européen avant/après, distance de déplacement.
- **Enjeu** : écart au titre, à l'Europe, à la relégation, derby, match retour (score de l'aller).
- **Arbitre et conditions** : profil de l'arbitre, météo, pelouse, affluence.
- **Marché** : cotes d'ouverture, cotes actuelles sans marge, mouvements, volumes.

---

### 18. API et événements temps réel

**REST (extraits)**
```
GET  /v1/matches?date=&competition=&status=
GET  /v1/matches/{id}                 # fiche complète + enjeux
GET  /v1/matches/{id}/predictions     # tous les marchés, triés par IC
GET  /v1/value-bets?min_value=&min_ic=
POST /v1/coupons/generate             # {size, conf_min, conf_max, mode, scope}
POST /v1/coupons/{id}/regenerate
GET  /v1/combo?count=1..20&conf_min=&mode=
GET  /v1/journal?period=&status=&market=
GET  /v1/integrity/alerts?level=
GET  /v1/teams/{id}/stats?metric=corners|shots|cards|...
POST /v1/favorites   DELETE /v1/favorites/{id}
POST /v1/assistant/ask
```

**WebSocket** (`wss://…/live`, abonnement par match ou par canal)
```
match.event        { match_id, minute, type, team, player }
match.stats        { match_id, stats, xg, momentum }
prediction.update  { prediction_id, p_cal, ic, fair_odds, value }
prediction.settled { prediction_id, status: VALIDE|PERDU|PUSH|ANNULE }
odds.move          { match_id, market, from, to, pct, severity }
integrity.alert    { match_id, risk_score, level, signals[] }
```
Chaque message porte un **numéro de séquence**. À la reconnexion, le client demande les messages manqués depuis le dernier numéro reçu (aucune perte).

---

### 19. Indicateurs de qualité (KPI et SLO)

| Domaine | Objectif |
|---|---|
| Calibration | écart moyen entre probabilité prévue et fréquence observée < 3 points par tranche de 10 % |
| Précision | Brier et log-loss meilleurs que les probabilités du marché sans marge (hors Pinnacle) |
| Value | CLV moyen positif sur 1 000+ value bets |
| Temps réel | latence événement → écran ≤ 1 s (p95) ; cotes pré-match ≤ 60 s |
| Disponibilité | 99,9 % |
| Données | 0 événement perdu ; réconciliation automatique avec le résultat officiel |
| Interface | Lighthouse ≥ 90, premier affichage < 2 s en 4G |

Un **rapport de performance automatique** est publié chaque semaine dans l'app (tableau de transparence).

---

### 20. Modèle économique

| Plan | Prix indicatif | Contenu |
|---|---|---|
| **Free** | 0 € | 3 prédictions/jour, calendrier, stats de base |
| **Pro** | 19-29 €/mois | toutes les prédictions, coupons, combo, journal, favoris, alertes |
| **Elite** | 59-99 €/mois | live avancé, intégrité, value bets en temps réel, assistant IA, simulateur, bankroll |
| **B2B / API** | sur devis | flux de prédictions et de signaux pour médias et partenaires |

Essai gratuit de 7 jours, paiement annuel avec réduction, parrainage. L'abonnement donne accès à des analyses : aucun gain n'est promis.

---

### 21. Critères d'acceptation (exemples à tester)

- **Coupon** : un coupon de 5 ne contient que des sélections entre 70 et 98 %, une seule par match, aucune sur un match 🟠/🔴 en intégrité, et affiche la probabilité combinée.
- **Régénérer** : si toutes les nouvelles sélections sont plus faibles, le coupon reste identique et le message « Coupon déjà optimal » apparaît.
- **Live** : un but est affiché et les prédictions recalculées en moins d'1 s. Une prédiction « Over 1.5 » passe en **Validé** dès le 2ᵉ but.
- **Journal** : les compteurs Tous / En cours / Validés / Perdus / Push correspondent exactement au détail des lignes.
- **Intégrité** : un mouvement de cote simulé de −25 % en 10 minutes sans information publique déclenche une alerte 🟠 horodatée.
- **Reconnexion** : après une coupure réseau de 30 s, le client récupère tous les événements manqués sans doublon.

---

### 22. Équipe virtuelle et méthode de travail

Travaille comme une équipe organisée :
1. **Product owner** : découpe en user stories avec critères d'acceptation.
2. **Data engineer** : ingestion, nettoyage, réconciliation des sources.
3. **Data scientist** : modèles, backtests, calibration, rapport de performance.
4. **Backend / temps réel** : API, WebSocket, files de messages.
5. **Frontend / UX** : maquettes, design system, composants, accessibilité.
6. **QA / SRE** : tests, monitoring, sécurité, déploiements.

À chaque étape, livre du code fonctionnel, les tests et un court compte rendu (fait, mesuré, prochaine étape).

---

### 23. Pistes d'innovation (phase 5)

- **Données de tracking** (positions des joueurs) pour les modèles de contrôle de l'espace (pitch control) et de probabilité de but par action (VAEP, xT).
- **Vision par ordinateur** sur les flux vidéo autorisés, pour détecter pressing et formations.
- **Modèles de graphes** (GNN) sur les réseaux de passes.
- **Apprentissage en ligne** : les modèles s'ajustent en continu pendant la saison.
- **Explications en langage naturel** générées automatiquement pour chaque prédiction.
- **Widgets et extensions** : widget mobile, bot Telegram/Discord, montre connectée.

---

### 24. Cadre obligatoire (non négociable)

1. **Données** : uniquement des sources légales, sous licence ou API officielles, en respectant leurs conditions d'utilisation. Aucune donnée inventée présentée comme réelle.
2. **Honnêteté des probabilités** : aucun pronostic n'est garanti. Les pourcentages affichés sont des probabilités calibrées et vérifiables, accompagnées des performances historiques réelles du modèle. Jamais de « 100 % sûr ».
3. **Intégrité** : signaux et scores de risque, pas d'accusation nominative ; possibilité de signalement aux autorités.
4. **Jeu responsable** : vérification d'âge (18+), limites de dépôt/mise conseillées, messages de prévention, liens vers les services d'aide, respect de la réglementation de chaque pays.
5. **Qualité** : chaque fonctionnalité est testée, documentée et mesurée avant d'être livrée.

Commence par me présenter l'architecture détaillée, le schéma de données final et le plan du MVP (user stories + critères d'acceptation). Ensuite, code étape par étape : à chaque étape, montre l'avancement, les tests passés et les métriques du modèle.
