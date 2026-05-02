import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from google.cloud import firestore


class FirestoreTTLCache:
    def __init__(
        self,
        collection_name: str | None = None,
        client: firestore.Client | None = None,
    ) -> None:
        self._client = client or firestore.Client()
        self._collection = self._client.collection(
            collection_name or os.getenv("FIRESTORE_CACHE_COLLECTION", "api_news")
        )

    def _document_id(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _document(self, key: str):
        return self._collection.document(self._document_id(key))

    def _get_entry(self, key: str) -> tuple[Any | None, datetime | None]:
        snapshot = self._document(key).get()
        if not snapshot.exists:
            return None, None

        payload = snapshot.to_dict() or {}
        expires_at = payload.get("expires_at")
        value = payload.get("value")
        return value, expires_at

    def get(self, key: str) -> Any | None:
        value, expires_at = self._get_entry(key)
        if value is None:
            return None

        if expires_at is None:
            return value

        if expires_at <= datetime.now(timezone.utc):
            return None

        return value

    def get_stale(self, key: str) -> Any | None:
        value, _ = self._get_entry(key)
        return value

    def set(self, key: str, value: Any, ttl_hours: int | None) -> None:
        now = datetime.now(timezone.utc)
        expires_at = None if ttl_hours is None else now + timedelta(hours=ttl_hours)
        self._document(key).set(
            {
                "key": key,
                "value": value,
                "created_at": now,
                "expires_at": expires_at,
            }
        )

    def delete(self, key: str) -> None:
        self._document(key).delete()
