from fastapi import HTTPException
import pytest
from unittest.mock import ANY, patch, MagicMock
from datetime import datetime, timedelta
from app.models import User
from app.services.email_verification_code import create_and_send_verification_code, verify_user_email

class TestCaseCreateAndSendVerificationCode:

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

    def test_create_and_send_verification_code_success(self, mock_db, mock_user):
        """Should generate code, mark old codes, create new one and send email."""

        with patch("app.services.email_verification_code.generate_confirmation_code", return_value="123456") as mock_generate_code, \
             patch("app.services.email_verification_code.mark_old_verification_codes_as_used") as mock_mark_old_codes, \
             patch("app.services.email_verification_code.create_email_verification_code") as mock_create_code, \
             patch("app.services.email_verification_code.send_email") as mock_send_email:

            mock_create_code.return_value.code = "123456"

            create_and_send_verification_code(mock_user, mock_db)

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
                subject="Your confirmation code",
                body=f"Hi {mock_user.name},\n\nYour confirmation code is: 123456\nIt will expire in 15 minutes."
            )

    def test_create_code_failure(self, mock_db, mock_user):
        """Should not send email if creating verification code fails."""

        with patch("app.services.email_verification_code.generate_confirmation_code", return_value="123456"), \
            patch("app.services.email_verification_code.mark_old_verification_codes_as_used"), \
            patch("app.services.email_verification_code.create_email_verification_code", side_effect=Exception("DB error")), \
            patch("app.services.email_verification_code.send_email") as mock_send_email:

            with pytest.raises(Exception, match="DB error"):
                create_and_send_verification_code(mock_user, mock_db)

            mock_send_email.assert_not_called()

    def test_send_email_failure(self, mock_db, mock_user):
        """Should raise exception if sending email fails."""

        with patch("app.services.email_verification_code.generate_confirmation_code", return_value="123456"), \
            patch("app.services.email_verification_code.mark_old_verification_codes_as_used"), \
            patch("app.services.email_verification_code.create_email_verification_code") as mock_create_code, \
            patch("app.services.email_verification_code.send_email", side_effect=Exception("SMTP error")):

            mock_create_code.return_value.code = "123456"

            with pytest.raises(Exception, match="SMTP error"):
                create_and_send_verification_code(mock_user, mock_db)

class TestCaseVerifyUserEmail:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_user(self):
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.is_verified = False
        return user

    @pytest.fixture
    def mock_confirmation(self):
        confirmation = MagicMock()
        confirmation.used = False
        return confirmation

    def test_verify_user_email_success(self, mock_db, mock_user, mock_confirmation):
        """Should verify user email successfully."""

        with patch("app.services.email_verification_code.get_user_by_email", return_value=mock_user), \
             patch("app.services.email_verification_code.get_valid_email_verification_code", return_value=mock_confirmation):

            verify_user_email(mock_db, mock_user.email, "123456")

            assert mock_confirmation.used is True
            assert mock_user.is_verified is True
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_user)

    def test_verify_user_email_user_not_found(self, mock_db):
        """Should raise 404 if user not found."""

        with patch("app.services.email_verification_code.get_user_by_email", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                verify_user_email(mock_db, "notfound@example.com", "123456")

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "User not found"

    def test_verify_user_email_already_verified(self, mock_db, mock_user):
        """Should raise 400 if user already verified."""

        mock_user.is_verified = True

        with patch("app.services.email_verification_code.get_user_by_email", return_value=mock_user):
            with pytest.raises(HTTPException) as exc_info:
                verify_user_email(mock_db, mock_user.email, "123456")

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Email already verified"

    def test_verify_user_email_invalid_code(self, mock_db, mock_user):
        """Should raise 400 if verification code is invalid or expired."""

        with patch("app.services.email_verification_code.get_user_by_email", return_value=mock_user), \
             patch("app.services.email_verification_code.get_valid_email_verification_code", return_value=None):

            with pytest.raises(HTTPException) as exc_info:
                verify_user_email(mock_db, mock_user.email, "wrongcode")

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Invalid or expired code"