import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./src/lib/db/schema.ts",
  out: "./drizzle",
  dialect: "postgresql",
  dbCredentials: { url: process.env.DATABASE_URL ?? process.env.POSTGRES_URL ?? "postgres://omniscore:omniscore@localhost:5432/omniscore" },
});
