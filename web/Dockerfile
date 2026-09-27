FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build && npm prune --omit=dev

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production PORT=3000
COPY --from=build /app ./
EXPOSE 3000
# Applique les migrations puis démarre ; la synchronisation tourne en arrière-plan (SYNC_INTERVAL_MINUTES).
CMD ["sh", "-c", "node scripts/migrate.mjs && npx next start -p $PORT"]
