from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest
from app.schemas.user import UserCreate
from app.core.config import Settings
import app.api.routes.auth

app.api.routes.auth.limiter.enabled = False  # Disable rate limiting for tests

@pytest.fixture(scope="function")
def user_data():
    return UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
        name="Test User"
    )

@pytest.fixture(autouse=True, scope="session")
def mock_settings():
    with patch('app.core.config.Settings', autospec=True) as mock_settings:
        mock_settings.return_value = Settings(
            database_url="sqlite:///:memory:",
            jwt_secret_key="test-secret-key",
            jwt_algorithm="HS256",
            smtp_server="sandbox.smtp.mailtrap.io",
            smtp_port=2525,
            sender_email="test@example.com",
            sender_password="test-password"
        )
        yield mock_settings

@pytest.fixture
def client():
    from app.api.main import app
    return TestClient(app)
