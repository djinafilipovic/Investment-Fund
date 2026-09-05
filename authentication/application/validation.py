import re

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

MAX_LENGTH = 256
MIN_PASSWORD_LENGTH = 8


def missing_field(payload, field):
    """Polje je "missing" ako nije prisutno ili je string duzine 0."""
    if field not in payload:
        return True
    value = payload[field]
    if value is None:
        return True
    if isinstance(value, str) and len(value) == 0:
        return True
    return False


def first_missing(payload, fields):
    for field in fields:
        if missing_field(payload, field):
            return field
    return None


def too_long(payload, field):
    value = payload.get(field)
    return isinstance(value, str) and len(value) > MAX_LENGTH


def valid_email(email):
    return isinstance(email, str) and len(email) <= MAX_LENGTH and bool(EMAIL_PATTERN.match(email))


def valid_password(password):
    return isinstance(password, str) and MIN_PASSWORD_LENGTH <= len(password) <= MAX_LENGTH
