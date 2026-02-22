from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Konfiguration
from models import db, Benutzer, Film
from omdb_client import OmdbClient

def app_erstellen() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Konfiguration)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.get("/")
    def startseite():
        benutzername = session.get("benutzername")
        return render_template("index.html", benutzername=benutzername)

    @app.get("/register")
    def registrieren_form():
        return render_template("register.html")

    @app.post("/register")
    def registrieren():
        name = request.form.get("name", "").strip()
        if not name:
            flash("Bitte einen Namen eingeben.", "error")
            return redirect(url_for("registrieren_form"))

        vorhandener = Benutzer.query.filter_by(name=name).first()
        if not vorhandener:
            neuer = Benutzer(name=name)
            db.session.add(neuer)
            db.session.commit()

        session["benutzername"] = name
        return redirect(url_for("filme_liste"))

    def aktiven_benutzer_holen() -> Benutzer | None:
        name = session.get("benutzername")
        if not name:
            return None
        return Benutzer.query.filter_by(name=name).first()

    @app.get("/movies")
    def filme_liste():
        benutzer = aktiven_benutzer_holen()
        if not benutzer:
            return redirect(url_for("registrieren_form"))

        filme = Film.query.filter_by(benutzer_id=benutzer.id).order_by(Film.id.desc()).all()
        return render_template("movies.html", benutzer=benutzer, filme=filme)

    @app.post("/movies/add")
    def film_hinzufuegen():
        benutzer = aktiven_benutzer_holen()
        if not benutzer:
            return redirect(url_for("registrieren_form"))

        titel = request.form.get("titel", "").strip()
        if not titel:
            flash("Filmtitel fehlt.", "error")
            return redirect(url_for("filme_liste"))

        client = OmdbClient(app.config["OMDB_API_KEY"])
        daten = client.film_suchen(titel)

        if not daten:
            flash("Film wurde nicht gefunden (OMDb).", "error")
            return redirect(url_for("filme_liste"))

        bereits_vorhanden = Film.query.filter_by(
            benutzer_id=benutzer.id,
            imdb_id=daten.get("imdbID")
        ).first()

        if bereits_vorhanden:
            flash("Film ist bereits in deiner Liste.", "error")
            return redirect(url_for("filme_liste"))

        film = Film(
            titel=daten.get("Title", titel),
            jahr=daten.get("Year"),
            imdb_id=daten.get("imdbID"),
            poster_url=daten.get("Poster"),
            benutzer_id=benutzer.id
        )
        db.session.add(film)
        db.session.commit()

        flash("Film hinzugefügt.", "success")
        return redirect(url_for("filme_liste"))

    @app.post("/movies/<int:film_id>/delete")
    def film_loeschen(film_id: int):
        benutzer = aktiven_benutzer_holen()
        if not benutzer:
            return redirect(url_for("registrieren_form"))

        film = Film.query.filter_by(id=film_id, benutzer_id=benutzer.id).first_or_404()
        db.session.delete(film)
        db.session.commit()
        flash("Film gelöscht.", "success")
        return redirect(url_for("filme_liste"))

    @app.get("/logout")
    def abmelden():
        session.clear()
        return redirect(url_for("startseite"))

    return app

app = app_erstellen()

if __name__ == "__main__":
    app.run(debug=True)
