"""Appels HTTP JSON avec cache disque (respect des quotas des API gratuites)."""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

CACHE = Path(os.environ.get("OMNISCORE_CACHE", Path(__file__).resolve().parents[2] / "data" / "cache")) / "api"


def get_json(url: str, params: dict | None = None, headers: dict | None = None, ttl_s: float = 1800, secret_params=()) -> dict | list | None:
    """GET JSON ; renvoie la réponse en cache si elle a moins de `ttl_s` secondes, None en cas d'échec réseau.

    Les paramètres listés dans `secret_params` (clés d'API) n'entrent pas dans le nom du fichier de cache.
    """
    params = params or {}
    public = {k: v for k, v in params.items() if k not in secret_params}
    key = hashlib.sha256((url + "?" + urllib.parse.urlencode(sorted(public.items()))).encode()).hexdigest()[:24]
    path = CACHE / f"{key}.json"
    if path.exists() and time.time() - path.stat().st_mtime < ttl_s:
        return json.loads(path.read_text())
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(full, headers={"User-Agent": "omniscore/1.0", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (hôtes fixes des fournisseurs)
            data = json.loads(r.read())
    except Exception as e:  # réseau, quota, clé invalide : on garde l'ancien cache s'il existe
        print(f"[api] {url} : {e}")
        return json.loads(path.read_text()) if path.exists() else None
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data
