import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Les fichiers du moteur (web/data) sont lus à l'exécution : on les inclut dans le déploiement.
  outputFileTracingIncludes: { "/**": ["./data/**"] },
};

export default nextConfig;
