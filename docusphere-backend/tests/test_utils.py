import socket
import pytest
from utils import chunk_settings, validate_public_url

@pytest.mark.parametrize('n,expected', [
    (100, (150, 50)), (1999, (150, 50)), (2000, (500, 150)),
    (49999, (500, 150)), (50000, (1000, 200))
])
def test_chunk_settings(n, expected):
    assert chunk_settings(n) == expected

@pytest.mark.parametrize('url', [
    'file:///etc/passwd', 'http://127.0.0.1/private', 'http://localhost',
    'http://169.254.169.254/latest/meta-data', 'http://example.com:8080',
    'http://user:pass@example.com'
])
def test_url_rejected(url):
    with pytest.raises(ValueError):
        validate_public_url(url)

def test_public_url(monkeypatch):
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *args, **kwargs: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))])
    assert validate_public_url('https://example.com/docs') == 'https://example.com/docs'
