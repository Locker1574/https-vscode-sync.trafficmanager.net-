"""Normalisation des noms d'équipes pour apparier les fournisseurs entre eux."""
from __future__ import annotations

import unicodedata

_DROP = (" fc", " cf", " afc", " sc", " ac", "fc ", "ac ", "ssc ", "as ", "rc ", "1. ", " 1901", " 1909", " 04", " calcio",
         " cfc", "sv ", " sv", "vfb ", "vfl ", "tsg ", "sl ", " club", "club ", "sporting clube de ", "futebol clube do ")


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower().replace("-", " ").replace(".", " ")
    s = f" {s} "
    for w in _DROP:
        s = s.replace(w, " ")
    return " ".join(s.split())


def same_team(a: str, b: str) -> bool:
    x, y = norm(a), norm(b)
    return x == y or (len(x) > 3 and len(y) > 3 and (x in y or y in x))
