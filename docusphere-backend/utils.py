"""Pure helpers that can be tested without downloading embedding models."""
import ipaddress
import socket
from urllib.parse import urlsplit


def chunk_settings(total_chars: int) -> tuple[int, int]:
    if total_chars < 2000:
        return 150, 50
    if total_chars < 50000:
        return 500, 150
    return 1000, 200


def validate_public_url(url: str) -> str:
    """Basic SSRF guard. For an internet-facing product also add DNS pinning/network egress ACLs."""
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port  # may raise ValueError
    except ValueError as error:
        raise ValueError('Invalid URL') from error
    if (parsed.scheme not in ('http', 'https') or not hostname or parsed.username
            or parsed.password or port not in (None, 80, 443)):
        raise ValueError('Only public HTTP(S) URLs with standard ports are supported')
    if hostname.lower() in ('localhost', 'localhost.localdomain') or hostname.endswith('.local'):
        raise ValueError('Private/internal URLs are not allowed')
    try:
        addresses = socket.getaddrinfo(hostname, port or (443 if parsed.scheme == 'https' else 80),
                                       type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise ValueError('Could not resolve URL hostname') from error
    if not addresses or any(not ipaddress.ip_address(info[4][0]).is_global for info in addresses):
        raise ValueError('Private/internal IP addresses are not allowed')
    return url
