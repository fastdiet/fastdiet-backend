import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.schemas.user import UserRegister
from app.services.user import register_user

class TestCaseUserRegister:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.fixture
    def user_input(self):
        return UserRegister(
            email="test@example.com",
            password="Password123!",
        )

    def test_register_user_success_when_user_does_not_exist(self, mock_db, user_input):
        """Registers a new user successfully when email is unique"""

        mock_user = MagicMock(email=user_input.email)
        original_password = user_input.password
        user_input_copy = user_input.model_copy(deep=True)

        with patch("app.services.user.get_user_by_email") as mock_get_user, \
            patch("app.services.user.hash_password") as mock_hash_password, \
            patch("app.services.user.create_user") as mock_create_user:
            
            mock_get_user.return_value = None
            mock_hash_password.return_value = "hashed_password"
            mock_create_user.return_value = mock_user

            result = register_user(mock_db, user_input_copy)

            assert result == mock_user
            assert user_input_copy.password == "hashed_password"
            mock_get_user.assert_called_once_with(mock_db, user_input.email)
            mock_hash_password.assert_called_once_with(original_password)
            mock_create_user.assert_called_once_with(mock_db, user_input_copy)

    def test_register_fails_if_verified_email_exists(self, mock_db, user_input):
        """Raises HTTPException when a VERIFIED user with that email already exists."""

        existing_user = MagicMock(email=user_input.email, is_verified= True)

        with patch("app.services.user.get_user_by_email") as mock_get_user:
            mock_get_user.return_value = existing_user

            with pytest.raises(HTTPException) as exc_info:
                register_user(mock_db, user_input)

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail['code'] == 'EMAIL_ALREADY_REGISTERED'
            assert exc_info.value.detail['message'] == "Email already registered"
            mock_get_user.assert_called_once_with(mock_db, user_input.email)
    
    def test_register_updates_user_if_unverified_email_exists(self, mock_db, user_input):
        """Updates password and returns existing user if an UNVERIFIED user with that email exists."""

        existing_user = MagicMock(email=user_input.email, is_verified=False)
        original_password = user_input.password

        with patch("app.services.user.get_user_by_email") as mock_get_user, \
            patch("app.services.user.hash_password") as mock_hash_password, \
            patch("app.services.user.create_user") as mock_create_user:
            
            mock_get_user.return_value = existing_user
            mock_hash_password.return_value = "new_hashed_password"

            result = register_user(mock_db, user_input)

            assert result == existing_user
            assert existing_user.hashed_password == "new_hashed_password"
            mock_get_user.assert_called_once_with(mock_db, user_input.email)
            mock_hash_password.assert_called_once_with(original_password)
            mock_create_user.assert_not_called()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(existing_user)


    @pytest.mark.parametrize("password, expected_error", [
        ("password", "uppercase letter"),  
        ("PASSWORD123", "lowercase letter"),
        ("Password", "digit"),
        ("Password1", "special character"),
        ("", "8 characters long"),
    ])
    def test_password_validation(self, password, expected_error):
        """Raises ValueError when the password does not meet security requirements"""

        with pytest.raises(ValueError) as exc_info:
            UserRegister(
                email="test@example.com",
                password=password,
            )
        assert expected_error in str(exc_info.value)