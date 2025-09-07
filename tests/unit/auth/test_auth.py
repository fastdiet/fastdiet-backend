import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.core.auth import authenticate_user

from app.schemas.token import TokenResponse, AuthResponse
from app.schemas.user import UserResponse
from app.schemas.user_preferences import UserPreferencesResponse

class TestAuthenticateUser:

    @pytest.mark.parametrize(
        "userid, password, mocked_user, verify_password_return, expected_response",
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
                    "auth_method": "traditional",
                    "gender": "male"
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
                        is_verified=True,
                        gender="male"
                    ),
                    preferences=UserPreferencesResponse(id=1, user_id=1, diet_type_id=1, goal='lose_weight')
                ),
                id="ok_authenticate_user_with_username"
            ),
            pytest.param(
                "user@expample.com",
                "SecurePass123!",
                {
                    "id": 1,
                    "username": "testuser",
                    "hashed_password": "hashed_password",
                    "is_verified": True,
                    "email": "user@example.com",
                    "name": "testuser",
                    "auth_method": "traditional",
                    "gender": "male"
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
                        is_verified=True,
                        gender="male"
                    ),
                    preferences=UserPreferencesResponse(id=1, user_id=1, diet_type_id=1, goal='lose_weight')
                ),
                id="ok_authenticate_user_with_email"
            ),
            pytest.param(
                "nonexistent",
                "SecurePass123!",
                None,
                None,
                HTTPException(
                    status_code=401,
                    detail={"code": "INVALID_CREDENTIALS", "message": "Incorrect username or password"} 
                ),
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
                    "auth_method": "traditional",
                    "gender": "male"
                },
                False,
                HTTPException(
                    status_code=401,
                    detail={"code": "INVALID_CREDENTIALS", "message": "Incorrect username or password"}
                ),
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
                    "auth_method": "traditional",
                    "gender": "male"
                },
                True,
                HTTPException(
                    status_code=403,
                    detail={"code": "USER_NOT_VERIFIED", "message": "User not verified"}
                ),
                id="error_user_not_verified"
            )
        ]
    )
    def test_authenticate_user(self, userid, password, mocked_user, verify_password_return, expected_response):

        with patch("app.core.auth.get_user_by_username") as mock_get_user_by_username, \
            patch("app.core.auth.get_user_by_email") as mock_get_user_by_email, \
            patch("app.core.auth.get_user_preferences_details") as mock_get_user_preferences, \
            patch("app.core.auth.verify_password") as mock_verify_password, \
            patch("app.core.auth.create_access_token") as mock_create_access_token, \
            patch("app.core.auth.create_refresh_token") as mock_create_refresh_token:

            user = None
            if mocked_user:
                user = MagicMock()
                for key, value in mocked_user.items():
                    setattr(user, key, value)
                setattr(user, "age", None)
                setattr(user, "weight", None)
                setattr(user, "height", None)

            if '@' in userid:
                mock_get_user_by_email.return_value = user
                mock_get_user_by_username.return_value = None
            else:
                mock_get_user_by_username.return_value = user
                mock_get_user_by_email.return_value = None

            mock_verify_password.return_value = verify_password_return
            mock_create_access_token.return_value = "access_token"
            mock_create_refresh_token.return_value = "refresh_token"

            if isinstance(expected_response, AuthResponse):
                mock_get_user_preferences.return_value = expected_response.preferences

            mock_db = MagicMock()

            if isinstance(expected_response, HTTPException):
                with pytest.raises(HTTPException) as exc_info:
                    authenticate_user(mock_db, userid, password)

                assert exc_info.value.status_code == expected_response.status_code
                assert exc_info.value.detail == expected_response.detail
            else:
                response = authenticate_user(mock_db, userid, password)
                
                assert response.tokens.model_dump() == expected_response.tokens.model_dump()
                assert response.user.model_dump() == expected_response.user.model_dump()
                assert response.preferences.model_dump() == expected_response.preferences.model_dump()

                if '@' in userid:
                    mock_get_user_by_email.assert_called_once_with(mock_db, userid)
                    mock_get_user_by_username.assert_not_called()
                else:
                    mock_get_user_by_username.assert_called_once_with(mock_db, userid)
                    mock_get_user_by_email.assert_not_called()
                
                mock_get_user_preferences.assert_called_once_with(mock_db, user.id)
                mock_create_access_token.assert_called_once_with(data={"sub": str(user.id)})
                mock_create_refresh_token.assert_called_once_with(user.id, mock_db)