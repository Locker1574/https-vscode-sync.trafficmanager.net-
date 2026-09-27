import { NextResponse, type NextRequest } from "next/server";

// Vérification optimiste (présence du cookie) ; la vérification réelle est faite côté serveur par requireUser().
export function proxy(request: NextRequest) {
  if (!request.cookies.has("omniscore_session")) {
    const url = new URL("/connexion", request.url);
    url.searchParams.set("suite", request.nextUrl.pathname);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/tableau-de-bord/:path*", "/calendrier/:path*", "/match/:path*", "/coupons/:path*", "/combo/:path*",
    "/value-bets/:path*", "/favoris/:path*", "/recherche/:path*", "/performance/:path*", "/mes-coupons/:path*", "/compte/:path*"],
};
