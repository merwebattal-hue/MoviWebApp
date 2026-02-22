import os

class Konfiguration:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///movieweb.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")
