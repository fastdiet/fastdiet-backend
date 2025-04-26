import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.schemas.user import UserCreate
from app.services.user import register_user

class TestCaseUserRegister:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.fixture
    def user_input(self):
        return UserCreate(
            email="test@example.com",
            username="testuser",
            password="Password123!",
            name="Test User"
        )

    def test_register_user_success(self, mock_db, user_input):
        """Registers a new user successfully when email and username are unique"""

        mock_user = MagicMock(email=user_input.email, username=user_input.username)
        original_password = user_input.password
        user_input_copy = user_input.model_copy(deep=True)

        with patch("app.services.user.get_user_by_username_or_email") as mock_get_user, \
             patch("app.services.user.hash_password") as mock_hash_password, \
             patch("app.services.user.create_user") as mock_create_user:
            
            mock_get_user.return_value = None
            mock_hash_password.return_value = "hashed_password"
            mock_create_user.return_value = mock_user

            result = register_user(mock_db, user_input_copy)

            assert result == mock_user
            assert user_input_copy.password == "hashed_password"
            assert user_input_copy.password != original_password
            mock_get_user.assert_called_once_with(mock_db, user_input.email, user_input.username)
            mock_hash_password.assert_called_once_with(original_password)
            mock_create_user.assert_called_once_with(mock_db, user_input_copy)

    def test_email_exists(self, mock_db, user_input):
        """Raises HTTPException when the email is already registered"""

        existing_user = MagicMock(email=user_input.email, username="differentusername")

        with patch("app.services.user.get_user_by_username_or_email") as mock_get_user:
            mock_get_user.return_value = existing_user

            with pytest.raises(HTTPException) as excinfo:
                register_user(mock_db, user_input)

            assert excinfo.value.status_code == 400
            assert excinfo.value.detail == "Email already registered"
            mock_get_user.assert_called_once_with(mock_db, user_input.email, user_input.username)


    def test_username_exists(self, mock_db, user_input):
        """Raises HTTPException when the username is already taken"""
    
        existing_user = MagicMock(email="different@example.com", username=user_input.username)

        with patch("app.services.user.get_user_by_username_or_email") as mock_get_user:
            mock_get_user.return_value = existing_user

            with pytest.raises(HTTPException) as excinfo:
                register_user(mock_db, user_input)

            assert excinfo.value.status_code == 400
            assert excinfo.value.detail == "Username already taken"
            mock_get_user.assert_called_once_with(mock_db, user_input.email, user_input.username)

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
            UserCreate(
                username="testuser",
                email="test@example.com",
                password=password,
                name="Test User"
            )
        assert expected_error in str(exc_info.value)