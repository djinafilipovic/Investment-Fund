from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

database = SQLAlchemy()


class Role(database.Model):
    __tablename__ = "roles"

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    name = database.Column(database.String(32), nullable=False, unique=True)

    users = database.relationship("User", back_populates="role", lazy="select")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(database.Model):
    __tablename__ = "users"

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    forename = database.Column(database.String(256), nullable=False)
    surname = database.Column(database.String(256), nullable=False)
    email = database.Column(database.String(256), nullable=False, unique=True, index=True)
    # kolona je duza od 256 jer se cuva hash lozinke, a ne lozinka u cistom tekstu
    password = database.Column(database.String(512), nullable=False)

    role_id = database.Column(database.Integer, database.ForeignKey("roles.id"), nullable=False)
    role = database.relationship("Role", back_populates="users", lazy="joined")

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password, method="pbkdf2:sha256")

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    def claims(self):
        return {
            "forename": self.forename,
            "surname": self.surname,
            "email": self.email,
            "role": self.role.name,
        }

    def __repr__(self):
        return f"<User {self.email} ({self.role_id})>"
