import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "OMNISCORE",
    short_name: "OMNISCORE",
    description: "Prédictions football calibrées",
    start_url: "/tableau-de-bord",
    display: "standalone",
    background_color: "#070b14",
    theme_color: "#070b14",
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml" }],
  };
}
