# OMNISCORE : prototype

Prototype fonctionnel en un seul fichier (`omniscore.html`), sans dépendance ni étape de build. Ouvrez-le dans un navigateur.

**Toutes les équipes, cotes et statistiques sont simulées.** Le moteur de calcul est réel ; pour la production, remplacez `genData()` par un connecteur vers une API sous licence (voir `../PROMPT_AGENT_IA.md`, section 1).

## Ce qui fonctionne
- Modèle Poisson + correction Dixon-Coles → 1X2, double chance, remboursé si nul, plus/moins, les deux marquent, 1re mi-temps.
- Modèles de comptage : corners, cartons, tirs cadrés, fautes, hors-jeux.
- Cotes multi-bookmakers simulées, value (`p × cote − 1`), mise ¼ Kelly.
- Indice de confiance `IC = 100 × p × A^0,6 × D^0,7 × M^0,9 × (1−R)^1,2 × (1−V)^0,5`.
- Live mis à jour chaque seconde (1 s = 30 s de jeu) : momentum, xG, stats, prochain but, prédictions live, auto-suivi Validé / Perdu / Remboursé.
- Coupons 2/3/5/8/10 (70-98 %), Générer / Régénérer (garde toujours le plus haut pourcentage), verrouillage.
- Combo : réglette 1-20, sélecteur rapide, curseur de confiance, modes Rendement / Sûreté / Équilibré, cotes simples.
- Journal (statuts, calibration, ROI par marché), Intégrité (z-score robuste, divergence, volume, 4 niveaux de couleur, journal des changements), Stats équipes (10 métriques, tendances, anomalies), Favoris et notifications.
- Sauvegarde locale de l'état toutes les 5 s, avec rattrapage du temps écoulé au rechargement.
