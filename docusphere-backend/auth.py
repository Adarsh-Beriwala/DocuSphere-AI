"""Password hashing + short-lived JWT; identity is never taken from a client-supplied user_id."""
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from config import JWT_SECRET
from database import find_user_by_id

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)

def ensure_secret():
    if len(JWT_SECRET) < 32 or JWT_SECRET.startswith('replace_with'):
        raise RuntimeError('JWT_SECRET missing/too short. Copy .env.example to .env and set a 32+ char secret.')

def hash_password(password):
    return password_hash.hash(password)

def verify_password(password, stored_hash):
    return password_hash.verify(password, stored_hash)

def create_token(user_id):
    ensure_secret()
    now = datetime.now(timezone.utc)
    payload = {'sub': user_id, 'iat': now, 'exp': now + timedelta(hours=12)}
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                 detail='Not authenticated', headers={'WWW-Authenticate':'Bearer'})
    if not credentials or credentials.scheme.lower() != 'bearer':
        raise unauthorized
    ensure_secret()
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=['HS256'])
        user_id = payload.get('sub')
        if not isinstance(user_id, str) or not user_id:
            raise unauthorized
    except jwt.PyJWTError:
        raise unauthorized
    user = find_user_by_id(user_id)
    if not user:
        raise unauthorized
    return {'id': user['id'], 'email': user['email']}
