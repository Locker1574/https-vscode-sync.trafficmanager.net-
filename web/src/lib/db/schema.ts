import { sql } from "drizzle-orm";
import {
  boolean,
  doublePrecision,
  index,
  integer,
  jsonb,
  pgTable,
  primaryKey,
  serial,
  text,
  timestamp,
  uuid,
} from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: uuid("id").primaryKey().defaultRandom(),
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  passwordHash: text("password_hash").notNull(),
  plan: text("plan").notNull().default("free"), // free | pro
  stripeCustomerId: text("stripe_customer_id").unique(),
  // Jeu responsable : pause volontaire jusqu'à cette date.
  pausedUntil: timestamp("paused_until", { withTimezone: true }),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const subscriptions = pgTable("subscriptions", {
  id: text("id").primaryKey(), // identifiant Stripe
  userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  status: text("status").notNull(),
  priceId: text("price_id"),
  currentPeriodEnd: timestamp("current_period_end", { withTimezone: true }),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

export const leagues = pgTable("leagues", {
  code: text("code").primaryKey(),
  name: text("name").notNull(),
});

export const matches = pgTable(
  "matches",
  {
    id: text("id").primaryKey(),
    league: text("league").notNull().references(() => leagues.code),
    date: text("date").notNull(), // AAAA-MM-JJ
    time: text("time"),
    round: text("round"),
    home: text("home").notNull(),
    away: text("away").notNull(),
    xgHome: doublePrecision("xg_home"),
    xgAway: doublePrecision("xg_away"),
    eloHome: integer("elo_home"),
    eloAway: integer("elo_away"),
    modelAgreement: doublePrecision("model_agreement"),
    dataCompleteness: doublePrecision("data_completeness"),
    scoreHome: integer("score_home"),
    scoreAway: integer("score_away"),
    updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [
    index("matches_date_idx").on(t.date),
    index("matches_teams_idx").using("gin", sql`to_tsvector('simple', ${t.home} || ' ' || ${t.away})`),
  ],
);

/** Valeur courante de chaque marché ; l'historique est dans prediction_snapshots et odds_snapshots. */
export const predictions = pgTable(
  "predictions",
  {
    matchId: text("match_id").notNull().references(() => matches.id, { onDelete: "cascade" }),
    key: text("key").notNull(),
    group: text("group").notNull(),
    label: text("label").notNull(),
    p: doublePrecision("p").notNull(),
    confidence: doublePrecision("confidence").notNull(),
    fairOdds: doublePrecision("fair_odds").notNull(),
    odds: doublePrecision("odds"),
    bookmaker: text("bookmaker"),
    value: doublePrecision("value"),
    status: text("status"), // V validé, P perdu, R remboursé
    updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [primaryKey({ columns: [t.matchId, t.key] }), index("predictions_p_idx").on(t.p)],
);

/** Historique append-only : rien n'est jamais écrasé. */
export const predictionSnapshots = pgTable(
  "prediction_snapshots",
  {
    id: serial("id").primaryKey(),
    matchId: text("match_id").notNull().references(() => matches.id, { onDelete: "cascade" }),
    generated: text("generated").notNull(),
    markets: jsonb("markets").notNull(),
    takenAt: timestamp("taken_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [index("snap_match_idx").on(t.matchId, t.takenAt)],
);

export const oddsSnapshots = pgTable(
  "odds_snapshots",
  {
    id: serial("id").primaryKey(),
    matchId: text("match_id").notNull().references(() => matches.id, { onDelete: "cascade" }),
    key: text("key").notNull(),
    odds: doublePrecision("odds").notNull(),
    bookmaker: text("bookmaker"),
    takenAt: timestamp("taken_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [index("odds_match_idx").on(t.matchId, t.key, t.takenAt)],
);

/** Prédiction figée avant le match par le moteur (journal réel) et son statut une fois réglée. */
export const trackedPicks = pgTable("tracked_picks", {
  matchId: text("match_id").primaryKey(),
  league: text("league").notNull(),
  date: text("date").notNull(),
  home: text("home").notNull(),
  away: text("away").notNull(),
  frozen: text("frozen").notNull(),
  key: text("key"),
  label: text("label"),
  p: doublePrecision("p"),
  status: text("status"),
  scoreHome: integer("score_home"),
  scoreAway: integer("score_away"),
});

export const favorites = pgTable(
  "favorites",
  {
    userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
    kind: text("kind").notNull(), // match | team | league
    ref: text("ref").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [primaryKey({ columns: [t.userId, t.kind, t.ref] })],
);

export const coupons = pgTable(
  "coupons",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
    kind: text("kind").notNull(), // jour | combo
    mode: text("mode").notNull(),
    pmin: doublePrecision("pmin").notNull(),
    combinedProbability: doublePrecision("combined_probability").notNull(),
    totalOdds: doublePrecision("total_odds").notNull(),
    status: text("status"), // V | P | R | null (en attente)
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [index("coupons_user_idx").on(t.userId, t.createdAt)],
);

export const couponItems = pgTable(
  "coupon_items",
  {
    couponId: uuid("coupon_id").notNull().references(() => coupons.id, { onDelete: "cascade" }),
    matchId: text("match_id").notNull(),
    key: text("key").notNull(),
    match: text("match").notNull(),
    label: text("label").notNull(),
    p: doublePrecision("p").notNull(),
    confidence: doublePrecision("confidence").notNull(),
    odds: doublePrecision("odds").notNull(),
    status: text("status"),
  },
  (t) => [primaryKey({ columns: [t.couponId, t.matchId, t.key] })],
);

/** Historique de chaque clic Générer / Régénérer. */
export const generations = pgTable("generations", {
  id: serial("id").primaryKey(),
  userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  action: text("action").notNull(), // generate | regenerate
  params: jsonb("params").notNull(),
  result: jsonb("result").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

/** Chaque synchronisation ; l'id sert de numéro de version pour le temps réel. */
export const syncRuns = pgTable("sync_runs", {
  id: serial("id").primaryKey(),
  source: text("source").notNull(),
  generated: text("generated"),
  matches: integer("matches").notNull().default(0),
  changed: integer("changed").notNull().default(0),
  oddsMoves: integer("odds_moves").notNull().default(0),
  settled: integer("settled").notNull().default(0),
  ok: boolean("ok").notNull().default(true),
  error: text("error"),
  startedAt: timestamp("started_at", { withTimezone: true }).notNull().defaultNow(),
  finishedAt: timestamp("finished_at", { withTimezone: true }),
});

export type Match = typeof matches.$inferSelect;
export type Prediction = typeof predictions.$inferSelect;
export type User = typeof users.$inferSelect;
