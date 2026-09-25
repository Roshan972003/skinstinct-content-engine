"""
Minimal Supabase REST (PostgREST) client — just enough for this app's three
tables. Uses `requests` directly against `${SUPABASE_URL}/rest/v1/...`
rather than the `supabase-py` package, to keep the Vercel function's
dependency surface small.
"""
from __future__ import annotations

import os
from typing import Any

import requests

TIMEOUT_SECONDS = 10


class SupabaseError(RuntimeError):
    pass


class SupabaseClient:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            raise SupabaseError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not configured")
        self.base = f"{url}/rest/v1"
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        resp = requests.post(
            f"{self.base}/{table}",
            headers={**self.headers, "Prefer": "return=representation"},
            json=row,
            timeout=TIMEOUT_SECONDS,
        )
        if not resp.ok:
            raise SupabaseError(f"insert into {table} failed: {resp.status_code} {resp.text}")
        data = resp.json()
        return data[0] if isinstance(data, list) else data

    def update(self, table: str, match: dict[str, Any], fields: dict[str, Any]) -> list[dict[str, Any]]:
        params = {f"{k}": f"eq.{v}" for k, v in match.items()}
        resp = requests.patch(
            f"{self.base}/{table}",
            headers={**self.headers, "Prefer": "return=representation"},
            params=params,
            json=fields,
            timeout=TIMEOUT_SECONDS,
        )
        if not resp.ok:
            raise SupabaseError(f"update {table} failed: {resp.status_code} {resp.text}")
        return resp.json()

    def select(self, table: str, match: dict[str, Any] | None = None, order: str | None = None,
               limit: int | None = None, select: str = "*") -> list[dict[str, Any]]:
        params: dict[str, Any] = {"select": select}
        if match:
            params.update({k: f"eq.{v}" for k, v in match.items()})
        if order:
            params["order"] = order
        if limit:
            params["limit"] = str(limit)
        resp = requests.get(f"{self.base}/{table}", headers=self.headers, params=params, timeout=TIMEOUT_SECONDS)
        if not resp.ok:
            raise SupabaseError(f"select from {table} failed: {resp.status_code} {resp.text}")
        return resp.json()
