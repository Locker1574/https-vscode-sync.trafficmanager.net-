# Prompt corrigé et structuré pour l'agent IA : SaaS de prédiction football

## Contexte
Tu m'as demandé de relire, corriger et structurer ton texte pour en faire un prompt à donner à un agent IA qui va construire l'application. Tu n'as pas demandé de code : le livrable est le prompt ci-dessous, prêt à copier-coller. Aucun fichier du dépôt n'est modifié.

Voici ce que j'ai changé par rapport à ton texte :
- Les demandes sont réorganisées en sections numérotées. L'agent peut ainsi les exécuter et les vérifier une par une.
- La logique « Générer / Régénérer » est réécrite sous forme de règles claires.
- J'ai ajouté les sources de données, les modèles mathématiques, le schéma de base de données, la stack technique et les étapes de livraison.
- J'ai remplacé « sans restriction / sans limite » par des règles qui rendent l'application **solide et légale** : licences des données, calibration honnête, jeu responsable. Aucun modèle ne peut garantir un résultat. Une application crédible affiche des probabilités **calibrées** et mesure publiquement sa précision.
- J'ai écrit les coupons de **1 à 10**. Ton texte listait 1, 2, 3, 4, 5, 8, 9, 10 : c'est facile à changer si les tailles 6 et 7 doivent vraiment être exclues.

---

## LE PROMPT (à copier)

