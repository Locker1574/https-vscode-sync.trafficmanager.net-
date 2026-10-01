# Prompt pour l'IA de construction d'app : SaaS de prédictions football virtuel FIFA + Jeu 21

## Contexte
L'utilisateur veut un prompt prêt à coller dans un générateur d'apps par IA (« argent AI ») pour construire un SaaS de prédictions sur le football virtuel (FIFA / FC, Penalty, Simulation) et le Jeu 21. Le livrable est **le texte ci-dessous**, pas du code dans ce dépôt. Le prompt impose de vrais modèles statistiques, des probabilités calibrées, la priorité à la confiance la plus haute, le suivi Validé / Perdu, et un affichage honnête de la précision réelle. Les jeux virtuels sont générés par un algorithme (RNG) avec une marge pour le bookmaker : aucune app ne peut garantir une « ultra précision ». Le prompt demande donc de mesurer la précision et de l'afficher telle quelle, au lieu de la promettre.

---

## PROMPT (à copier-coller)

```
Tu es une équipe d'experts réunie en une seule IA : architecte SaaS full-stack, data scientist spécialisé en modélisation sportive (Poisson, Dixon-Coles, Elo/Glicko, Skellam, Monte-Carlo), ingénieur ML (XGBoost/LightGBM, calibration de probabilités), expert en probabilités des jeux de cartes, et designer UX mobile-first.

## MISSION
Construis une application SaaS complète, prête pour la production, de PRÉDICTIONS sur les jeux virtuels de football (FIFA / EA FC) et sur le Jeu 21. Elle doit analyser chaque match ou chaque main, calculer des probabilités calibrées pour tous les marchés de paris, classer les options de la plus forte à la plus faible confiance, puis valider automatiquement chaque prédiction (VALIDÉ ✅ / PERDU ❌) quand le résultat tombe.

## COMPÉTITIONS À COUVRIR (chacune avec son propre modèle et son propre historique)
Football virtuel :
- FC 26. 5x5 Rush. Superligue
- FC 24. 4x4. Championnat d'Angleterre
- FC 25. 3x3. Ligue de conférence
- FC 26. England Championship
- FC 26. Champions League
- FC 26. Championnat du monde
- FC 25. Italy Championship
- FC 25. Ligue européenne
- FC 26. Germany Championship
- FC 26. Italy Championship
- FC 26. Spain Championship
- UEFA Nations League. Simulation
Tirs au but :
- FC24. Penalty / FC25. Penalty / FC26. Penalty / FIFA23. Penalty / Penalty (toutes les variantes)
Jeu 21 :
- 21 classics
- 21 Dota. Jusqu'à 3 victoires
- Le 21

IMPORTANT : les formats 5x5, 4x4 et 3x3 produisent beaucoup plus de buts que le 11 contre 11. Ne mélange jamais les ligues : chaque compétition a ses propres paramètres (moyenne de buts, avantage du domicile, distribution des scores, durée du match).

## 1. COLLECTE DES DONNÉES
- Module d'ingestion des résultats en continu : connecteurs API/flux configurables (le fournisseur de données est une variable d'environnement), import CSV/JSON, et saisie manuelle par un administrateur.
- Pour chaque match, stocke : compétition, horodatage, équipes, score à la mi-temps et score final, minutes des buts, corners, cartons, cotes d'ouverture et de clôture pour chaque marché.
- Pour les penalties : séquence de tous les tirs (marqué/raté), tireur, côté, ordre.
- Pour le Jeu 21 : cartes du joueur et du croupier, total de chaque main, résultat, nombre de manches (format « jusqu'à 3 victoires »).
- Contrôle de qualité : dédoublonnage, détection des données aberrantes, stockage horodaté (time-series).

## 2. MOTEUR DE PRÉDICTION FOOTBALL VIRTUEL (ensemble de modèles)
a) Notes de force par équipe : Elo dynamique + attaque/défense par équipe (rolling window, décroissance exponentielle du poids des vieux matchs).
b) Modèle de buts : Poisson bivarié + correction Dixon-Coles pour les petits scores. Matrice de probabilités pour chaque score exact de 0-0 à 10-10, avec une plus grande plage pour les formats Rush, 4x4 et 3x3.
c) Modèle ML : gradient boosting (LightGBM/XGBoost) entraîné sur des variables comme la forme récente, la tête-à-tête, le rythme de buts par ligue, les tendances mi-temps et fin de match, et les cotes du marché (probabilité implicite après retrait de la marge).
d) Simulation Monte-Carlo (≥ 10 000 simulations par match) pour dériver tous les marchés.
e) Les modèles sont combinés par stacking ou par moyenne pondérée. Les poids sont optimisés par ligue sur un jeu de validation.
f) Calibration obligatoire (Platt ou isotonique). Un « 70 % » doit se réaliser environ 70 % du temps.
g) Détection des motifs ou cycles possibles du générateur : tests statistiques (chi², autocorrélation, runs test). L'app indique honnêtement quand aucun motif exploitable n'est détecté.

Marchés à calculer pour chaque match :
1X2, Double chance, Draw No Bet, Over/Under (toutes les lignes : 0.5 → 9.5 selon le format), Les deux équipes marquent (BTTS), Score exact, Mi-temps/Fin de match, Résultat à la mi-temps, Over/Under mi-temps, Total de buts par équipe, Handicap asiatique et européen, Équipe qui marque en premier/en dernier, Pair/Impair, Marge de victoire, Clean sheet, Corners et cartons quand les données existent.

Marchés penalty : vainqueur de la séance, nombre total de tirs réussis, prochain tir marqué/raté, séance qui va jusqu'en mort subite, score exact de la séance (modèle binomial/Markov tir par tir).

## 3. MOTEUR JEU 21
- Calcul exact des probabilités (combinatoire et suivi du sabot si le nombre de jeux de cartes est connu), à partir des cartes déjà sorties : probabilité de dépasser 21, distribution de la main finale du croupier, et EV de chaque action (tirer, rester, doubler).
- Stratégie de base optimale et recommandation de l'action ayant la meilleure EV.
- Marchés : vainqueur de la manche, total des points du joueur/croupier (plus ou moins de X), bust oui/non, 21 exact, et vainqueur du match « jusqu'à 3 victoires » (chaîne de Markov sur les manches).
- Si le sabot est mélangé à chaque main, l'app l'indique et n'affiche que les probabilités théoriques.

## 4. CLASSEMENT ET AFFICHAGE DES PRÉDICTIONS
- Pour chaque match ou main, affiche TOUTES les options de pari, triées par probabilité calibrée décroissante.
- La prédiction ayant la plus forte confiance apparaît EN PREMIER et en évidence (« Pick principal »).
- Niveaux de confiance : 🟢 Très forte (≥ 80 %), 🟡 Forte (65-79 %), 🟠 Moyenne (50-64 %), 🔴 Faible (< 50 %).
- Pour chaque option, affiche : probabilité du modèle (%), cote du bookmaker, probabilité implicite, Value = (probabilité × cote) − 1, intervalle de confiance, et une courte explication en français (les 3 facteurs principaux, via SHAP).
- Filtres : par compétition, par marché, par confiance minimale et par value positive.
- Générateur de combinés : sélections les plus fiables, probabilité combinée calculée et affichée honnêtement (elle baisse vite).
- Mise suggérée : critère de Kelly fractionné (¼ Kelly), plafonné, affiché seulement si la value est positive.

## 5. VALIDATION AUTOMATIQUE ET SUIVI
- Dès que le résultat est ingéré, chaque prédiction passe à VALIDÉ ✅ ou PERDU ❌ (ou REMBOURSÉ pour DNB et handicap).
- Tableau de bord des performances : taux de réussite par compétition, par marché et par niveau de confiance, ROI, profit cumulé, série en cours, Brier score, log-loss et courbe de calibration.
- Historique complet, exportable en CSV.
- Le modèle se réentraîne automatiquement (planifié, par ex. toutes les nuits) et suit sa dérive : si la précision baisse, il rétrograde les niveaux de confiance.

## 6. BACKTESTING
- Backtest walk-forward sur l'historique de chaque ligue, sans fuite de données (le modèle ne voit que le passé).
- Rapport : précision réelle par niveau de confiance, ROI simulé à la cote de clôture, et comparaison avec un modèle de base qui suit simplement les cotes du marché.

## 7. FONCTIONNALITÉS SAAS
- Authentification (e-mail + Google), rôles Admin / Abonné / Gratuit.
- Abonnements via Stripe : Gratuit (quelques pronostics par jour), Premium et VIP (tous les marchés, alertes, API).
- Notifications push/Telegram/e-mail quand un pick 🟢 est disponible.
- Panneau admin : gestion des ligues, des sources de données, des paramètres des modèles et des utilisateurs.
- Interface en français, mobile-first, mode sombre, mise à jour en temps réel (WebSocket).

## 8. STACK TECHNIQUE RECOMMANDÉE
- Frontend : Next.js + TypeScript + Tailwind + shadcn/ui, graphiques avec Recharts.
- Backend API : FastAPI (Python) pour le moteur de prédiction, PostgreSQL + TimescaleDB, Redis (cache et file de tâches), Celery/RQ pour l'ingestion et le réentraînement.
- ML : pandas, numpy, scipy, scikit-learn, LightGBM, statsmodels, SHAP.
- Déploiement : Docker, CI/CD, variables d'environnement pour les clés, logs et monitoring.
- Tests unitaires du moteur de probabilités : la somme des probabilités 1X2 vaut 100 %, la matrice de scores est cohérente, et les calculs du Jeu 21 sont vérifiés contre des valeurs connues.

## 9. RÈGLES D'HONNÊTETÉ ET DE CONFORMITÉ (obligatoires)
- Ne JAMAIS afficher « 100 % sûr » ni « gain garanti ». Les jeux virtuels sont générés par un algorithme avec une marge pour l'opérateur. Seules les probabilités calibrées et le taux de réussite réel mesuré sont affichés.
- Le pourcentage affiché doit toujours correspondre à la réussite observée en backtest et en direct (page « Transparence » publique).
- Section Jeu responsable : limites de mise, avertissement 18+, liens d'aide, auto-exclusion.
- Respect du RGPD et des lois locales sur les jeux d'argent.

## LIVRABLES ATTENDUS
1. L'architecture et le schéma de la base de données.
2. Le code complet du frontend, du backend et du moteur ML, avec des commentaires.
3. Les scripts d'ingestion et de backtesting.
4. Un jeu de données de démonstration pour tester l'app sans fournisseur réel.
5. Un README d'installation et de déploiement.

Commence par me présenter l'architecture et le schéma de la base de données, puis construis l'application module par module en testant chaque étape.
```

---

## Conseils d'utilisation
- Si l'IA cible limite la longueur des messages, envoie le prompt par sections (1 → 9) dans l'ordre.
- La précision dépend surtout de la quantité et de la qualité de l'historique : il faut idéalement plusieurs milliers de matchs par ligue avant de faire confiance aux niveaux 🟢.
- Juge l'app sur sa page « Transparence » (taux réel par niveau de confiance), pas sur ses promesses.

## Vérification
Après la génération, vérifier que : (1) les probabilités 1X2 font 100 %, (2) le backtest walk-forward tourne sur les données de démo, (3) le statut VALIDÉ/PERDU change bien quand un résultat est saisi, (4) le pick principal est bien celui qui a la plus forte probabilité.
