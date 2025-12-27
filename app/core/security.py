"""
Security dependencies and utilities for API key/JWT authentication.
"""
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from jose import jwt, JWTError

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key


def get_jwt_token(credentials: HTTPAuthorizationCredentials = Security(http_bearer)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing JWT token")
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid JWT token")
