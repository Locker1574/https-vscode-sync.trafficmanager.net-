import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "OMNISCORE", template: "%s · OMNISCORE" },
  description: "Prédictions football calibrées : probabilités, indice de confiance, coupons et value bets. Aucune prédiction n'est garantie.",
  applicationName: "OMNISCORE",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#070b14" },
    { media: "(prefers-color-scheme: light)", color: "#f5f7fb" },
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="fr" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
