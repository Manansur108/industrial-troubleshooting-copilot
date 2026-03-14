from __future__ import annotations

import sys
from pathlib import Path
from io import BytesIO

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.main import app

client = TestClient(app)


def test_health():
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json()['status'] == 'ok'


def test_upload_ask_and_list_documents():
    files = [('files', ('sample.txt', BytesIO(b'Motor overload relay trip. Reset overload before restart. Verify safety interlock status.'), 'text/plain'))]
    upload = client.post('/api/upload', files=files)
    assert upload.status_code == 200
    payload = upload.json()
    assert payload['files']

    ask = client.post('/api/ask', json={'question': 'Why is the motor not starting?', 'top_k': 3})
    assert ask.status_code == 200
    body = ask.json()
    assert body['sources']
    assert body['recommended_actions']

    docs = client.get('/api/documents')
    assert docs.status_code == 200
    assert len(docs.json()['documents']) >= 1
