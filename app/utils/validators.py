import re


def validate_password_strength(password: str) -> str:
    errors = []

    if len(password) < 8:
        errors.append("The password must be at least 8 characters long")
    if not re.search(r'[A-Z]', password):
        errors.append("The password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append("The password must contain at least one lowercase letter")
    if not re.search(r'[0-9]', password):
        errors.append("The password must contain at least one digit")
    if not re.search(r'[^A-Za-z0-9]', password):
        errors.append("The password must contain at least one special character")

    if errors:
        raise ValueError(". ".join(errors))

    return password