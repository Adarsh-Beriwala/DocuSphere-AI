from types import SimpleNamespace
import rag

class FakeStore:
    def __init__(self, distance):
        self.distance = distance
        self.calls = []

    def similarity_search_with_score(self, query, k, filter):
        self.calls.append((query, k, filter))
        doc = SimpleNamespace(page_content='Students need 75 percent attendance.',
                              metadata={'document_id': 'doc1', 'chunk_index': 0,
                                        'source': 'policy.pdf', 'page': 3})
        return [(doc, self.distance)]

class FakeLLM:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return SimpleNamespace(content=self.reply)

def test_low_cosine_distance_keeps_chunk_and_enforces_owner(monkeypatch):
    store = FakeStore(0.15)
    model = FakeLLM('Minimum attendance is 75% [1].')
    monkeypatch.setattr(rag, 'vectorstore', lambda: store)
    monkeypatch.setattr(rag, 'llm', lambda: model)
    monkeypatch.setattr(rag, 'ENABLE_QUERY_REWRITE', False)
    monkeypatch.setattr(rag, 'COSINE_DISTANCE_CUTOFF', 0.65)
    output = rag.answer('alice-id', 'What is minimum attendance?')
    assert output['confidence'] == 'retrieved'
    assert output['reason'] == 'answered'
    assert output['best_distance'] == 0.15
    assert output['sources'][0]['page'] == 3
    assert store.calls == [('What is minimum attendance?', rag.RETRIEVAL_K, {'user_id': 'alice-id'})]
    assert 'Students need 75 percent attendance' in model.calls[0][1][1]

def test_high_cosine_distance_rejected_without_generation(monkeypatch):
    store = FakeStore(0.91)
    model = FakeLLM('This should never be called')
    monkeypatch.setattr(rag, 'vectorstore', lambda: store)
    monkeypatch.setattr(rag, 'llm', lambda: model)
    monkeypatch.setattr(rag, 'ENABLE_QUERY_REWRITE', False)
    monkeypatch.setattr(rag, 'COSINE_DISTANCE_CUTOFF', 0.65)
    output = rag.answer('bob-id', 'Unrelated question')
    assert output['confidence'] == 'no_match'
    assert output['reason'] == 'distance_gate'
    assert output['best_distance'] == 0.91
    assert not model.calls

def test_model_abstention_reports_no_match(monkeypatch):
    monkeypatch.setattr(rag, 'vectorstore', lambda: FakeStore(0.05))
    monkeypatch.setattr(rag, 'llm', lambda: FakeLLM(rag.FALLBACK))
    monkeypatch.setattr(rag, 'ENABLE_QUERY_REWRITE', False)
    output = rag.answer('alice-id', 'Question with no factual answer')
    assert output['confidence'] == 'no_match'
    assert len(output['sources']) == 1  # Debugging evidence remains visible even when model abstains.
    assert output['sources'][0]['document'] == 'policy.pdf'
    assert output['reason'] == 'llm_abstained'
