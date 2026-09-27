// Copie les fichiers du moteur (../backend/data) dans web/data pour qu'ils soient déployés avec l'application.
import { copyFile, mkdir, stat } from "node:fs/promises";
import path from "node:path";

const src = path.resolve("../backend/data");
const dst = path.resolve("data");
const files = ["predictions.json", "track.json", "backtest.json"];

await mkdir(dst, { recursive: true });
for (const f of files) {
  try {
    await copyFile(path.join(src, f), path.join(dst, f));
  } catch (e) {
    // Sans le dossier du moteur (ex. build isolé), on garde une copie existante si elle est là.
    if (!(await stat(path.join(dst, f)).catch(() => null))) console.warn(`Attention : ${f} introuvable dans ${src} (${e.code ?? e.message}).`);
  }
}
console.log(`Données du moteur prêtes dans ${dst}.`);
