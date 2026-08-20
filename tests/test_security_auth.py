import pytest
from security.auth import get_password_hash, verify_password, create_access_token
import jwt
from config.settings import settings


def test_password_hashing():
    raw_password = "SuperSecurePassword123!"
    hashed = get_password_hash(raw_password)
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_generation_and_decoding():
    payload = {"sub": "neeraj", "role": "admin"}
    token = create_access_token(payload)
    decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert decoded["sub"] == "neeraj"
    assert decoded["role"] == "admin"
