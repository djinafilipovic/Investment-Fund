import json

from flask import Response

JSON_MIME = "application/json"


def json_response(payload, status=200):
    return Response(json.dumps(payload), status=status, mimetype=JSON_MIME)


def empty_ok():
    """200 bez dodatnog sadrzaja."""
    return Response(status=200)


def error(message, status=400):
    return json_response({"message": message}, status)
