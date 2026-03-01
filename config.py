from dotenv import load_dotenv
import os

load_dotenv()

class Konfiguration:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    OMDB_API_KEY = os.getenv("OMDB_API_KEY")
    SQLALCHEMY_DATABASE_URI = "sqlite:///movieweb.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
