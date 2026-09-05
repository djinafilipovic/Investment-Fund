from datetime import datetime, timezone


def parse_iso_datetime(value):
    """Parsira ISO 8601 string (npr. 2026-06-08T22:12:00.000Z) u datetime u UTC."""
    if not isinstance(value, str) or len(value) == 0:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def format_iso_datetime(value):
    """Formatira datetime u ISO 8601 string sa milisekundama i Z sufiksom."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    milliseconds = value.microsecond // 1000
    return value.strftime("%Y-%m-%dT%H:%M:%S") + f".{milliseconds:03d}Z"


def serialize_asset(document):
    """Prevodi MongoDB dokument u JSON objekat prema specifikaciji."""
    asset = {
        "id": str(document["_id"]),
        "name": document.get("name"),
        "categories": document.get("categories", []),
        "buying_date": format_iso_datetime(document.get("buying_date")),
        "buying_price": document.get("buying_price"),
        "info": document.get("info", {}),
    }

    # selling_date i selling_price su prisutni jedino ako je imovina prodata
    if document.get("selling_date") is not None:
        asset["selling_date"] = format_iso_datetime(document.get("selling_date"))
    if document.get("selling_price") is not None:
        asset["selling_price"] = document.get("selling_price")

    return asset
