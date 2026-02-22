from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Benutzer(db.Model):
    __tablename__ = "benutzer"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

    filme = db.relationship("Film", backref="benutzer", cascade="all, delete-orphan")

class Film(db.Model):
    __tablename__ = "film"

    id = db.Column(db.Integer, primary_key=True)
    titel = db.Column(db.String(255), nullable=False)
    jahr = db.Column(db.String(10))
    imdb_id = db.Column(db.String(20))
    poster_url = db.Column(db.String(500))
    kommentar = db.Column(db.String(500))
    bewertung = db.Column(db.Integer)

    benutzer_id = db.Column(db.Integer, db.ForeignKey("benutzer.id"), nullable=False)
