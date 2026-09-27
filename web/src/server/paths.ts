import path from "node:path";

/**
 * Dossier des fichiers JSON du moteur : OMNISCORE_DATA_DIR s'il est défini (développement),
 * sinon web/data, rempli au build par scripts/copy-data.mjs et inclus dans le déploiement.
 */
export function dataDir() {
  const custom = process.env.OMNISCORE_DATA_DIR;
  return custom ? path.resolve(/*turbopackIgnore: true*/ process.cwd(), custom) : path.join(process.cwd(), "data");
}
