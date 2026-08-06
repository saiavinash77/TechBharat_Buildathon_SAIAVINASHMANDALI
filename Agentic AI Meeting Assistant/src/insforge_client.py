"""Minimal server-only InsForge REST client for the private meeting workflow."""

from __future__ import annotations

import os
from typing import Any

import requests


class InsForgeConfigurationError(RuntimeError):
    pass


class InsForgeRepository:
    def __init__(self, base_url: str | None = None, api_key: str | None = None, session=None):
        self.base_url = (base_url or os.getenv("INSFORGE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("INSFORGE_API_KEY", "")
        if not self.api_key or "replace_with" in self.api_key:
            import json
            from pathlib import Path
            proj_file = Path(".insforge/project.json")
            if proj_file.exists():
                try:
                    data = json.loads(proj_file.read_text(encoding="utf-8"))
                    self.api_key = data.get("api_key", self.api_key)
                    if not self.base_url:
                        self.base_url = data.get("oss_host", self.base_url).rstrip("/")
                except Exception:
                    pass
        if not self.base_url or not self.api_key or "replace_with" in self.api_key:
            raise InsForgeConfigurationError("INSFORGE_URL and server-only INSFORGE_API_KEY are required.")
        self.session = session or requests.Session()

    def _request(self, method: str, table: str, *, params=None, payload=None) -> Any:
        response = self.session.request(
            method,
            f"{self.base_url}/api/database/records/{table}",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "Prefer": "return=representation"},
            params=params,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        return response.json() if response.content else []

    def insert(self, table: str, record: dict[str, Any]) -> dict[str, Any]:
        rows = self._request("POST", table, payload=[record])
        if not rows:
            raise RuntimeError(f"InsForge did not return the inserted {table} row.")
        return rows[0]

    def get_one(self, table: str, record_id: str) -> dict[str, Any] | None:
        rows = self._request("GET", table, params={"id": f"eq.{record_id}", "limit": 1})
        return rows[0] if rows else None

    def list(self, table: str, filters: dict[str, str] | None = None, *, order: str | None = None) -> list[dict[str, Any]]:
        params = dict(filters or {})
        if order:
            params["order"] = order
        return self._request("GET", table, params=params)

    def find_one(self, table: str, filters: dict[str, str]) -> dict[str, Any] | None:
        rows = self._request("GET", table, params={**filters, "limit": 1})
        return rows[0] if rows else None

    def update(self, table: str, record_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        rows = self._request("PATCH", table, params={"id": f"eq.{record_id}"}, payload=changes)
        if not rows:
            raise RuntimeError(f"InsForge did not return the updated {table} row.")
        return rows[0]
