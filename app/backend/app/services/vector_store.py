from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from app.backend.app.core.config import PROCESSED_DIR

STORE_PATH = PROCESSED_DIR / 'documents_store.json'


class LocalVectorStore:
    def __init__(self, store_path: Path = STORE_PATH):
        self.store_path = store_path
        self._db = self._load()

    def _load(self) -> dict[str, Any]:
        if self.store_path.exists():
            return json.loads(self.store_path.read_text())
        return {'documents': {}, 'chunks': []}

    def _save(self) -> None:
        self.store_path.write_text(json.dumps(self._db, indent=2))

    def upsert_document(self, document: dict, chunks: list[dict]) -> None:
        self._db['documents'][document['document_id']] = document
        self._db['chunks'] = [c for c in self._db['chunks'] if c['document_id'] != document['document_id']]
        for chunk in chunks:
            enriched = {**chunk, 'document_id': document['document_id'], 'file_name': document['file_name']}
            enriched['tf'] = self._term_freq(enriched['text'])
            self._db['chunks'].append(enriched)
        self._save()

    def list_documents(self) -> list[dict]:
        return list(self._db['documents'].values())

    def delete_document(self, document_id: str) -> bool:
        existed = document_id in self._db['documents']
        self._db['documents'].pop(document_id, None)
        self._db['chunks'] = [c for c in self._db['chunks'] if c['document_id'] != document_id]
        self._save()
        return existed

    def get_document(self, document_id: str) -> dict | None:
        return self._db['documents'].get(document_id)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        qtf = self._term_freq(query)
        scored: list[dict] = []
        for chunk in self._db['chunks']:
            score = self._cosine(qtf, chunk.get('tf', {}))
            if score > 0:
                scored.append({**chunk, 'score': round(score, 4)})
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _term_freq(text: str) -> dict[str, int]:
        tokens = re.findall(r'[a-zA-Z0-9_\-]+', (text or '').lower())
        return dict(Counter(tokens))

    @staticmethod
    def _cosine(a: dict[str, int], b: dict[str, int]) -> float:
        if not a or not b:
            return 0.0
        common = set(a) & set(b)
        dot = sum(a[k] * b[k] for k in common)
        an = math.sqrt(sum(v * v for v in a.values()))
        bn = math.sqrt(sum(v * v for v in b.values()))
        if not an or not bn:
            return 0.0
        return dot / (an * bn)
