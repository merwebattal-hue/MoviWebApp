from flask import Flask, render_template, request, redirect, url_for, flash
from config import Konfiguration
from models import db
from omdb_client import OmdbClient
from data_manager import DataManager
import logging
import json
import os


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
    # BLOG JSON HELPERS
    # =========================
    DATA_FILE = os.path.join(os.path.dirname(__file__), "blog_posts.json")

    def lade_blog_posts():
        """
        Liest alle Blogposts aus der JSON-Datei und gibt sie als Liste zurück.
        Falls die Datei nicht existiert oder ungültig ist, wird eine leere Liste zurückgegeben.
        """
        if not os.path.exists(DATA_FILE):
            return []
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                posts = json.load(f)

                # Falls ältere Posts noch kein likes-Feld haben
                for post in posts:
                    if "likes" not in post:
                        post["likes"] = 0

                return posts
        except (json.JSONDecodeError, OSError):
            return []

    def speichere_blog_posts(posts):
        """
        Schreibt alle Blogposts zurück in die JSON-Datei.
        """
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)

    def naechste_id(posts):
        """
        Erzeugt eine neue eindeutige ID (max_id + 1).
        """
        if not posts:
            return 1
        return max(p.get("id", 0) for p in posts) + 1

    # =========================
    # HOME (BLOG INDEX)
    # =========================
    @app.get("/")
    def index():
        posts = lade_blog_posts()
        return render_template("index.html", posts=posts)

    # =========================
    # ADD (BLOG POST)
    # =========================
    @app.route("/add", methods=["GET", "POST"])
    def add():
        if request.method == "POST":
            author = request.form.get("author", "").strip()
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()

            if not author or not title or not content:
                flash("Bitte alle Felder ausfüllen (Autor, Titel, Inhalt).", "error")
                return render_template("add.html", author=author, title=title, content=content)

            posts = lade_blog_posts()
            new_post = {
                "id": naechste_id(posts),
                "author": author,
                "title": title,
                "content": content,
                "likes": 0,
            }
            posts.append(new_post)
            speichere_blog_posts(posts)

            flash("Blogpost wurde hinzugefügt.", "success")
            return redirect(url_for("index"))

        return render_template("add.html")

    # =========================
    # UPDATE (BLOG POST)
    # =========================
    @app.route("/update/<int:post_id>", methods=["GET", "POST"])
    def update(post_id: int):
        posts = lade_blog_posts()
        post = next((p for p in posts if p.get("id") == post_id), None)

        if post is None:
            flash("Blogpost nicht gefunden.", "error")
            return redirect(url_for("index"))

        if request.method == "POST":
            author = request.form.get("author", "").strip()
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()

            if not author or not title or not content:
                flash("Bitte alle Felder ausfüllen (Autor, Titel, Inhalt).", "error")
                post_form = {
                    "id": post_id,
                    "author": author,
                    "title": title,
                    "content": content,
                    "likes": post.get("likes", 0),
                }
                return render_template("update.html", post=post_form)

            for p in posts:
                if p.get("id") == post_id:
                    p["author"] = author
                    p["title"] = title
                    p["content"] = content
                    break

            speichere_blog_posts(posts)
            flash("Blogpost wurde aktualisiert.", "success")
            return redirect(url_for("index"))

        return render_template("update.html", post=post)

    # =========================
    # DELETE (BLOG POST)
    # =========================
    @app.route("/delete/<int:post_id>")
    def delete(post_id: int):
        posts = lade_blog_posts()
        neue_posts = [p for p in posts if p.get("id") != post_id]

        if len(neue_posts) == len(posts):
            flash("Blogpost nicht gefunden.", "error")
            return redirect(url_for("index"))

        speichere_blog_posts(neue_posts)
        flash("Blogpost wurde gelöscht.", "success")
        return redirect(url_for("index"))

    # =========================
    # LIKE (BLOG POST)
    # =========================
    @app.route("/like/<int:post_id>")
    def like(post_id: int):
        posts = lade_blog_posts()

        gefunden = False
        for p in posts:
            if p.get("id") == post_id:
                p["likes"] = p.get("likes", 0) + 1
                gefunden = True
                break

        if not gefunden:
            flash("Blogpost nicht gefunden.", "error")
            return redirect(url_for("index"))

        speichere_blog_posts(posts)
        flash("Blogpost wurde geliked.", "success")
        return redirect(url_for("index"))

    # =========================
    # USERS HOME (LIST + CREATE FORM)
    # =========================
    @app.get("/users")
    def users_home():
        benutzer = repo.get_users()
        return render_template("users_index.html", benutzer=benutzer)

    # =========================
    # USERS (CREATE)
    # =========================
    @app.post("/users")
    def benutzer_erstellen():
        name = request.form.get("name", "").strip()
        if not name:
            flash("Bitte einen Namen eingeben.", "error")
            return redirect(url_for("users_home"))

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
            return redirect(url_for("users_home"))

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