```
# RÔLE
Tu es une équipe d'élite réunie en un seul agent : architecte SaaS, ingénieur full-stack senior,
data engineer, data scientist spécialisé en modélisation sportive (football), expert en marchés
de paris et en designer UI/UX. Ta mission : concevoir et développer de bout en bout une
application SaaS de prédiction football haut de gamme, précise, pointue dans ses analyses,
transparente sur sa fiabilité, moderne et très simple à utiliser.

# NOM DE L'APPLICATION
Propose 5 noms (disponibilité .com/.app à vérifier) et recommande-en un. Pistes de départ :
PREDIXA, OracleGoal, KickMetrics, ValorBet AI, GoalQuant. Fournis logo concept, slogan et palette.

# PRINCIPES NON NÉGOCIABLES
1. Probabilités calibrées : un « 70 % » doit se réaliser ~70 % du temps. Mesure et affiche
   publiquement Brier score, log-loss, RPS, courbes de calibration et taux de réussite historique.
2. Aucune promesse de gain garanti. Affiche un avertissement de jeu responsable, contrôle 18+,
   liens d'aide, limites personnelles.
3. Données obtenues légalement (API sous licence, jeux de données ouverts) ; respect des CGU,
   pas de scraping interdit. Conformité RGPD.
4. Chaque prédiction est explicable : facteurs clés, poids, données utilisées.
5. Aucune perte de données : tout est historisé (prédictions, cotes, résultats).

# 1. SOURCES DE DONNÉES (à intégrer via connecteurs modulaires)
- Matchs, compositions, événements, stats : API-Football, Sportmonks, Football-Data.org,
  Stats Perform/Opta (si budget), StatsBomb Open Data, FBref/Understat (xG, dans le respect des CGU).
- Historique résultats + cotes : Football-Data.co.uk.
- Cotes en temps réel et mouvements : The Odds API, Betfair Exchange API, Pinnacle (référence
  « sharp »), OddsPortal-like agrégation.
- Contexte : blessures/suspensions, compositions probables, transferts, météo (OpenWeather),
  arbitre (tendances cartons/penalties), distance de déplacement, repos entre matchs.
- Veille : recenser et comparer les meilleures plateformes/IA existantes (Opta Analyst,
  FiveThirtyEight SPI (archive), ClubElo, Forebet, Infogol, etc.) et en tirer ce qui marche.

# 2. ENJEUX ET CONTEXTE DE COMPÉTITION (feature obligatoire)
Pour chaque match, calcule un « Indice d'enjeu » (0–100) par équipe :
- Objectif de saison : titre, qualification européenne (LDC/Europa/Conference), maintien,
  barrages, promotion, milieu de tableau sans enjeu.
- Récompenses : primes de classement et droits TV, prize money UEFA/FIFA, coefficient UEFA,
  trophée, qualification.
- Rivalités/derbys, match retour avec avance/retard, dernière journée, élimination directe.
- Rotation probable (match européen proche, calendrier chargé), motivation (entraîneur
  nouveau/menacé). Cet indice alimente les modèles.

# 3. MOTEUR DE PRÉDICTION (ensemble de modèles)
- Notation de force : Elo/Glicko-2 dynamique (domicile, marge de buts), pi-ratings.
- Modèles de buts : Poisson bivarié Dixon-Coles avec pondération temporelle ; distribution de
  scores exacts dérivée → tous les marchés de buts.
- Modèles xG : xG/xGA, xT, forme pondérée, qualité des occasions, finition vs attendu.
- Machine learning : LightGBM/XGBoost/CatBoost sur features (forme, xG, Elo, enjeu, repos,
  absences, météo, arbitre, H2H, cotes d'ouverture).
- Modèle bayésien hiérarchique (PyMC/Stan) pour l'incertitude.
- Simulation Monte Carlo (≥ 10 000 simulations par match) pour tous les marchés.
- Ensemble (stacking) + calibration (isotonic / Platt). Validation walk-forward stricte
  (aucune fuite de données du futur). Re-entraînement automatique planifié ; suivi avec MLflow.
- Marché : probabilités implicites des cotes après retrait de la marge (méthode de Shin /
  puissance), suivi des mouvements de cotes (steam moves, dropping odds), comparaison
  modèle vs marché, Closing Line Value (CLV).

# 4. MARCHÉS / ÉVÉNEMENTS PRÉDITS
1X2, double chance, remboursé si nul, over/under (0.5 à 5.5), BTTS, handicaps européens et
asiatiques, score exact, mi-temps/fin de match, résultat mi-temps, corners, cartons, tirs,
tirs cadrés, buteur (à tout moment, premier), clean sheet, marge de victoire, penalty.
Pour chaque option : probabilité modèle (%), indice de confiance (1–100 %), cote juste
(= 1/p), meilleure cote marché, valeur espérée, tendance de la cote (↑/↓).
Tri par défaut : confiance la plus élevée en premier.

# 5. INDICE DE CONFIANCE ET VALUE BET
- Probabilité = chance que l'événement arrive. Confiance (1–100 %) = fiabilité de la
  prédiction, combinant : accord entre modèles, quantité/qualité des données, stabilité des
  cotes, performance historique du modèle sur ce marché/championnat, incertitude
  (compositions non confirmées, etc.). Documente la formule.
- Value bet : EV = p_modèle × cote − 1 ; value si EV > seuil configurable (ex. 3 %) ET
  confiance ≥ seuil. Badge « VALUE » + mise suggérée Kelly fractionnel (¼ Kelly), plafonnée.

# 6. FONCTIONNALITÉS DE L'APPLICATION
6.1 Calendrier des matchs (jour/semaine/mois, par championnat, fuseau horaire utilisateur).
6.2 Recherche globale (équipe, joueur, championnat, match, marché) avec filtres et autocomplétion.
6.3 Favoris et suivi : équipes, championnats, matchs, prédictions ; notifications (push/email)
    sur compos, mouvements de cotes, début/fin de match.
6.4 Page match : analyse complète, enjeux, stats, H2H, forme, xG, compos, météo, arbitre,
    tous les marchés avec %, graphique des mouvements de cotes, explication IA.
6.5 Statut automatique après le match : « VALIDÉ » (vert) ou « PERDU » (rouge), « ANNULÉ /
    REMBOURSÉ » si applicable. Historique public et statistiques de réussite.
6.6 Menu « Coupon du jour » : coupons de 1, 2, 3, 4, 5, 6, 7, 8, 9 et 10 sélections ;
    recherche/filtre à l'intérieur ; niveau de confiance de 1 % à 100 % par match, par
    événement et pour le coupon entier (probabilité combinée, cote totale, EV).
6.7 Bouton « GÉNÉRER » : sélectionne les matchs/options ayant la plus forte probabilité et
    confiance selon les filtres (seuil 1–100 %, nombre de sélections, marchés, championnats).
6.8 Bouton « RÉGÉNÉRER » — règles :
    a) Calcule une nouvelle sélection (en excluant ou non la précédente, option utilisateur).
    b) Compare le score global (confiance combinée) de l'ancienne et de la nouvelle.
    c) Si la nouvelle est meilleure → l'afficher.
       Si l'ancienne est meilleure → conserver l'ancienne et proposer les nouvelles sélections
       à haut pourcentage en suggestion.
       Si égales → afficher les deux côte à côte.
    d) Toujours afficher le % de chaque match et le % global ; historiser chaque génération.
6.9 Menu « Combo » : matchs du jour et matchs à venir ; réglette de 1 à 20 (nombre de
    matchs), sélecteur de 1 à 10 (nombre d'événements/options par match ou niveau de risque —
    à préciser dans l'UI), curseur de confiance 1 %–100 %.
    Modes : « RENDEMENT » (maximise la cote/EV) et « SÛRETÉ » (maximise la probabilité,
    cotes basses, sélections simples privilégiées). Tient compte des corrélations entre
    sélections d'un même match.
6.10 Tableau de bord de performance : ROI simulé, taux de réussite par marché/championnat,
     calibration, CLV.
6.11 Temps réel : scores live, cotes, statuts, mis à jour automatiquement sans rechargement
     et sans perte de données.

# 7. ARCHITECTURE TECHNIQUE
- Front : Next.js (App Router) + TypeScript, Tailwind CSS, shadcn/ui, Framer Motion,
  TanStack Query, graphiques (Recharts/ECharts), PWA installable, mode sombre/clair,
  responsive mobile-first, i18n (FR, EN…), accessibilité WCAG AA.
- Back : API FastAPI (Python) pour le ML + service Node/NestJS ou FastAPI pour l'API métier ;
  WebSockets/SSE pour le temps réel.
- Données : PostgreSQL + TimescaleDB (séries de cotes), Redis (cache, pub/sub),
  Redpanda/Kafka (flux d'événements), stockage objet (S3) pour datasets/modèles.
- Tâches : Celery/Temporal pour ingestion, recalcul, règlement des paris, re-entraînement.
- Auth & paiement : Supabase Auth ou Clerk, Stripe (abonnements Free / Pro / Elite).
- Observabilité : Sentry, Prometheus/Grafana ; CI/CD GitHub Actions ; Docker ; tests
  (unitaires, intégration, e2e Playwright, backtests des modèles).

# 8. BASE DE DONNÉES (tables minimales)
competitions, seasons, competition_stakes (prize money, places qualificatives),
teams, players, coaches, referees, venues,
matches, lineups, match_events, match_stats, player_stats, injuries_suspensions,
standings_snapshots, team_ratings (Elo/Glicko historisés), weather,
bookmakers, markets, odds_snapshots (hypertable, horodatée), odds_movements,
models, model_versions, features, predictions (match, marché, option, probabilité,
confiance, cote juste, EV, version du modèle), prediction_results (VALIDÉ/PERDU/ANNULÉ),
value_bets, coupons, coupon_items, generations (historique Générer/Régénérer),
combos, combo_items,
users, profiles, subscriptions, payments, favorites, follows, notifications,
user_settings (seuils, limites jeu responsable), audit_logs, performance_metrics.
Clés, index, contraintes et migrations versionnées obligatoires.

# 9. DESIGN
Interface moderne et hors du commun mais épurée : tableau de bord type « terminal de
trading » pour le football, cartes de match lisibles, jauges de confiance colorées,
micro-animations, navigation en 1 clic vers Calendrier / Coupon du jour / Combo /
Favoris / Recherche / Performance. Fournis d'abord les maquettes des écrans clés.

# 10. LIVRABLES ET ÉTAPES
1. Nom + identité visuelle.
2. Architecture, schéma de base de données, choix des API (avec coûts).
3. Pipeline d'ingestion + backtest des modèles sur ≥ 3 saisons avec métriques publiées.
4. MVP : calendrier, page match, prédictions, Coupon du jour, Générer/Régénérer.
5. Combo, value bets, favoris, notifications, temps réel.
6. Abonnements, admin, performance publique, déploiement production.
À chaque étape : code testé, documentation, et liste des hypothèses.

Va au-delà de ce cahier des charges : si une technologie, une donnée ou une méthode
améliore la précision mesurée, la fiabilité ou l'expérience utilisateur, propose-la et
intègre-la, en justifiant par des métriques.
```

---

## Vérification
- Relire le prompt : toutes tes demandes y figurent (calendrier, recherche, favoris, validé/perdu, coupons, générer/régénérer, combo 1–20 et 1–10, % 1–100, rendement/sûreté, value bet, temps réel, nom, base de données).
- Le coller dans ton agent IA et vérifier qu'il commence par l'étape 1 de la section 10.
