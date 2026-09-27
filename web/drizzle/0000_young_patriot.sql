CREATE TABLE "coupon_items" (
	"coupon_id" uuid NOT NULL,
	"match_id" text NOT NULL,
	"key" text NOT NULL,
	"match" text NOT NULL,
	"label" text NOT NULL,
	"p" double precision NOT NULL,
	"confidence" double precision NOT NULL,
	"odds" double precision NOT NULL,
	"status" text,
	CONSTRAINT "coupon_items_coupon_id_match_id_key_pk" PRIMARY KEY("coupon_id","match_id","key")
);
--> statement-breakpoint
CREATE TABLE "coupons" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"kind" text NOT NULL,
	"mode" text NOT NULL,
	"pmin" double precision NOT NULL,
	"combined_probability" double precision NOT NULL,
	"total_odds" double precision NOT NULL,
	"status" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "favorites" (
	"user_id" uuid NOT NULL,
	"kind" text NOT NULL,
	"ref" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "favorites_user_id_kind_ref_pk" PRIMARY KEY("user_id","kind","ref")
);
--> statement-breakpoint
CREATE TABLE "generations" (
	"id" serial PRIMARY KEY NOT NULL,
	"user_id" uuid NOT NULL,
	"action" text NOT NULL,
	"params" jsonb NOT NULL,
	"result" jsonb NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "leagues" (
	"code" text PRIMARY KEY NOT NULL,
	"name" text NOT NULL
);
--> statement-breakpoint
CREATE TABLE "matches" (
	"id" text PRIMARY KEY NOT NULL,
	"league" text NOT NULL,
	"date" text NOT NULL,
	"time" text,
	"round" text,
	"home" text NOT NULL,
	"away" text NOT NULL,
	"xg_home" double precision,
	"xg_away" double precision,
	"elo_home" integer,
	"elo_away" integer,
	"model_agreement" double precision,
	"data_completeness" double precision,
	"score_home" integer,
	"score_away" integer,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "odds_snapshots" (
	"id" serial PRIMARY KEY NOT NULL,
	"match_id" text NOT NULL,
	"key" text NOT NULL,
	"odds" double precision NOT NULL,
	"bookmaker" text,
	"taken_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "prediction_snapshots" (
	"id" serial PRIMARY KEY NOT NULL,
	"match_id" text NOT NULL,
	"generated" text NOT NULL,
	"markets" jsonb NOT NULL,
	"taken_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "predictions" (
	"match_id" text NOT NULL,
	"key" text NOT NULL,
	"group" text NOT NULL,
	"label" text NOT NULL,
	"p" double precision NOT NULL,
	"confidence" double precision NOT NULL,
	"fair_odds" double precision NOT NULL,
	"odds" double precision,
	"bookmaker" text,
	"value" double precision,
	"status" text,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "predictions_match_id_key_pk" PRIMARY KEY("match_id","key")
);
--> statement-breakpoint
CREATE TABLE "subscriptions" (
	"id" text PRIMARY KEY NOT NULL,
	"user_id" uuid NOT NULL,
	"status" text NOT NULL,
	"price_id" text,
	"current_period_end" timestamp with time zone,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "sync_runs" (
	"id" serial PRIMARY KEY NOT NULL,
	"source" text NOT NULL,
	"generated" text,
	"matches" integer DEFAULT 0 NOT NULL,
	"changed" integer DEFAULT 0 NOT NULL,
	"odds_moves" integer DEFAULT 0 NOT NULL,
	"settled" integer DEFAULT 0 NOT NULL,
	"ok" boolean DEFAULT true NOT NULL,
	"error" text,
	"started_at" timestamp with time zone DEFAULT now() NOT NULL,
	"finished_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "tracked_picks" (
	"match_id" text PRIMARY KEY NOT NULL,
	"league" text NOT NULL,
	"date" text NOT NULL,
	"home" text NOT NULL,
	"away" text NOT NULL,
	"frozen" text NOT NULL,
	"key" text,
	"label" text,
	"p" double precision,
	"status" text,
	"score_home" integer,
	"score_away" integer
);
--> statement-breakpoint
CREATE TABLE "users" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"email" text NOT NULL,
	"name" text NOT NULL,
	"password_hash" text NOT NULL,
	"plan" text DEFAULT 'free' NOT NULL,
	"stripe_customer_id" text,
	"paused_until" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "users_email_unique" UNIQUE("email"),
	CONSTRAINT "users_stripe_customer_id_unique" UNIQUE("stripe_customer_id")
);
--> statement-breakpoint
ALTER TABLE "coupon_items" ADD CONSTRAINT "coupon_items_coupon_id_coupons_id_fk" FOREIGN KEY ("coupon_id") REFERENCES "public"."coupons"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "coupons" ADD CONSTRAINT "coupons_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "favorites" ADD CONSTRAINT "favorites_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "generations" ADD CONSTRAINT "generations_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "matches" ADD CONSTRAINT "matches_league_leagues_code_fk" FOREIGN KEY ("league") REFERENCES "public"."leagues"("code") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "odds_snapshots" ADD CONSTRAINT "odds_snapshots_match_id_matches_id_fk" FOREIGN KEY ("match_id") REFERENCES "public"."matches"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "prediction_snapshots" ADD CONSTRAINT "prediction_snapshots_match_id_matches_id_fk" FOREIGN KEY ("match_id") REFERENCES "public"."matches"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "predictions" ADD CONSTRAINT "predictions_match_id_matches_id_fk" FOREIGN KEY ("match_id") REFERENCES "public"."matches"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "subscriptions" ADD CONSTRAINT "subscriptions_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "coupons_user_idx" ON "coupons" USING btree ("user_id","created_at");--> statement-breakpoint
CREATE INDEX "matches_date_idx" ON "matches" USING btree ("date");--> statement-breakpoint
CREATE INDEX "matches_teams_idx" ON "matches" USING gin (to_tsvector('simple', "home" || ' ' || "away"));--> statement-breakpoint
CREATE INDEX "odds_match_idx" ON "odds_snapshots" USING btree ("match_id","key","taken_at");--> statement-breakpoint
CREATE INDEX "snap_match_idx" ON "prediction_snapshots" USING btree ("match_id","taken_at");--> statement-breakpoint
CREATE INDEX "predictions_p_idx" ON "predictions" USING btree ("p");