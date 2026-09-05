from bson import ObjectId
from bson.errors import InvalidId

MAX_LENGTH = 256

# validni MongoDB operatori poredjenja koji se prihvataju u info_filters
COMPARISON_OPERATORS = {
    "eq",
    "ne",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "nin",
}


def missing_field(payload, field):
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


def is_number(value):
    """True za int/float, ali ne za bool (bool je podtip int u Pythonu)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def valid_price(value):
    return is_number(value) and value > 0


def valid_object_id(value):
    if not isinstance(value, str):
        return False
    try:
        ObjectId(value)
    except (InvalidId, TypeError):
        return False
    return True


def valid_categories(value):
    if not isinstance(value, list):
        return False
    for category in value:
        if not isinstance(category, str) or len(category) == 0 or len(category) > MAX_LENGTH:
            return False
    return True


def normalize_operator(operator):
    """Prihvata i "eq" i "$eq" i vraca oblik koji MongoDB ocekuje."""
    if not isinstance(operator, str) or len(operator) == 0:
        return None
    name = operator[1:] if operator.startswith("$") else operator
    if name not in COMPARISON_OPERATORS:
        return None
    return "$" + name
