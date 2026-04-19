"""
Context Store
=============
In-memory shared state store for all agents.
In production: replace with Redis or a database.
"""

from typing import Any, Dict


class ContextStore:
    def __init__(self):
        self._store: Dict[str, Dict] = {}

    def init(self, txn_id: str, data: dict):
        self._store[txn_id] = data.copy()

    def get(self, txn_id: str) -> dict:
        return self._store.get(txn_id, {})

    def update(self, txn_id: str, updates: dict):
        if txn_id not in self._store:
            self._store[txn_id] = {}
        self._store[txn_id].update(updates)

    def delete(self, txn_id: str):
        self._store.pop(txn_id, None)

    def all(self) -> dict:
        return self._store.copy()
