from models import db, Benutzer, Film


class DataManager:
    def create_user(self, name: str):
        benutzer = Benutzer(name=name)
        db.session.add(benutzer)
        db.session.commit()
        return benutzer

    def get_users(self):
        return Benutzer.query.order_by(Benutzer.id.asc()).all()

    def get_user(self, benutzer_id: int):
        return Benutzer.query.get(benutzer_id)

    def get_movies(self, benutzer_id: int):
        return Film.query.filter_by(benutzer_id=benutzer_id).order_by(Film.id.desc()).all()

    def movie_exists(self, benutzer_id: int, imdb_id: str):
        return Film.query.filter_by(benutzer_id=benutzer_id, imdb_id=imdb_id).first()

    def add_movie(self, benutzer_id, titel, jahr, imdb_id, poster_url, director):
        film = Film(
            titel=titel,
            jahr=jahr,
            imdb_id=imdb_id,
            poster_url=poster_url,
            director=director,
            benutzer_id=benutzer_id
        )
        db.session.add(film)
        db.session.commit()
        return film

    def update_movie(self, benutzer_id: int, film_id: int, neuer_titel: str):
        film = Film.query.filter_by(id=film_id, benutzer_id=benutzer_id).first()
        if not film:
            return None
        film.titel = neuer_titel
        db.session.commit()
        return film

    def delete_movie(self, benutzer_id: int, film_id: int):
        film = Film.query.filter_by(id=film_id, benutzer_id=benutzer_id).first()
        if not film:
            return False
        db.session.delete(film)
        db.session.commit()
        return True
