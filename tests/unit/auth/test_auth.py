from datetime import datetime, timedelta
import pytest
from unittest.mock import patch, MagicMock, ANY
from fastapi import HTTPException
from app.core.auth import authenticate_user
from app.schemas.token import TokenResponse
from jose import jwt
from app.core.auth import create_access_token, create_refresh_token

class TestAuthenticateUser:

    @pytest.mark.parametrize(
        "username, password, mocked_user, verify_password_return, expected_response",
        [
            pytest.param(
                "testuser",
                "SecurePass123!",
                MagicMock(id=1, username="testuser", hashed_password="hashed_password", is_verified=True),
                True,
                TokenResponse(
                    access_token="access_token",
                    refresh_token="refresh_token",
                    token_type="bearer"
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
                MagicMock(id=1, username="testuser", hashed_password="hashed_password", is_verified=True),
                False,
                HTTPException(status_code=401, detail="Invalid credentials"),
                id="error_wrong_password"
            ),
            pytest.param(
                "testuser",
                "SecurePass123!",
                MagicMock(id=1, username="testuser", hashed_password="hashed_password", is_verified=False),
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
            
            mock_get_user.return_value = mocked_user
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
                assert response.access_token == expected_response.access_token
                assert response.refresh_token == expected_response.refresh_token
                assert response.token_type == expected_response.token_type

                mock_get_user.assert_called_once_with(mock_db,username)
                if mocked_user:
                    mock_verify_password.assert_called_once_with(password, mocked_user.hashed_password)
                    if mocked_user.is_verified:
                        mock_create_access_token.assert_called_once_with(data={"sub": str(mocked_user.id)})
                        mock_create_refresh_token.assert_called_once_with(mocked_user.id, mock_db)



            
            