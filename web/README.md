# OMNISCORE : application web SaaS

Application Next.js qui s'appuie sur le moteur Python (`../backend`) : comptes, abonnements, prédictions en base de données, temps réel.

## Fonctionnalités
- **Comptes** : inscription (18 ans et plus), connexion, sessions signées (JWT HS256 dans un cookie `httpOnly`), mots de passe bcrypt.
- **Tableau de bord** : prochaine journée, sélections à plus forte confiance, value bets, journal réel, dernière mise à jour.
- **Calendrier** : 21 prochaines journées, filtre par championnat, étoile de suivi sur chaque match.
- **Fiche match** : 41 marchés avec probabilité, indice de confiance, cote juste, cote du marché, mouvement de cote, value, statut Validé / Perdu / Remboursé, évolution depuis la première version du modèle.
- **Coupon du jour** : 1 à 10 sélections, seuil de confiance 1-100 %, modes Sûreté / Équilibré / Rendement, matchs du jour ou à venir, filtres par championnat et par marché, recherche dans le coupon, verrouillage.
  - **Générer** : meilleure option de chaque match au-dessus du seuil.
  - **Régénérer** : une sélection n'est remplacée que par une nouvelle au pourcentage plus élevé *et* au score au moins égal ; sinon le coupon est conservé et les nouveaux matchs sont proposés en alternative. Chaque clic est historisé (`generations`).
- **Combo** : réglette de 1 à 20 matchs, sélecteur de 1 à 10 options par match, choix de l'option par match, mode paris simples (cotes seules).
- **Value bets** (Pro) : EV = p × cote − 1 ≥ 3 %, mise ¼ Kelly plafonnée à 5 %.
- **Mes coupons** : réglés automatiquement à l'arrivée des résultats.
- **Favoris** : matchs et équipes suivis. **Recherche** : équipes et prochains matchs.
- **Performance** : journal réel, backtest (RPS, log-loss, Brier, précision), calibration, coupons backtestés.
- **Compte** : offre Gratuit / Pro (Stripe Checkout, portail client, webhook), pause jeu responsable (prolongeable, jamais raccourcie).
- **Temps réel** : `/api/stream` (Server-Sent Events) envoie la version des données ; les pages se rafraîchissent sans perdre l'état local.
- **Aucune perte de données** : upsert des valeurs courantes, historique append-only (`prediction_snapshots`, `odds_snapshots`), journal réel jamais réécrit, chaque synchronisation tracée (`sync_runs`).

## Offres
| | Gratuit | Pro |
|---|---|---|
| Coupons | 3 sélections | 10 sélections |
| Combo | 3 matchs | 20 matchs |
| Value bets | aperçu | oui |
| Favoris | 10 | 500 |

## Démarrage local
```bash
cp .env.example .env.local      # renseigner SESSION_SECRET (openssl rand -base64 32)
npm install
npm run db:migrate              # PostgreSQL requis (DATABASE_URL)
npm run prebuild && npm run sync  # copie ../backend/data dans web/data puis importe les prédictions
npm run dev                     # http://localhost:3000
```
Tout en un : `SESSION_SECRET=$(openssl rand -base64 32) docker compose up --build` à la racine du dépôt (base, API du moteur, application).

## Mise en ligne sur Vercel
Le dépôt est déjà relié à Vercel. Dans le projet Vercel :
1. **Settings → General → Root Directory** : `web`. Laisser activée l'option qui inclut les fichiers hors de ce dossier (le build copie `../backend/data`).
2. **Storage → Neon (Postgres)** → *Connect Project* : `DATABASE_URL` est ajouté automatiquement (`POSTGRES_URL` est aussi accepté).
3. **Settings → Environment Variables** :
   - `SESSION_SECRET` : 32 caractères minimum (`openssl rand -base64 32`) ;
   - `CRON_SECRET` : chaîne aléatoire (protège `/api/cron/sync`) ;
   - optionnel : `APP_URL` (URL publique) et les clés Stripe.
4. **Redéployer.**

À chaque déploiement, `vercel.json` lance `npm run vercel-build` : copie des données du moteur dans `web/data`, migrations, synchronisation, puis build.
Un cron Vercel appelle `/api/cron/sync` tous les jours à 06:30 UTC. La mise à jour quotidienne du moteur (`omniscore-daily.yml`) commite de nouvelles données, ce qui redéploie l'application.

## Synchronisation
Source : l'API du moteur (`OMNISCORE_API_URL`, route `/v1/export`) ou, à défaut, les fichiers JSON : `web/data` (copié depuis `../backend/data` par `npm run build`) ou le dossier `OMNISCORE_DATA_DIR`.
Déclencheurs : toutes les `SYNC_INTERVAL_MINUTES` en arrière-plan (serveur Node), `GET /api/cron/sync` avec `Authorization: Bearer CRON_SECRET` (planificateur externe), ou `npm run sync`.

## Stripe
Définir `STRIPE_SECRET_KEY`, `STRIPE_PRICE_PRO` (prix récurrent) et `STRIPE_WEBHOOK_SECRET`, puis pointer le webhook vers `/api/stripe/webhook` (événements `customer.subscription.*`). Sans clé, l'offre Pro n'est pas proposée.

## Qualité
```bash
npm run lint && npm run typecheck && npm test && npm run build
```
La CI (`.github/workflows/web-ci.yml`) lance aussi les migrations et deux synchronisations sur une vraie base PostgreSQL.

## Structure
- `src/lib/engine/` : logique pure (coupons, Générer / Régénérer, règlement des paris), testée avec Vitest.
- `src/lib/db/schema.ts` : schéma PostgreSQL (Drizzle), migrations dans `drizzle/`.
- `src/server/` : synchronisation, requêtes, actions serveur, offres, Stripe.
- `src/app/(public)` : accueil, connexion, inscription. `src/app/(app)` : espace membre.
