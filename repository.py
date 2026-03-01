from models import db, Benutzer, Film

class DatenRepository:
    def alle_benutzer_holen(self) -> list[Benutzer]:
        return Benutzer.query.order_by(Benutzer.name.asc()).all()

    def benutzer_erstellen(self, name: str) -> Benutzer:
        vorhandener = Benutzer.query.filter_by(name=name).first()
        if vorhandener:
            return vorhandener
        neuer = Benutzer(name=name)
        db.session.add(neuer)
        db.session.commit()
        return neuer

    def benutzer_holen(self, benutzer_id: int) -> Benutzer | None:
        return Benutzer.query.get(benutzer_id)

    def filme_von_benutzer_holen(self, benutzer_id: int) -> list[Film]:
        return Film.query.filter_by(benutzer_id=benutzer_id).order_by(Film.id.desc()).all()

    def film_hinzufuegen(self, benutzer_id, titel, jahr, imdb_id, poster_url, director):
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

    def film_ist_bereits_vorhanden(self, benutzer_id: int, imdb_id: str | None) -> bool:
        if not imdb_id:
            return False
        vorhanden = Film.query.filter_by(benutzer_id=benutzer_id, imdb_id=imdb_id).first()
        return vorhanden is not None

    def film_loeschen(self, benutzer_id: int, film_id: int) -> None:
        film = Film.query.filter_by(id=film_id, benutzer_id=benutzer_id).first_or_404()
        db.session.delete(film)
        db.session.commit()

    def film_aktualisieren(self, benutzer_id: int, film_id: int, neuer_titel: str) -> None:
        film = Film.query.filter_by(id=film_id, benutzer_id=benutzer_id).first_or_404()
        film.titel = neuer_titel.strip() or film.titel
        db.session.commit()

