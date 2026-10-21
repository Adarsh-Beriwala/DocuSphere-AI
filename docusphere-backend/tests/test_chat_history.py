"""Tests that persistent chat turns survive reconnects and are user-scoped."""
import json
import sqlite3
import database


def test_chat_turns_persist_and_isolate_users(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'SQLITE_PATH', tmp_path / 'test.sqlite3')
    database.init_db()
    database.add_user('alice', 'alice@example.com', 'testhash')
    database.add_user('bob', 'bob@example.com', 'testhash')

    answer = {
        'answer': 'Comments begin with # [1]', 'sources': [{
            'document': 'docs.python.org/3/tutorial/introduction.html',
            'document_id': 'file1', 'excerpt': 'Comments start with a hash character #.',
            'page': None,
        }], 'confidence': 'retrieved', 'reason': 'answered', 'best_distance': 0.21,
    }
    database.save_chat_turn('alice', 'How do Python comments work?', answer)
    database.save_chat_turn('bob', 'Hello Bob?', {'answer': 'Only Bob!', 'sources': []})

    # Reopen the SQLite file through a fresh DB connection for each read.
    alice_history = database.load_chat_messages('alice')
    bob_history = database.load_chat_messages('bob')
    assert len(alice_history) == 2
    assert alice_history[0] == {'role': 'user', 'text': 'How do Python comments work?'}
    assert alice_history[1]['sources'][0]['document_id'] == 'file1'
    assert alice_history[1]['bestDistance'] == .21
    assert len(bob_history) == 2
    assert bob_history[1]['text'] == 'Only Bob!'
    assert 'Hello Bob?' not in str(alice_history)
    assert 'comments' not in str(bob_history).lower()

    database.delete_chat_history('bob')
    assert database.load_chat_messages('bob') == []
    assert database.load_chat_messages('alice') == alice_history


def test_chat_history_returns_last_100_turns_in_order(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'SQLITE_PATH', tmp_path / 'test.sqlite3')
    database.init_db()
    database.add_user('alice', 'alice@example.com', 'testhash')
    for index in range(105):
        database.save_chat_turn('alice', f'Q {index}', {'answer': f'A {index}', 'sources': []})
    items = database.load_chat_messages('alice')
    assert len(items) == 200
    assert items[0]['text'] == 'Q 5'
    assert items[-1]['text'] == 'A 104'


def test_init_db_non_destructive_migration(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'SQLITE_PATH', tmp_path / 'preexisting.sqlite3')
    database.init_db()
    database.add_user('alice', 'alice@example.com', 'testhash')
    with database.connection() as con:
        con.execute('INSERT INTO documents(id,user_id,name,kind,chunks,chunk_size) VALUES(?,?,?,?,?,?)',
                    ('pdf1', 'alice', 'existing.pdf', 'pdf', 5, 500))
    # Restart-style init_db must not drop old tables or documents.
    database.init_db()
    assert len(database.list_documents('alice')) == 1
    assert database.load_chat_messages('alice') == []
    with database.connection() as con:
        assert con.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 1
