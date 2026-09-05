import uuid as uuid_module

from bson import ObjectId
from bson.errors import InvalidId


def missing_field(payload, field):
    if field not in payload:
        return True
    value = payload[field]
    if value is None:
        return True
    if isinstance(value, str) and len(value) == 0:
        return True
    return False


def valid_uuid(value):
    if not isinstance(value, str):
        return False
    try:
        uuid_module.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return True


def valid_object_id(value):
    if not isinstance(value, str):
        return False
    try:
        ObjectId(value)
    except (InvalidId, TypeError):
        return False
    return True
