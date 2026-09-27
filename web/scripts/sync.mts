// Synchronisation manuelle : npm run sync
const { syncOnce } = await import("../src/server/sync");
const { db } = await import("../src/lib/db");
console.log(await syncOnce());
await db.$client.end();
