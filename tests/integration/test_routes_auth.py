from fastapi import HTTPException
import pytest
from unittest.mock import ANY, MagicMock, patch
from http import HTTPStatus
from app.schemas.token import AuthResponse, TokenResponse
from app.schemas.user import UserResponse

class TestUserLoginEndpoint:

    @pytest.mark.parametrize(
        "user_input, mocked_service_response, expected_status, expected_json_response",
        [
            pytest.param(
                { "username": "testuser", "password": "SecurePass123!" },
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
                        age=None,
                        gender=None,
                        weight=None,
                        height=None
                    ),
                    preferences=None
                ),
                HTTPStatus.OK,
                {
                    "tokens": {
                        "access_token": "access_token",
                        "refresh_token": "refresh_token",
                        "token_type": "bearer"
                    },
                    "user": {
                        "id": 1,
                        "username": "testuser",
                        "email": "user@example.com",
                        "name": "testuser",
                        "auth_method": "traditional",
                        "is_verified": True,
                        "age": None,
                        "gender": None,
                        "weight": None,
                        "height": None
                    },
                    "preferences": None
                },
                id="ok_login"
            ),
            pytest.param(
                {
                    "username": "nonexistent",
                    "password": "Wrongpassword!123"
                },
                HTTPException(
                    status_code=HTTPStatus.UNAUTHORIZED,
                    detail={"code": "INVALID_CREDENTIALS", "message": "Incorrect username or password"}
                ),
                HTTPStatus.UNAUTHORIZED,
                {"detail": {"code": "INVALID_CREDENTIALS", "message": "Incorrect username or password"}},
                id="error_invalid_credentials"
            ),
            pytest.param(
                {
                    "username": "unverified",
                    "password": "SecurePass123!"
                },
                HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail={"code": "USER_NOT_VERIFIED", "message": "User not verified"}
                ),
                HTTPStatus.FORBIDDEN,
                {"detail": {"code": "USER_NOT_VERIFIED", "message": "User not verified"}},
                id="error_unverified_user"
            ),
        ]
    )
    def test_login_user(self, client, user_input, mocked_service_response, expected_status, expected_json_response):
        with patch("app.api.routes.auth.authenticate_user") as mock_auth:
            if isinstance(mocked_service_response, HTTPException):
                mock_auth.side_effect = mocked_service_response 
            else:
                mock_auth.return_value = mocked_service_response 
            
            response = client.post(
                "/login",
                data=user_input,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            assert response.status_code == expected_status
            assert response.json() == expected_json_response

            mock_auth.assert_called_once_with(ANY, user_input["username"], user_input["password"])

class TestUserRegisterEndpoint:

    @pytest.mark.parametrize(
        "user_input, mocked_service_response, expected_status, expected_json_response",
        [
            pytest.param(
                {"email": "test@example.com", "password": "SecurePass123!"},
                UserResponse(
                    id=1,
                    email="test@example.com",
                    username=None,
                    name=None,
                    auth_method="traditional",
                    is_verified=False,
                    age=None,
                    gender=None,
                    weight=None,
                    height=None
                ),
                HTTPStatus.CREATED,
                {"id": 1, "email": "test@example.com", "username": None, "name": None, "age": None, "gender": None, "weight": None, "height": None, "auth_method": "traditional", "is_verified": False},
                id="ok_register"
            ),
            pytest.param(
                {"email": "exists@example.com", "password": "SecurePass123!"},
                HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail={"code": "EMAIL_ALREADY_REGISTERED", "message": "Email already registered"} 
                ),
                HTTPStatus.BAD_REQUEST,
                {"detail": {"code": "EMAIL_ALREADY_REGISTERED", "message": "Email already registered"}},
                id="error_email_exists"
            )
        ]
    )
    def test_register_user(self, client, user_input, mocked_service_response, expected_status, expected_json_response):
        with patch("app.api.routes.auth.register_user") as mock_register:
            if isinstance(mocked_service_response, HTTPException):
                mock_register.side_effect = mocked_service_response
            else:
                mock_register.return_value = mocked_service_response

            response = client.post("/register", json=user_input)

            assert response.status_code == expected_status
            assert response.json() == expected_json_response


class TestSendVerificationCode:
    @pytest.mark.parametrize("email, mocked_user_lookup, expected_status, expected_json_response",
        [
            pytest.param(
                "new@example.com",
                MagicMock(is_verified=False),
                200,
                {"success": True, "message": "Verification code sent"},
                id="success"
            ),
            pytest.param(
                "notfound@example.com",
                None,
                404,
                {"detail": {"code": "USER_NOT_FOUND", "message": "User not found"}},
                id="error_not_found"
            ),
            pytest.param(
                "verified@example.com",
                MagicMock(is_verified=True),
                400,
                {"detail": {"code": "USER_ALREADY_VERIFIED", "message": "User already verified"}},
                id="error_already_verified"
            ),
        ]
    )
    def test_send_verification_code(self, client, email, mocked_user_lookup, expected_status, expected_json_response):
        with patch("app.api.routes.auth.get_user_by_email") as mock_get_user, \
            patch("app.api.routes.auth.create_and_send_verification_code") as mock_send_code:
            
            mock_get_user.return_value = mocked_user_lookup
            
            response = client.post("/send-verification-code", json={"email": email})

            assert response.status_code == expected_status
            assert response.json() == expected_json_response

            if expected_status == 200:
                mock_send_code.assert_called_once_with(mocked_user_lookup, ANY, ANY)

class TestSendResetCode:

    @pytest.mark.parametrize("email, mocked_user_lookup, expected_status, expected_json_response",
        [
            pytest.param(
                "verified@example.com",
                MagicMock(is_verified=True),
                200,
                {"success": True, "message": "Reset code sent successfully"},
                id="success"
            ),
            pytest.param(
                "notfound@example.com",
                None,
                404,
                {"detail": {"code": "USER_NOT_FOUND", "message": "User not found"}},
                id="error_not_found"
            ),
            pytest.param(
                "unverified@example.com",
                MagicMock(is_verified=False),
                403,
                {"detail": {"code": "USER_NOT_VERIFIED_FOR_RESET", "message": "You need to verify your email before resetting the password"}},
                id="error_not_verified"
            ),
        ]
    )
    def test_send_reset_code(self, client, email, mocked_user_lookup, expected_status, expected_json_response):
        with patch("app.api.routes.auth.get_user_by_email") as mock_get_user, \
            patch("app.api.routes.auth.create_and_send_reset_code") as mock_send_code:
            
            mock_get_user.return_value = mocked_user_lookup

            response = client.post("/send-reset-code", json={"email": email})

            assert response.status_code == expected_status
            assert response.json() == expected_json_response

            if expected_status == 200:
                mock_send_code.assert_called_once_with(mocked_user_lookup, ANY, ANY)