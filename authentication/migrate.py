"""Inicijalizacija relacione baze podataka.

Kreira sve potrebne tabele, uloge i pocetni nalog direktora fonda.
Skript je idempotentan i moze se pokretati vise puta.
Pokrece se kao initContainer u okviru Kubernetes deployment-a.
"""

import sys
import time

from application.configuration import Configuration
from application.models import Role, User, database
from authentication import application

MAX_ATTEMPTS = 60
WAIT_SECONDS = 2


def wait_for_database():
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with application.app_context():
                database.session.execute(database.text("SELECT 1"))
            print("[migrate] Baza podataka je dostupna.", flush=True)
            return True
        except Exception as error:  # noqa: BLE001 - ceka se i na DNS i na startovanje baze
            print(
                f"[migrate] Baza nije dostupna ({attempt}/{MAX_ATTEMPTS}): {error.__class__.__name__}",
                flush=True,
            )
            time.sleep(WAIT_SECONDS)
    return False


def create_schema():
    with application.app_context():
        database.create_all()
        print("[migrate] Tabele su kreirane.", flush=True)


def ensure_roles():
    with application.app_context():
        for name in (Configuration.ROLE_DIRECTOR, Configuration.ROLE_EMPLOYEE):
            if Role.query.filter(Role.name == name).first() is None:
                database.session.add(Role(name=name))
                print(f"[migrate] Dodata uloga: {name}", flush=True)
        database.session.commit()


def ensure_director():
    with application.app_context():
        director_role = Role.query.filter(Role.name == Configuration.ROLE_DIRECTOR).first()

        existing = User.query.filter(User.email == Configuration.DIRECTOR_EMAIL).first()
        if existing is not None:
            print("[migrate] Direktor vec postoji, preskacem.", flush=True)
            return

        director = User(
            forename=Configuration.DIRECTOR_FORENAME,
            surname=Configuration.DIRECTOR_SURNAME,
            email=Configuration.DIRECTOR_EMAIL,
            role_id=director_role.id,
        )
        director.set_password(Configuration.DIRECTOR_PASSWORD)

        database.session.add(director)
        database.session.commit()
        print(f"[migrate] Dodat pocetni direktor: {Configuration.DIRECTOR_EMAIL}", flush=True)


if __name__ == "__main__":
    if not wait_for_database():
        print("[migrate] Baza podataka nije postala dostupna. Prekidam.", flush=True)
        sys.exit(1)

    create_schema()
    ensure_roles()
    ensure_director()
    print("[migrate] Inicijalizacija zavrsena.", flush=True)
