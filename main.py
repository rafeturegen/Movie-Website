from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///new-movies.db"
Bootstrap5(app)


# CREATE DB


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)


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
    new_rating = StringField("Your Rating out of 10 e.g 7.5", validators=[DataRequired()])
    new_review = StringField("Your review", validators=[DataRequired()])
    submit = SubmitField("Done")


class AddMovieForm(FlaskForm):
    movie_name = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    print(all_movies)
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", all_movies=all_movies)


@app.route("/edit", methods=["POST", "GET"])
def edit_rating():
    movie_id = request.args.get("movie_id")
    requested_movie = db.get_or_404(Movie, movie_id)
    form = RateMovieForm()
    if form.validate_on_submit():
        requested_movie.rating = float(form.new_rating.data)
        requested_movie.review = form.new_review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", movie=requested_movie, form=form)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("movie_id")
    requested_movie = db.get_or_404(Movie, movie_id)
    db.session.delete(requested_movie)
    db.session.commit()
    return redirect(url_for('home'))


TMDB_API_KEY = '8ba3bcdf065d757beca30914cef5c722'


@app.route("/add_movie", methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_title = form.movie_name.data
        url = "https://api.themoviedb.org/3/search/movie?include_adult=false&language=en-US&page=1"

        params = {
            "query": movie_title,
            "api_key": "ba3bcdf065d757beca30914cef5c722"
        }

        response = requests.get(url, params={"api_key": TMDB_API_KEY, "query": movie_title})
        data = response.json()["results"]

        return render_template("select.html", films=data)
    return render_template("add.html", form=form)


@app.route("/select", methods=["POST", "GET"])
def select():
    movie_id = request.args.get("film_id")
    if movie_id:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"

        response = requests.get(url=url,
                                params={
                                    "api_key": "8ba3bcdf065d757beca30914cef5c722"
                                })
        new_movie = Movie(
            title=response.json()['title'],
            img_url=F"{"https://image.tmdb.org/t/p/original/"}{response.json()["poster_path"]}",
            year=response.json()["release_date"].split("-")[0],
            description=response.json()["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit_rating", movie_id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
