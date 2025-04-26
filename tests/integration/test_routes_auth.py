from fastapi import HTTPException
import pytest
from unittest.mock import ANY, MagicMock, patch
from http import HTTPStatus
from app.schemas.token import TokenResponse

class TestUserLoginEndpoint:

    @pytest.mark.parametrize(
        "user_input, mocked_response, expected_status, expected_response",
        [
            pytest.param(
                {
                    "username": "testuser",
                    "password": "SecurePass123!"
                },
                TokenResponse(
                    access_token="access_token",
                    refresh_token="refresh_token",
                    token_type="bearer"
                ),
                HTTPStatus.OK,
                {
                    "access_token": "access_token",
                    "refresh_token": "refresh_token",
                    "token_type": "bearer"
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
                    detail="Invalid credentials"
                ),
                HTTPStatus.UNAUTHORIZED,
                {
                    "detail": "Invalid credentials"
                },
                id="error_invalid_credentials"
            ),
            pytest.param(
                {
                    "username": "unverified",
                    "password": "SecurePass123!"
                },
                HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail="User not verified"
                ),
                HTTPStatus.FORBIDDEN,
                {
                    "detail": "User not verified"
                },
                id="error_unverified_user"
            ),
        ]
    )
    def test_login_user(self, client, user_input, mocked_response, expected_status, expected_response):
        with patch("app.api.routes.auth.authenticate_user") as mock_auth:
            if isinstance(mocked_response, HTTPException):
                mock_auth.side_effect = mocked_response 
            else:
                mock_auth.return_value = mocked_response 
            
            response = client.post(
                "/login",
                data=user_input,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            assert response.status_code == expected_status
            assert response.json() == expected_response

            mock_auth.assert_called_once_with(ANY, user_input["username"], user_input["password"])

class TestUserRegisterEndpoint:

    @pytest.mark.parametrize(
        "user_input, mocked_response, expected_status, expected_response",
        [
            pytest.param(
                {
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "SecurePass123!",
                    "name": "Test User"
                },
                {
                    "id": 1,
                    "email": "test@example.com",
                    "username": "testuser",
                    "name": "Test User",
                    "auth_method": "traditional",
                    "is_verified": False
                },
                HTTPStatus.CREATED,
                 {
                    "id": 1,
                    "email": "test@example.com",
                    "username": "testuser",
                    "name": "Test User",
                    "auth_method": "traditional",
                    "is_verified": False
                },
                id="ok_register"
            ),
            pytest.param(
                {
                    "email": "test@example.com",
                    "username": "anotheruser",
                    "password": "SecurePass123!",
                    "name": "Another User"
                },
                HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Email already exists" 
                ),
                HTTPStatus.BAD_REQUEST,
                {
                    "detail": "Email already exists"
                },
                id="error_email_exists"
            )

        ]
    )
    def test_register_user(self, client, user_input, mocked_response, expected_status, expected_response):
        with patch("app.api.routes.auth.register_user") as mock_register:
            if isinstance(mocked_response, HTTPException):
                mock_register.side_effect = mocked_response
            else:
                mock_register.return_value = mocked_response

            response = client.post("/register", json=user_input)

            assert response.status_code == expected_status
            assert response.json() == expected_response


    class TestSendVerificationCode:

        @pytest.mark.parametrize(
            "email, mocked_user, expected_status, expected_detail",
            [
                pytest.param(
                    "testuser@example.com",
                    MagicMock(is_verified=False),
                    200,
                    None,
                    id="success_send_verification_code"
                ),
                pytest.param(
                    "nonexistent@example.com",
                    None,
                    404,
                    "User not found",
                    id="error_user_not_found"
                ),
                pytest.param(
                    "alreadyverified@example.com",
                    MagicMock(is_verified=True),
                    400,
                    "User already verified",
                    id="error_user_already_verified"
                ),
            ]
        )
        def test_send_verification_code(self, client, email, mocked_user, expected_status, expected_detail):
            with patch("app.api.routes.auth.get_user_by_email") as mock_get_user_by_email, \
                patch("app.api.routes.auth.create_and_send_verification_code") as mock_create_and_send_verification_code:
                
                mock_get_user_by_email.return_value = mocked_user

                response = client.post("/send-verification-code", params={"email": email})

                assert response.status_code == expected_status

                if expected_status == 200:
                    json_response = response.json()
                    assert json_response["success"] is True
                    assert json_response["message"] == "Verification code sent."
                    mock_create_and_send_verification_code.assert_called_once_with(mocked_user, ANY)
                else:
                    json_response = response.json()
                    assert json_response["detail"] == expected_detail

    class TestSendResetCode:

        @pytest.mark.parametrize(
            "email, mocked_user, expected_status, expected_detail",
            [
                pytest.param(
                    "verifieduser@example.com",
                    MagicMock(is_verified=True),
                    200,
                    None,
                    id="success_send_reset_code"
                ),
                pytest.param(
                    "nonexistent@example.com",
                    None,
                    404,
                    "User not found",
                    id="error_user_not_found"
                ),
                pytest.param(
                    "unverifieduser@example.com",
                    MagicMock(is_verified=False),
                    403,
                    "You need to verify your email before resetting the password",
                    id="error_user_not_verified"
                ),
            ]
        )
        def test_send_reset_code(self, client, email, mocked_user, expected_status, expected_detail):

            with patch("app.api.routes.auth.get_user_by_email") as mock_get_user_by_email, \
                patch("app.api.routes.auth.create_and_send_reset_code") as mock_create_and_send_reset_code:
                
                mock_get_user_by_email.return_value = mocked_user

                response = client.post("/send-reset-code", params={"email": email})

                assert response.status_code == expected_status

                if expected_status == 200:
                    json_response = response.json()
                    assert json_response["success"] is True
                    assert json_response["message"] == "Reset code sent successfully"
                    mock_create_and_send_reset_code.assert_called_once_with(mocked_user, ANY)
                else:
                    json_response = response.json()
                    assert json_response["detail"] == expected_detail