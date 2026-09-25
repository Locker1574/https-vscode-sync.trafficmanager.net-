# Prompt pour l'agent IA : construire « OMNISCORE », une application SaaS d'analyse et de prédiction football

> **Mode d'emploi** : copiez tout ce qui se trouve sous la ligne « PROMPT » et collez-le dans votre agent IA (agent de développement autonome).
> Le texte d'origine a été corrigé, réorganisé et complété avec le modèle de données, l'architecture, les algorithmes et les critères d'acceptation.
>
> **Version 3** : coupons de 1 à 10 sélections, curseur de confiance de 1 à 100 %, Combo avec sélecteur de 1 à 10, « Régénérer » qui affiche aussi la nouvelle proposition, menu Stats équipes enrichi, règle « temps réel sans perte » dans chaque menu, schéma de données complété, point de départ existant (section 25).

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
- Les probabilités affichées sont **bornées entre 1 % et 99 %** : aucun événement de football n'est certain.
- Mesures publiées dans l'app : **Brier score, log-loss, RPS, ROI historique, courbe de calibration, taux de réussite par tranche de confiance**.
- Backtesting walk-forward sur plusieurs saisons ; aucun « data leakage ».

#### 2.3 Contexte et enjeux (« pourquoi les équipes s'affrontent »)
Pour chaque match, calcule un **indice d'enjeu** : titre, qualification européenne, maintien, derby/rivalité, match à élimination directe, prime financière (droits TV, primes UEFA, relégation = perte de revenus), rotation probable (match de coupe entre deux matchs importants), motivation d'un entraîneur menacé. Cet indice est une variable du modèle et est affiché dans la fiche match, avec **ce qui est en jeu et pour quel prix** (montants issus de la table `competition_prizes`).

#### 2.4 Marchés prédits
1X2, double chance, draw no bet, handicap asiatique et européen, over/under (0.5 à 5.5), BTTS, score exact, mi-temps/fin de match, résultat 1re mi-temps, buteur, premier but, corners (total, par équipe, handicap), cartons, fautes, tirs, tirs cadrés, hors-jeux, touches, tacles, passes décisives, clean sheet, minute du premier but.

Chaque prédiction affiche : **probabilité modèle (%)**, **cote juste** (1/p), **meilleure cote du marché**, **value (%)**, **indice de confiance** et **explication** (top facteurs via SHAP). Pour chaque match, les options sont **triées par confiance décroissante : la plus forte confiance est toujours en premier**.

#### 2.5 Value bets
- `value = probabilité_modèle × cote_bookmaker − 1`. Value bet si `value > seuil` (ex. 3 %) et si la confiance est suffisante.
- La value est calculée **pour chaque prédiction de chaque menu** (coupons, combo, live, stats équipes) et signalée par un badge « Value ».
- Comparaison avec la probabilité « sans marge » du marché (dé-vigging, méthode de Shin ou puissance) et avec Pinnacle comme référence.
- Mise conseillée : **critère de Kelly fractionné** (¼ Kelly), plafonnée.
- Suivi du **CLV (Closing Line Value)** pour mesurer la qualité réelle des prédictions.

---

### 3. Menus et fonctionnalités

#### 3.0 Règles communes à tous les menus
- **Temps réel sans perte** : toutes les données sont dynamiques et fluides. Elles se mettent à jour en continu, sans rechargement de page et sans perte : push WebSocket, live chaque seconde, cotes pré-match toutes les 30-60 s. Chaque changement est historisé. Après une coupure, les événements manqués sont récupérés. Chaque écran affiche l'heure de la dernière mise à jour et la source.
- **Curseur de confiance de 1 % à 100 %** (coupons, Générer/Régénérer, Combo, recherche) : double curseur minimum/maximum, réglé par défaut sur 70-98 %. Il filtre la probabilité calibrée. Un second réglage, optionnel, filtre l'indice de confiance IC (0-100, section 12).
- **Règle des 100 %** : la probabilité affichée ne dépasse jamais 99 %. Si l'utilisateur règle le minimum à 100 %, l'app affiche « Aucune prédiction n'atteint 100 % : le football n'est jamais certain » et propose les sélections les plus proches.
- **Code couleur des statuts et de l'importance**, identique partout (section 7).

