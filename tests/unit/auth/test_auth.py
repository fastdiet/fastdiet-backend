import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.core.auth import authenticate_user
from app.schemas.token import TokenResponse, AuthResponse, UserResponse

class TestAuthenticateUser:

    @pytest.mark.parametrize(
        "username, password, mocked_user, verify_password_return, expected_response",
        [
            pytest.param(
                "testuser",
                "SecurePass123!",
                {
                    "id": 1,
                    "username": "testuser",
                    "hashed_password": "hashed_password",
                    "is_verified": True,
                    "email": "user@example.com",
                    "name": "testuser",
                    "auth_method": "traditional"
                },
                True,
                AuthResponse(
                    tokens=TokenResponse(
                        access_token="access_token",
                        refresh_token="refresh_token",
                        token_type="bearer"
                    ),
                    user=UserResponse(
                        id=1,
                        username="testuser",
                        email="user@example.com",
                        name="testuser",
                        auth_method="traditional",
                        is_verified=True
                    ),
                ),
                id="ok_authenticate_user"
            ),
            pytest.param(
                "nonexistent",
                "SecurePass123!",
                None,
                None,
                HTTPException(status_code=401, detail="Invalid credentials"),
                id="error_user_not_found"
            ),
            pytest.param(
                "testuser",
                "WrongPassword",
                {
                    "id": 1,
                    "username": "testuser",
                    "hashed_password": "hashed_password",
                    "is_verified": True,
                    "email": "user@example.com",
                    "name": "testuser",
                    "auth_method": "traditional"
                },
                False,
                HTTPException(status_code=401, detail="Invalid credentials"),
                id="error_wrong_password"
            ),
            pytest.param(
                "testuser",
                "SecurePass123!",
                {
                    "id": 1,
                    "username": "testuser",
                    "hashed_password": "hashed_password",
                    "is_verified": False,
                    "email": "user@example.com",
                    "name": "testuser",
                    "auth_method": "traditional"
                },
                True,
                HTTPException(status_code=403, detail="User not verified"),
                id="error_user_not_verified"
            )
        ]
    )
    def test_authenticate_user(self, username, password, mocked_user, verify_password_return, expected_response):
        with patch("app.core.auth.get_user_by_username") as mock_get_user, \
             patch("app.core.auth.verify_password") as mock_verify_password, \
             patch("app.core.auth.create_access_token") as mock_create_access_token, \
             patch("app.core.auth.create_refresh_token") as mock_create_refresh_token:

            # Configurar el mock del usuario
            if mocked_user is not None:
                user = MagicMock()
                user.id = mocked_user["id"]
                user.username = mocked_user["username"]
                user.hashed_password = mocked_user["hashed_password"]
                user.is_verified = mocked_user["is_verified"]
                user.email = mocked_user["email"]
                user.name = mocked_user["name"]
                user.auth_method = mocked_user["auth_method"]
            else:
                user = None

            mock_get_user.return_value = user
            mock_verify_password.return_value = verify_password_return
            mock_create_access_token.return_value = "access_token"
            mock_create_refresh_token.return_value = "refresh_token"

            mock_db = MagicMock()

            if isinstance(expected_response, HTTPException):
                with pytest.raises(HTTPException) as exc_info:
                    authenticate_user(mock_db, username, password)
                assert exc_info.value.status_code == expected_response.status_code
                assert exc_info.value.detail == expected_response.detail
            else:
                response = authenticate_user(mock_db, username, password)
                
                assert response.tokens.access_token == expected_response.tokens.access_token
                assert response.tokens.refresh_token == expected_response.tokens.refresh_token
                assert response.tokens.token_type == expected_response.tokens.token_type
                
                assert response.user.model_dump() == expected_response.user.model_dump()

                mock_get_user.assert_called_once_with(mock_db, username)
                if user and user.is_verified and verify_password_return:
                    mock_create_access_token.assert_called_once_with(data={"sub": str(user.id)})
                    mock_create_refresh_token.assert_called_once_with(user.id, mock_db)