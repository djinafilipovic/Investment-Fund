from functools import wraps

from flask_jwt_extended import get_jwt, verify_jwt_in_request

from application.responses import json_response


def role_required(role):
    """Zahteva validan token za pristup i odgovarajucu ulogu korisnika.

    Ako zaglavlje Authorization nije prisutno, flask-jwt-extended vraca
    401 i telo {"msg": "Missing Authorization Header"}, kako je i trazeno.

    Token pogresne uloge (npr. direktorov token na servisu za zaposlene)
    tretira se isto kao izostanak zaglavlja - odgovor je 401 sa istom
    porukom, jer takav token ne predstavlja validan pristup ovom servisu.
    """

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") != role:
                return json_response({"msg": "Missing Authorization Header"}, 401)
            return function(*args, **kwargs)

        return wrapper

    return decorator
