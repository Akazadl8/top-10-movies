import os

import requests
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange, Optional

# Get a free API key from https://www.themoviedb.org/settings/api and set it as TMDB_API_KEY
MOVIE_DB_API_KEY = os.environ.get("TMDB_API_KEY", "")
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "change-me-in-production")
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///movies.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    rating = FloatField("Your Rating Out of 10 e.g. 7.5",
                        validators=[DataRequired(message="Please enter a number, e.g. 7.5"),
                                    NumberRange(min=0, max=10)])
    review = StringField("Your Review", validators=[Optional()])
    submit = SubmitField("Done")


class FindMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


def tmdb_get(url, **params):
    """Call The Movie Database API. Returns the JSON, or None if something went wrong."""
    if not MOVIE_DB_API_KEY:
        flash("No TMDB API key found. Set the TMDB_API_KEY environment variable (see README).")
        return None
    try:
        response = requests.get(url, params={"api_key": MOVIE_DB_API_KEY, **params}, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        flash("Couldn't reach The Movie Database. Check your API key and internet connection.")
        return None


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()  # convert ScalarResult to Python List

    # Highest rating gets ranking 1
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id", type=int)
    if movie_id is None:
        abort(404)
    movie = db.get_or_404(Movie, movie_id)
    if request.method == "GET":
        form.rating.data = movie.rating
        form.review.data = movie.review
    if form.validate_on_submit():
        movie.rating = round(form.rating.data, 1)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id", type=int)
    if movie_id is None:
        abort(404)
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = FindMovieForm()
    if form.validate_on_submit():
        data = tmdb_get(MOVIE_DB_SEARCH_URL, query=form.title.data)
        if data is not None:
            return render_template("select.html", options=data.get("results", []))
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id", type=int)
    if not movie_api_id:
        return redirect(url_for("add_movie"))

    data = tmdb_get(f"{MOVIE_DB_INFO_URL}/{movie_api_id}", language="en-US")
    if data is None:
        return redirect(url_for("add_movie"))

    # Already in the list? Just go and rate it again.
    existing = db.session.execute(db.select(Movie).where(Movie.title == data["title"])).scalar()
    if existing:
        flash(f"{existing.title} is already in your list.")
        return redirect(url_for("rate_movie", id=existing.id))

    release_year = (data.get("release_date") or "0").split("-")[0]
    poster = data.get("poster_path")
    new_movie = Movie(
        title=data["title"],
        year=int(release_year) if release_year.isdigit() else 0,
        img_url=f"{MOVIE_DB_IMAGE_URL}{poster}" if poster else "https://placehold.co/500x750?text=No+Poster",
        description=(data.get("overview") or "No description available.")[:500]
    )
    db.session.add(new_movie)
    db.session.commit()

    # Go straight to rating the new movie
    return redirect(url_for("rate_movie", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
