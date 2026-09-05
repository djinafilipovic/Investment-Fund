"""Veb servis za upravljanje korisnickim nalozima (registracija, prijava, brisanje)."""

from flask import Flask, request
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required

from application.configuration import Configuration
from application.models import Role, User, database
from application.responses import empty_ok, error, json_response
from application.validation import first_missing, too_long, valid_email, valid_password

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)
jwt = JWTManager(application)


@application.route("/register", methods=["POST"])
def register():
    payload = request.get_json(silent=True) or {}

    fields = ["forename", "surname", "email", "password"]

    missing = first_missing(payload, fields)
    if missing is not None:
        return error(f"Field {missing} is missing.")

    for field in fields:
        if too_long(payload, field):
            return error(f"Invalid {field}.")

    if not valid_email(payload["email"]):
        return error("Invalid email.")

    if not valid_password(payload["password"]):
        return error("Invalid password.")

    exists = User.query.filter(User.email == payload["email"]).first()
    if exists is not None:
        return error("Email already exists.")

    employee_role = Role.query.filter(Role.name == Configuration.ROLE_EMPLOYEE).first()
    if employee_role is None:
        employee_role = Role(name=Configuration.ROLE_EMPLOYEE)
        database.session.add(employee_role)
        database.session.flush()

    user = User(
        forename=payload["forename"],
        surname=payload["surname"],
        email=payload["email"],
        role_id=employee_role.id,
    )
    user.set_password(payload["password"])

    database.session.add(user)
    database.session.commit()

    return empty_ok()


@application.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}

    fields = ["email", "password"]

    missing = first_missing(payload, fields)
    if missing is not None:
        return error(f"Field {missing} is missing.")

    if not valid_email(payload["email"]):
        return error("Invalid email.")

    user = User.query.filter(User.email == payload["email"]).first()
    if user is None or not user.check_password(payload["password"]):
        return error("Invalid credentials.")

    access_token = create_access_token(identity=user.email, additional_claims=user.claims())
    return json_response({"accessToken": access_token})


@application.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    email = get_jwt_identity()

    user = User.query.filter(User.email == email).first()
    if user is None:
        return error("Unknown user.")

    database.session.delete(user)
    database.session.commit()

    return empty_ok()


@application.route("/health", methods=["GET"])
def health():
    return json_response({"status": "ok", "service": "authentication"})


if __name__ == "__main__":
    # debug ostaje iskljucen: ukljucen debug pokrece auto-reloader, koji bi
    # u kontejneru napravio dva procesa umesto jednog
    application.run(host="0.0.0.0", port=5000, debug=False)
