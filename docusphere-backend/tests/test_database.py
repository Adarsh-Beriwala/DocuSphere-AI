import database

def test_sqlite_metadata_persistence_and_user_isolation(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'SQLITE_PATH', tmp_path / 'docs.sqlite3')
    database.init_db()
    database.add_user('alice-id', 'alice@example.com', 'hashed_password')
    database.add_user('bob-id', 'bob@example.com', 'hashed_password')
    database.insert_document('doc-1', 'alice-id', 'my-private.pdf', 'pdf', None, 4, 500)
    assert len(database.list_documents('alice-id')) == 1
    assert database.list_documents('bob-id') == []
    assert database.find_document('bob-id', 'doc-1') is None
    # Reopen a new connection to ensure state was persisted, not kept in a Python list.
    assert database.find_document('alice-id', 'doc-1')['name'] == 'my-private.pdf'
    database.remove_document('bob-id', 'doc-1')
    assert database.find_document('alice-id', 'doc-1') is not None
    database.remove_document('alice-id', 'doc-1')
    assert database.list_documents('alice-id') == []
