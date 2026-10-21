"""FastAPI roundtrip with fake LLM response, no network or real user data."""
from fastapi.testclient import TestClient
# The offline test runner may not have the original project's password library.
# Stub it ONLY in this test process; deployed production code stays unchanged.
import sys
import types
if 'pwdlib' not in sys.modules:
    try:
        from pwdlib import PasswordHash
    except ImportError:
        fake = types.ModuleType('pwdlib')
        class PasswordHash:
            @classmethod
            def recommended(cls):
                return cls()
            def hash(self, value):
                return 'fakehashed:' + value
            def verify(self, value, hashed):
                return hashed == 'fakehashed:' + value
        fake.PasswordHash = PasswordHash
        sys.modules['pwdlib'] = fake
import main, database, auth


def test_chat_endpoints_authenticated_and_persistent(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'SQLITE_PATH', tmp_path / 'demo.sqlite3')
    monkeypatch.setattr(auth, 'JWT_SECRET', 'a-long-random-test-secret-string-longer-than-32-characters')
    monkeypatch.setattr(main, 'list_documents', lambda uid: [{'id':'test-doc'}])
    monkeypatch.setattr(main, 'answer', lambda uid, q: {
        'answer': 'Source-backed answer [1]', 'sources': [{
            'document': 'notes.pdf', 'document_id': 'test-doc', 'excerpt': 'Source-backed text'
        }], 'confidence': 'retrieved', 'reason': 'answered', 'best_distance': .15,
    })
    with TestClient(main.app) as client:
        alice = client.post('/auth/register', json={'email':'alice@example.com','password':'abc123456'}).json()
        bob = client.post('/auth/register', json={'email':'bob@example.com','password':'abc123456'}).json()
        a = {'Authorization': 'Bearer '+alice['access_token']}
        b = {'Authorization': 'Bearer '+bob['access_token']}
        assert client.get('/chat/history').status_code == 401
        assert client.get('/chat/history', headers=a).json()['messages'] == []
        result = client.post('/query', headers=a, json={'question':'Why Python?'}).json()
        assert result['confidence'] == 'retrieved'
        assert [x['role'] for x in client.get('/chat/history', headers=a).json()['messages']] == ['user','assistant']
        assert client.get('/chat/history', headers=b).json()['messages'] == []
        assert client.delete('/chat/history', headers=b).status_code == 200
        assert len(client.get('/chat/history', headers=a).json()['messages']) == 2
        assert client.delete('/chat/history', headers=a).status_code == 200
        assert client.get('/chat/history', headers=a).json()['messages'] == []
