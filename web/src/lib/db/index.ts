import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";

const globalForDb = globalThis as unknown as { pool?: Pool };

// Une seule connexion partagée, y compris entre les rechargements à chaud en développement.
const pool =
  globalForDb.pool ??
  new Pool({ connectionString: process.env.DATABASE_URL ?? process.env.POSTGRES_URL, max: Number(process.env.DATABASE_POOL_MAX ?? 10) });
if (process.env.NODE_ENV !== "production") globalForDb.pool = pool;

export const db = drizzle(pool, { schema });
export { schema };