#### 3.1 Tableau de bord (Accueil)
Matchs du jour, meilleures prédictions (tri par confiance décroissante), value bets du jour, alertes intégrité, performance du modèle.

#### 3.2 Calendrier des matchs
Vue jour / semaine / mois, filtres (compétition, pays, heure, statut, niveau de confiance), fiche match détaillée (prédictions sur tous les marchés, enjeux, compositions, cotes et leur évolution).

#### 3.3 Recherche
Recherche globale instantanée (équipes, joueurs, compétitions, matchs, marchés), avec autocomplétion et filtres avancés (dont le curseur de confiance).

#### 3.4 Favoris et suivi
Ajout d'équipes, compétitions, matchs et prédictions en favoris ; notifications (push, e-mail, Telegram) : début de match, but, prédiction validée/perdue, mouvement de cote important, alerte intégrité.

#### 3.5 Statut des prédictions
Chaque prédiction a un statut mis à jour automatiquement : **En attente → En cours → Validé ✅ / Perdu ❌ / Remboursé (push) ↩ / Annulé**.

#### 3.6 Menu « Coupon du jour »
- Tailles : **1, 2, 3, 4, 5, 6, 7, 8, 9 et 10 sélections** (une rangée de boutons). Le coupon de 1 est le meilleur pari simple du jour.
- **Curseur de confiance 1-100 %** (section 3.0).
- Chaque sélection affiche : probabilité, IC, cote, value, tendance de la cote (↑ ↓ →), alerte intégrité éventuelle, statut en direct.
- Le coupon affiche la **probabilité combinée réelle** (produit des probabilités, en tenant compte des corrélations), la cote totale, la value et son statut (en attente, en cours, validé, perdu).
- **Recherche et filtres à l'intérieur du menu** (équipe, compétition, marché, heure, confiance).
- Indicateurs de tendance : mouvements de cotes, changements récents, forme.

> ⚠️ Règle mathématique à afficher clairement : la probabilité d'un combiné diminue avec le nombre de sélections (ex. 10 sélections à 90 % ≈ 35 % de réussite globale). L'app ne doit jamais présenter un combiné comme « sûr ».

#### 3.7 Bouton « Générer » / « Régénérer »
- **Générer** : sélectionne automatiquement les matchs et marchés ayant la plus forte probabilité dans la plage choisie (1-100 %), une sélection par match, en analysant tous les marchés de chaque match.
- **Régénérer** : calcule une nouvelle proposition (sans reprendre les sélections actuelles), puis compare position par position et **garde toujours la sélection au pourcentage le plus élevé** :

  | Situation | Affichage |
  |---|---|
  | Les sélections actuelles sont toutes meilleures | Le coupon actuel est affiché tel quel avec « Coupon déjà optimal ». La nouvelle proposition, plus faible, est montrée en dessous, grisée, pour comparaison. |
  | Certaines nouvelles sélections sont meilleures | Elles remplacent les plus faibles, marquées « Nouveau ». Le coupon mélange donc les meilleures anciennes et les meilleures nouvelles. |
  | Toutes les nouvelles sélections sont meilleures | Le nouveau coupon est affiché. |

- Aucun doublon de match et pas de sélections trop corrélées.
- Les sélections verrouillées par l'utilisateur (🔒) ne sont jamais remplacées.
- L'historique des générations est conservé (table `coupon_generations`).

#### 3.8 Menu « Combo »
- Périmètre : **matchs du jour** ou **matchs à venir**.
- **Réglette de 1 à 20** (nombre de matchs) et **sélecteur rapide 1, 2, 3, 4, 5, 6, 7, 8, 9 et 10**, synchronisés (choisir 7 place la réglette sur 7).
- **Curseur de confiance 1-100 %**.
- Modes : **Rendement** (maximise la cote/value), **Sûreté** (maximise la probabilité), **Équilibré**.
- Option **« cotes simples »** : chaque sélection est proposée en pari simple, avec sa mise Kelly, au lieu d'un combiné.
- Pour chaque match, l'option retenue est la meilleure parmi **tous les marchés** analysés.

