from flask import Flask, render_template, request, redirect, url_for, flash
from config import Konfiguration
from models import db
from omdb_client import OmdbClient
from data_manager import DataManager
import logging


def app_erstellen() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Konfiguration)

    # Logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # DB / Repo
    db.init_app(app)
    repo = DataManager()

    with app.app_context():
        db.create_all()

    # =========================
    # INDEX (USERS LIST + CREATE FORM)
    # =========================
    @app.get("/")
    def startseite():
        benutzer = repo.get_users()
        return render_template("index.html", benutzer=benutzer)

    # =========================
    # USERS (CREATE)
    # =========================
    @app.post("/users")
    def benutzer_erstellen():
        name = request.form.get("name", "").strip()
        if not name:
            flash("Bitte einen Namen eingeben.", "error")
            return redirect(url_for("startseite"))

        neuer = repo.create_user(name)
        return redirect(url_for("filme_liste", benutzer_id=neuer.id))

    # =========================
    # MOVIES (LIST)
    # =========================
    @app.get("/users/<int:benutzer_id>/movies")
    def filme_liste(benutzer_id: int):
        benutzer = repo.get_user(benutzer_id)
        if not benutzer:
            flash("Benutzer nicht gefunden.", "error")
            return redirect(url_for("startseite"))

        filme = repo.get_movies(benutzer_id)
        return render_template("movies.html", benutzer=benutzer, filme=filme)

    # =========================
    # MOVIES (ADD)
    # =========================
    @app.post("/users/<int:benutzer_id>/movies")
    def film_hinzufuegen(benutzer_id: int):
        titel_eingabe = request.form.get("titel", "").strip()
        if not titel_eingabe:
            flash("Filmtitel fehlt.", "error")
            return redirect(url_for("filme_liste", benutzer_id=benutzer_id))

        try:
            client = OmdbClient(app.config.get("OMDB_API_KEY", ""))
            daten = client.film_suchen(titel_eingabe)
        except Exception:
            app.logger.exception("OMDb-Abfrage fehlgeschlagen")
            flash("OMDb-Abfrage fehlgeschlagen. API-Key/Netzwerk prüfen.", "error")
            return redirect(url_for("filme_liste", benutzer_id=benutzer_id))

        if not daten:
            flash("Film wurde nicht gefunden (OMDb).", "error")
            return redirect(url_for("filme_liste", benutzer_id=benutzer_id))

        imdb_id = daten.get("imdbID")
        if imdb_id and repo.movie_exists(benutzer_id, imdb_id):
            flash("Film ist bereits in deiner Liste.", "error")
            return redirect(url_for("filme_liste", benutzer_id=benutzer_id))

        repo.add_movie(
            benutzer_id=benutzer_id,
            titel=daten.get("Title", titel_eingabe),
            jahr=daten.get("Year"),
            imdb_id=imdb_id,
            poster_url=daten.get("Poster"),
            director=daten.get("Director"),
        )

        flash("Film hinzugefügt.", "success")
        return redirect(url_for("filme_liste", benutzer_id=benutzer_id))

    # =========================
    # MOVIES (UPDATE)
    # =========================
    @app.post("/users/<int:benutzer_id>/movies/<int:film_id>/update")
    def film_aktualisieren(benutzer_id: int, film_id: int):
        neuer_titel = request.form.get("neuer_titel", "").strip()
        if not neuer_titel:
            flash("Neuer Titel fehlt.", "error")
            return redirect(url_for("filme_liste", benutzer_id=benutzer_id))

        updated = repo.update_movie(benutzer_id, film_id, neuer_titel)
        if not updated:
            flash("Film nicht gefunden.", "error")
            return redirect(url_for("filme_liste", benutzer_id=benutzer_id))

        flash("Film aktualisiert.", "success")
        return redirect(url_for("filme_liste", benutzer_id=benutzer_id))

    # =========================
    # MOVIES (DELETE)
    # =========================
    @app.post("/users/<int:benutzer_id>/movies/<int:film_id>/delete")
    def film_loeschen(benutzer_id: int, film_id: int):
        ok = repo.delete_movie(benutzer_id, film_id)
        if not ok:
            flash("Film nicht gefunden.", "error")
            return redirect(url_for("filme_liste", benutzer_id=benutzer_id))

        flash("Film gelöscht.", "success")
        return redirect(url_for("filme_liste", benutzer_id=benutzer_id))

    # =========================
    # ERROR HANDLERS
    # =========================
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        app.logger.exception("Internal Server Error")
        return render_template("500.html"), 500

    return app


app = app_erstellen()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
