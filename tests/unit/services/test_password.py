from fastapi import HTTPException
import pytest
from unittest.mock import ANY, patch, MagicMock
from app.models import User, PasswordResetCode
from app.services.password import create_and_send_reset_code, verify_valid_reset_code, reset_user_password

class TestCaseCreateAndSendResetCode:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_user(self):
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.name = "Test User"
        user.username = "testuser"
        return user

    def test_create_and_send_reset_code_success(self, mock_db, mock_user):
        """Should generate code, mark old codes, create new one and send email."""

        with patch("app.services.password.generate_confirmation_code", return_value="123456") as mock_generate_code, \
             patch("app.services.password.mark_old_reset_codes_as_used") as mock_mark_old_codes, \
             patch("app.services.password.create_password_reset_code") as mock_create_code, \
             patch("app.services.password.send_email") as mock_send_email:

            mock_create_code.return_value.code = "123456"

            create_and_send_reset_code(mock_user, mock_db)

            mock_generate_code.assert_called_once()
            mock_mark_old_codes.assert_called_once_with(mock_db, mock_user.id)
            mock_create_code.assert_called_once_with(
                db=mock_db,
                code="123456",
                user_id=mock_user.id,
                expires_at= ANY
            )
            mock_send_email.assert_called_once_with(
                to_email=mock_user.email,
                subject="Your password reset code",
                body=f"Hi {mock_user.name},\n\nYour password reset code is: 123456\nIt will expire in 15 minutes."
            )

    def test_create_code_failure(self, mock_db, mock_user):
        """Should not send email if creating password reset code fails."""

        with patch("app.services.password.generate_confirmation_code", return_value="123456"), \
            patch("app.services.password.mark_old_reset_codes_as_used"), \
            patch("app.services.password.create_password_reset_code", side_effect=Exception("DB error")), \
            patch("app.services.password.send_email") as mock_send_email:

            with pytest.raises(Exception, match="DB error"):
                create_and_send_reset_code(mock_user, mock_db)

            mock_send_email.assert_not_called()

    def test_send_email_failure(self, mock_db, mock_user):
        """Should raise exception if sending email fails."""

        with patch("app.services.password.generate_confirmation_code", return_value="123456"), \
            patch("app.services.password.mark_old_reset_codes_as_used"), \
            patch("app.services.password.create_password_reset_code") as mock_create_code, \
            patch("app.services.password.send_email", side_effect=Exception("SMTP error")):

            mock_create_code.return_value.code = "123456"

            with pytest.raises(Exception, match="SMTP error"):
                create_and_send_reset_code(mock_user, mock_db)

class TestCaseVerifyValidResetCode:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_user(self):
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_reset_code(self):
        code = MagicMock(spec=PasswordResetCode)
        code.used = False
        return code

    def test_verify_valid_reset_code_success(self, mock_db, mock_user, mock_reset_code):
        """Should return user and reset code if valid."""

        with patch("app.services.password.get_user_by_email", return_value=mock_user), \
             patch("app.services.password.get_valid_password_reset_code", return_value=mock_reset_code):

            user, reset_code = verify_valid_reset_code(mock_db, mock_user.email, "123456")

            assert user == mock_user
            assert reset_code == mock_reset_code

    def test_verify_valid_reset_code_user_not_found(self, mock_db):
        """Should raise 404 if user not found."""

        with patch("app.services.password.get_user_by_email", return_value=None):

            with pytest.raises(HTTPException) as exc_info:
                verify_valid_reset_code(mock_db, "notfound@example.com", "123456")

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "User not found"

    def test_verify_valid_reset_code_invalid_code(self, mock_db, mock_user):
        """Should raise 400 if reset code invalid or expired."""

        with patch("app.services.password.get_user_by_email", return_value=mock_user), \
             patch("app.services.password.get_valid_password_reset_code", return_value=None):

            with pytest.raises(HTTPException) as exc_info:
                verify_valid_reset_code(mock_db, mock_user.email, "wrongcode")

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Invalid or expired reset code"

class TestCaseResetUserPassword:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_user(self):
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_reset_code(self):
        code = MagicMock(spec=PasswordResetCode)
        code.used = False
        return code

    def test_reset_user_password_success(self, mock_db, mock_user, mock_reset_code):
        """Should reset user's password and mark code as used."""

        with patch("app.services.password.verify_valid_reset_code", return_value=(mock_user, mock_reset_code)), \
             patch("app.services.password.hash_password", return_value="new_hashed_password"):

            reset_user_password(mock_db, mock_user.email, "123456", "NewPassword!123")

            assert mock_user.hashed_password == "new_hashed_password"
            assert mock_reset_code.used is True
            mock_db.commit.assert_called_once()

    def test_reset_user_password_invalid_reset_code(self, mock_db):
        """Should raise exception if reset code verification fails."""

        with patch("app.services.password.verify_valid_reset_code", side_effect=HTTPException(status_code=400, detail="Invalid or expired reset code")):

            with pytest.raises(HTTPException) as exc_info:
                reset_user_password(mock_db, "test@example.com", "wrongcode", "NewPassword!123")

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Invalid or expired reset code"