#### 3.9 Menu « Live » (en direct)
Sous-onglets : **Matchs en direct, Recherche, Prédictions live, À venir, Terminés, 1re mi-temps**.
- Mise à jour **chaque seconde** (WebSocket, latence d'affichage ≤ 1 s).
- Analyse de tout le match : momentum, pression offensive, xG live, tirs, corners, cartons, possession, remplacements, cartons rouges.
- Prédictions live recalculées à chaque événement : prochain but, total de buts, corners, cartons, résultat final, 1re mi-temps, avec le pourcentage de chaque option.
- **Auto-suivi** : chaque prédiction live passe automatiquement en **Validé / Perdu** dès que l'événement est tranché.
- **Sous-menu 1re mi-temps** : statistiques et prédictions propres à la 1re période (résultat MT, buts MT, corners MT, cartons MT), réglées automatiquement à la pause.
- Graphique de momentum et timeline des événements.

#### 3.10 Menu « Journal »
Historique complet et filtrable (jour, semaine, mois, saison, compétition, marché) : **Tous / En cours / Validés / Perdus / Push / Annulés**, avec tous les détails (cote prise, cote de clôture, probabilité, value, résultat, CLV). Statistiques : taux de réussite par tranche de confiance, ROI, profit/perte, séries. Export CSV/PDF.

#### 3.11 Menu « Intégrité » (détection d'anomalies de marché)
Objectif : **repérer les matchs présentant des signaux statistiques inhabituels**, comme le font les services d'intégrité professionnels (Sportradar UFDS, IBIA).
- Surveillance des **mouvements de cotes** anormaux (amplitude, vitesse, moment, divergence entre bookmakers et exchange, volumes Betfair).
- Détection d'**événements brusques** (cotes qui bougent sans information publique : blessure, composition…).
- Algorithmes : z-scores, **Isolation Forest**, détection de ruptures (CUSUM, Bayesian changepoint), comparaison cotes attendues vs observées, historique des équipes/arbitres/compétitions à risque.
- **Score de risque 0-100** avec code couleur : 🟢 normal, 🟡 à surveiller, 🟠 suspect, 🔴 très suspect.
- **Journal horodaté de chaque changement** avec degré d'importance, suivi continu des matchs signalés (avant, pendant et après le match) et alertes.
- Pour chaque match signalé : les **marchés les plus exposés** (ceux dont la cote bouge anormalement), avec la probabilité du modèle comparée à la probabilité implicite du marché, avant et pendant le match.
- Impact sur les prédictions : un match à risque élevé voit sa confiance réduite et est **exclu par défaut des coupons**.

> ⚖️ L'app présente des **signaux statistiques et un niveau de risque**, jamais une accusation : « anomalie de marché détectée », pas « match truqué ». Toute suspicion réelle se signale aux autorités compétentes (fédérations, ANJ/régulateurs, IBIA).

#### 3.12 Menu « Stats équipes »
Sous-menus : **Corners, Tirs, Tirs cadrés, Cartons, Fautes, Hors-jeux, Passes décisives, Tacles, Touches** (+ xG, xGA, possession, PPDA, duels, centres, arrêts du gardien).
- Moyennes pour/contre, domicile/extérieur, 5/10 derniers matchs, tendances, écart-type, classement.
- Pour chaque statistique : **matchs concernés**, **mouvements et changements de cotes** des marchés associés (ex. corners, cartons), **tendances**, **signaux** et **circonstances** (arbitre, météo, enjeu, absences, score, carton rouge).
- Prédiction des marchés correspondants pour chaque match à venir, avec probabilité, IC et value.
- Détection des valeurs aberrantes : une anomalie crée une alerte, montre les matchs et les cotes concernés et renvoie au menu Intégrité.
- Graphiques : tendances, radars, heatmaps, comparaison de deux équipes.
- Historique horodaté de chaque changement, avec niveau d'importance et code couleur (table `change_log`).

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
competitions(id, country_id, name, type, level)
seasons(id, competition_id, year_start, year_end)
competition_prizes(id, competition_id, season_id, stage, amount, currency,
                   description, source)          -- primes, droits TV, coût d'une relégation
standings(id, competition_id, season_id, team_id, position, points, played,
          goal_diff, form, updated_at)            -- sert à l'indice d'enjeu
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
team_stat_aggregates(id, team_id, season_id, metric, scope,   -- scope : home|away|all
                     window, avg_for, avg_against, std, trend, updated_at)  -- window : 5|10|season

-- Cotes et marchés
bookmakers(id, name, type, is_sharp)
markets(id, code, name, category)            -- 1X2, OU25, BTTS, CORNERS_OU95...
odds(time, match_id, bookmaker_id, market_id, selection, price, volume, is_live) -- hypertable
odds_movements(id, match_id, market_id, selection, from_price, to_price, pct_change,
               window_seconds, detected_at, severity)

-- Prédictions
models(id, name, version, type, trained_at, metrics_json, is_active)
predictions(id, match_id, market_id, selection, model_id, probability, fair_odds,
            best_odds, value_pct, confidence, is_live, minute, period, explanation_json,
            status, created_at, settled_at)
  -- CHECK (probability BETWEEN 0.01 AND 0.99)
  -- status : EN_ATTENTE | EN_COURS | VALIDE | PERDU | PUSH | ANNULE
prediction_history(id, prediction_id, probability, odds, changed_at, reason)
value_bets(id, prediction_id, bookmaker_id, odds, value_pct, kelly_stake, clv, status)

-- Coupons et combos
coupons(id, user_id, type, size, conf_min, conf_max, ic_min, mode, scope, singles,
        combined_probability, total_odds, status, generated_at, generation_round)
  -- type : coupon | combo ; mode : surete | equilibre | rendement ; scope : jour | avenir
  -- CHECK ((type = 'coupon' AND size BETWEEN 1 AND 10) OR (type = 'combo' AND size BETWEEN 1 AND 20))
  -- CHECK (conf_min BETWEEN 1 AND 100 AND conf_max BETWEEN 1 AND 100 AND conf_min <= conf_max)
coupon_selections(id, coupon_id, prediction_id, position, locked, is_new, replaced_by)
coupon_generations(id, coupon_id, round, proposed_json, kept_json, replaced_json,
                   message, created_at)          -- historique Générer / Régénérer + alternative

-- Intégrité et journal des changements
integrity_alerts(id, match_id, risk_score, level, signals_json, status, created_at, updated_at)
integrity_signals(id, alert_id, type, market_id, description, severity, detected_at)
integrity_watchlist(id, match_id, reason, followed_since)
change_log(id, entity_type, entity_id, field, old_value, new_value,
           importance, color, source_id, detected_at)
  -- importance : faible | moyen | fort | critique ; color : vert | jaune | orange | rouge
  -- utilisé par Intégrité, Stats équipes, cotes et prédictions

-- Sources et ingestion (zéro perte)
data_sources(id, name, type, licence, priority, status, last_success_at)
ingestion_runs(id, source_id, entity, started_at, finished_at, records_in, records_ok,
               records_rejected, last_sequence, status)
ws_event_log(seq, channel, payload_json, created_at)   -- rattrapage après reconnexion

-- Utilisateurs / SaaS
users(id, email, password_hash, locale, timezone, plan_id, birth_date, created_at)
plans(id, name, price, features_json, limits_json)
subscriptions(id, user_id, plan_id, stripe_id, status, renews_at)
favorites(id, user_id, entity_type, entity_id, created_at)
notifications(id, user_id, type, payload_json, read, created_at)
user_bet_journal(id, user_id, prediction_id, coupon_id, stake, odds_taken, result, profit)
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
model_performance(id, model_id, market_id, competition_id, period, brier, log_loss, rps,
                  hit_rate, roi, clv_avg, calibration_json)
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
- **Brier** : `(1/N) Σ (p − o)²` ; **log-loss** : `−(1/N) Σ [o·ln p + (1−o)·ln(1−p)]` ; **RPS** pour les issues ordonnées (1X2).
- **Anomalie de cote** : `z = (Δcote − μ_Δ) / σ_Δ` sur une fenêtre glissante.

---

### 7. Interface utilisateur

- Design moderne et original, sombre par défaut, style « terminal de trading » : cartes, badges de confiance colorés, jauges circulaires, graphiques animés. Simple à prendre en main dès la première visite.
- Code couleur de confiance : 🟢 ≥ 85 %, 🟡 70-84 %, 🟠 55-69 %, 🔴 < 55 %.
- Code couleur d'importance (intégrité, changements, stats) : 🟢 faible, 🟡 moyen, 🟠 fort, 🔴 critique.
- Navigation : barre latérale (desktop) / barre inférieure (mobile).
- Accessibilité WCAG AA, responsive de 320 px au 4K, temps de chargement < 2 s.
- Mise à jour fluide sans rechargement de page (optimistic UI, skeletons, animations discrètes).

---

### 8. Temps réel et fiabilité

- Pré-match : rafraîchissement des cotes toutes les 30-60 s ; live : push à chaque événement et horloge/statistiques rafraîchies chaque seconde (latence cible ≤ 1 s).
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
2. **V2** : ML avancé + calibration, coupons 1-10, bouton Générer/Régénérer, combo, value bets.
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
| `p_cal` | Probabilité calibrée de l'ensemble de modèles | sortie du méta-modèle après calibration isotonique, bornée entre 0,01 et 0,99 |
| `A` | Accord entre modèles | `1 − écart-type des probabilités des modèles / 0,5` |
| `D` | Complétude des données | part des variables clés disponibles (compos confirmées, xG, absences, arbitre…) |
| `M` | Accord avec le marché | `1 − abs(p_modèle − p_marché_sans_marge)`, avec Pinnacle comme référence |
| `R` | Risque intégrité | score du menu Intégrité ramené entre 0 et 1 |
| `V` | Volatilité | instabilité de la prédiction sur les dernières heures (live : dernières minutes) |

Les exposants `α…ζ` sont **appris par optimisation** (maximisation de la réussite par tranche d'IC en backtest) et non fixés à la main. Une sélection entre dans un coupon ou un combo si `conf_min ≤ p_cal ≤ conf_max` (curseur 1-100 %, défaut 70-98 %) **et** `IC ≥ seuil utilisateur`.

---

### 13. Algorithme « Générer / Régénérer » (pseudo-code)

```python
def generer(scope, taille, conf_min=0.70, conf_max=0.98, ic_min=0, mode="surete", exclure=()):
    # taille : 1-10 (coupon) ou 1-20 (combo)
    # conf_min / conf_max : curseur 1-100 % ramené entre 0,01 et 1,00
    candidats = [
        p for p in predictions(scope)            # scope : "jour" ou "avenir"
        if conf_min <= p.p_cal <= conf_max
        and p.ic >= ic_min
        and p.id not in exclure
        and p.integrity_level in ("vert", "jaune")
        and p.match.kickoff > now() + marge_minutes
    ]
    # une seule sélection par match : la meilleure parmi tous ses marchés
    meilleurs = best_per_match(candidats, key=score(mode))
    coupon = []
    for c in sorted(meilleurs, key=score(mode), reverse=True):
        if len(coupon) == taille: break
        if max_correlation(c, coupon) < 0.3:   # évite les sélections liées
            coupon.append(c)
    return Coupon(coupon, p_combinee=proba_jointe(coupon))  # Monte-Carlo si corrélations

def regenerer(coupon_actuel, taille, **params):
    alternative = generer(taille=taille, exclure=ids(coupon_actuel), **params)
    final, remplacees = [], []
    for ancien, neuf in zip_longest(coupon_actuel.trie(), alternative.trie()):
        if ancien is None:
            final.append(neuf)
        elif neuf is None or ancien.locked or score(ancien) >= score(neuf):
            final.append(ancien)                 # on garde le plus haut pourcentage
        else:
            final.append(neuf.marquer("Nouveau"))
            remplacees.append((ancien, neuf))
    final = completer(dedupe_par_match(final), alternative, taille)
    message = "Coupon déjà optimal" if not remplacees else f"{len(remplacees)} sélection(s) améliorée(s)"
    return {
        "coupon": Coupon(final, p_combinee=proba_jointe(final)),
        "alternative": alternative,              # affichée à côté, grisée si plus faible
        "remplacees": remplacees,
        "message": message,
    }
```

Score selon le mode :
- **Sûreté** : `p_cal` (le plus haut pourcentage gagne), puis `IC` en cas d'égalité
- **Rendement** : `EV × IC` (EV = p × cote − 1)
- **Équilibré** : `√(p_cal) × (1 + EV) × IC`

Chaque génération est enregistrée (`coupon_generations`) avec la proposition, les sélections gardées, les sélections remplacées et le message.

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
- **Enjeu** : écart au titre, à l'Europe, à la relégation, derby, match retour (score de l'aller), primes en jeu.
- **Arbitre et conditions** : profil de l'arbitre, météo, pelouse, affluence.
- **Marché** : cotes d'ouverture, cotes actuelles sans marge, mouvements, volumes.

---

### 18. API et événements temps réel

**REST (extraits)**
```
GET  /v1/matches?date=&competition=&status=
GET  /v1/matches/{id}                 # fiche complète + enjeux et primes
GET  /v1/matches/{id}/predictions     # tous les marchés, triés par confiance
GET  /v1/value-bets?min_value=&min_ic=
POST /v1/coupons/generate             # {size: 1..10, conf_min: 1..100, conf_max: 1..100, ic_min, mode, scope, q}
POST /v1/coupons/{id}/regenerate      # → {coupon, alternative, remplacees, message}
GET  /v1/combo?count=1..20&conf_min=1..100&conf_max=1..100&mode=&scope=jour|avenir&singles=
GET  /v1/journal?period=&status=&market=
GET  /v1/integrity/alerts?level=
GET  /v1/teams/{id}/stats?metric=corners|shots|shots_on_target|cards|fouls|offsides|assists|tackles|throw_ins
GET  /v1/changes?entity=&importance=  # journal des changements coloré
POST /v1/favorites   DELETE /v1/favorites/{id}
POST /v1/assistant/ask
```

**WebSocket** (`wss://…/live`, abonnement par match ou par canal)
```
match.event        { match_id, minute, type, team, player }
match.stats        { match_id, period, stats, xg, momentum }
prediction.update  { prediction_id, p_cal, ic, fair_odds, value }
prediction.settled { prediction_id, status: VALIDE|PERDU|PUSH|ANNULE }
coupon.update      { coupon_id, status, combined_probability }
odds.move          { match_id, market, from, to, pct, severity }
integrity.alert    { match_id, risk_score, level, signals[] }
change.logged      { entity_type, entity_id, field, old, new, importance, color }
```
Chaque message porte un **numéro de séquence**. À la reconnexion, le client demande les messages manqués depuis le dernier numéro reçu (aucune perte).

---

### 19. Indicateurs de qualité (KPI et SLO)

| Domaine | Objectif |
|---|---|
| Calibration | écart moyen entre probabilité prévue et fréquence observée < 3 points par tranche de 10 % |
| Précision | Brier, log-loss et RPS meilleurs que les probabilités du marché sans marge (hors Pinnacle) et que le moteur existant (RPS 0,2009, section 25) |
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

- **Coupon** : avec le curseur sur 70-98 %, un coupon de 5 ne contient que des sélections entre 70 et 98 %, une seule par match, aucune sur un match 🟠/🔴 en intégrité, et affiche la probabilité combinée.
- **Coupon de 1** : renvoie le meilleur pari simple du jour dans la plage choisie.
- **Curseur à 100 %** : le message « Aucune prédiction n'atteint 100 % » s'affiche avec les sélections les plus proches ; aucune probabilité affichée ne dépasse 99 %.
- **Régénérer** : si toutes les nouvelles sélections sont plus faibles, le coupon reste identique, le message « Coupon déjà optimal » apparaît et la nouvelle proposition est visible, grisée, en dessous. Si une nouvelle sélection est meilleure, elle remplace la plus faible et porte le badge « Nouveau ».
- **Combo** : choisir 7 dans le sélecteur place la réglette sur 7 ; la réglette accepte de 1 à 20.
- **Live** : un but est affiché et les prédictions recalculées en moins d'1 s. Une prédiction « Over 1.5 » passe en **Validé** dès le 2ᵉ but. Les prédictions de 1re mi-temps sont réglées à la pause.
- **Journal** : les compteurs Tous / En cours / Validés / Perdus / Push correspondent exactement au détail des lignes.
- **Intégrité** : un mouvement de cote simulé de −25 % en 10 minutes sans information publique déclenche une alerte 🟠 horodatée.
- **Stats équipes** : une moyenne de corners qui varie de plus de 2 écarts-types crée une entrée 🟠 dans le journal des changements, avec les matchs et les cotes concernés.
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

Utilise toutes les ressources **légales** disponibles, et va aussi loin que possible dans ce cadre :

1. **Données** : uniquement des sources légales, sous licence ou API officielles, en respectant leurs conditions d'utilisation. Aucune donnée inventée présentée comme réelle.
2. **Honnêteté des probabilités** : aucun pronostic n'est garanti. Les pourcentages affichés sont des probabilités calibrées et vérifiables, accompagnées des performances historiques réelles du modèle. Jamais de « 100 % sûr ».
3. **Intégrité** : signaux et scores de risque, pas d'accusation nominative ; possibilité de signalement aux autorités.
4. **Jeu responsable** : vérification d'âge (18+), limites de dépôt/mise conseillées, messages de prévention, liens vers les services d'aide, respect de la réglementation de chaque pays.
5. **Qualité** : chaque fonctionnalité est testée, documentée et mesurée avant d'être livrée.

---

### 25. Point de départ existant

Si tu as accès au dépôt du projet, ne repars pas de zéro :

- **`backend/`** : moteur Python sur données réelles (résultats officiels de 8 championnats, source openfootball, domaine public). Il comprend Dixon-Coles pondéré dans le temps, Elo, un mélange 65 % Dixon-Coles / 35 % Elo, la calibration isotonique, les marchés, la value, Kelly, un score d'intégrité, une API FastAPI, des tests, un journal réel des prédictions et une mise à jour quotidienne par GitHub Actions.
- **Résultats du backtest walk-forward** (9 211 matchs) : RPS 0,2009, log-loss 0,9903, précision 1X2 51,2 %. Calibration : 70-80 % annoncé → 74 % observé ; 80-90 % → 85 % ; 90-98 % → 93 %. C'est le niveau à battre.
- **`prototype/omniscore.html`** : maquette fonctionnelle de tous les menus (données simulées + onglets sur matchs réels). Elle utilise encore les anciennes plages (coupons 2/3/5/8/10, confiance 70-98 %), à aligner sur ce prompt.
- **Prochains gains attendus** : cotes réelles, xG et compositions. Avec les seuls résultats, le modèle a atteint son plafond.

---

Commence par me présenter l'architecture détaillée, le schéma de données final et le plan du MVP (user stories + critères d'acceptation). Si le dépôt existe, commence par un audit de `backend/` et `prototype/` et dis ce que tu réutilises. Ensuite, code étape par étape : à chaque étape, montre l'avancement, les tests passés et les métriques du modèle.
