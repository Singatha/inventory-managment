from app.auth.security import create_token, decode_token, hash_password, verify_password
from app.users.models import User, UserRole


def make_user() -> User:
    user = User(
        email="employee@example.com",
        password_hash="unused",
        first_name="Test",
        last_name="Employee",
        role=UserRole.EMPLOYEE,
    )
    user.id = 42
    return user


def test_password_hashing_does_not_store_plaintext() -> None:
    password = "CorrectHorse123!"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_access_token_contains_identity_role_and_type() -> None:
    claims = decode_token(create_token(make_user(), "access"))

    assert claims["sub"] == "42"
    assert claims["role"] == "EMPLOYEE"
    assert claims["type"] == "access"
    assert claims["jti"]

