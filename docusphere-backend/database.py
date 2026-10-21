"""Small, persistent SQLite metadata store. Chroma handles only vectors and chunks."""
import sqlite3
import json
from contextlib import contextmanager
from config import SQLITE_PATH

@contextmanager
def connection():
    con = sqlite3.connect(str(SQLITE_PATH), timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def init_db():
    with connection() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            kind TEXT NOT NULL CHECK (kind IN ('pdf', 'url')),
            original_url TEXT,
            chunks INTEGER NOT NULL,
            chunk_size INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_docs_user ON documents(user_id);
        CREATE TABLE IF NOT EXISTS chat_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            question TEXT NOT NULL,
            answer_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_chat_turns_user_id
            ON chat_turns(user_id, id DESC);
        ''')

def find_user_by_email(email):
    with connection() as db:
        row = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        return dict(row) if row else None

def find_user_by_id(user_id):
    with connection() as db:
        row = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
        return dict(row) if row else None

def add_user(user_id, email, hashed_password):
    with connection() as db:
        db.execute('INSERT INTO users(id,email,password_hash) VALUES(?,?,?)',
                   (user_id, email, hashed_password))

def list_documents(user_id):
    with connection() as db:
        rows = db.execute('''SELECT id, name, kind AS type, original_url,
            chunks, chunk_size, created_at FROM documents
            WHERE user_id=? ORDER BY created_at DESC, rowid DESC''', (user_id,)).fetchall()
        return [dict(row) for row in rows]

def find_document(user_id, doc_id):
    with connection() as db:
        row = db.execute('SELECT * FROM documents WHERE id=? AND user_id=?',
                         (doc_id, user_id)).fetchone()
        return dict(row) if row else None

def insert_document(doc_id, user_id, name, kind, url, chunks, chunk_size):
    with connection() as db:
        db.execute('''INSERT INTO documents(id,user_id,name,kind,original_url,chunks,chunk_size)
                      VALUES(?,?,?,?,?,?,?)''',
                   (doc_id, user_id, name, kind, url, chunks, chunk_size))

def remove_document(user_id, doc_id):
    with connection() as db:
        db.execute('DELETE FROM documents WHERE id=? AND user_id=?', (doc_id, user_id))


def save_chat_turn(user_id: str, question: str, answer_payload: dict):
    """Store a user question and its generated reply in one SQLite transaction."""
    serialized = json.dumps(answer_payload, ensure_ascii=False)
    with connection() as db:
        db.execute(
            'INSERT INTO chat_turns(user_id,question,answer_json) VALUES(?,?,?)',
            (user_id, question, serialized),
        )


def load_chat_messages(user_id: str, turn_limit: int = 100):
    """Most recent turns, returned oldest first, compatible with React message shape."""
    with connection() as db:
        rows = db.execute(
            'SELECT question, answer_json FROM chat_turns '
            'WHERE user_id=? ORDER BY id DESC LIMIT ?',
            (user_id, turn_limit),
        ).fetchall()
    messages = []
    for row in reversed(rows):
        payload = json.loads(row['answer_json'])
        messages.append({'role': 'user', 'text': row['question']})
        messages.append({
            'role': 'assistant',
            'text': payload.get('answer', ''),
            'sources': payload.get('sources', []),
            'confidence': payload.get('confidence'),
            'reason': payload.get('reason'),
            'bestDistance': payload.get('best_distance'),
        })
    return messages


def delete_chat_history(user_id: str):
    with connection() as db:
        db.execute('DELETE FROM chat_turns WHERE user_id=?', (user_id,))
