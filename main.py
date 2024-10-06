from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

# initializing the flask app and sqlalchemy
app = Flask(__name__)


# just a necessity
class Base(DeclarativeBase):
    pass


url = "https://api.themoviedb.org/3/search/movie?include_adult=true&language=en-US&page=1"

headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9"
                     ".eyJhdWQiOiIxZmUzZjM5ZWRmNmQ4MDViMTlhMDIyMWRmMjA2ZTcyNiIsInN1YiI6IjY1Zjg4ZDY4OWM5N2JkMDE2NGVkNDgxMiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.VF6xccyMCIAuASbizPboiBa7QJNNUsC1miX-8_hfNuY"
}

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(app)

app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


# CREATE DB

class Movies(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(250), nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=True)


# CREATE TABLE
with app.app_context():
    db.create_all()


class UpdateRating(FlaskForm):
    rating = StringField("Your Rating out of 10 e.g. 6.9", validators=[DataRequired()])
    review = StringField("Review about the movie", validators=[DataRequired()])
    submit = SubmitField("Done")


class AddMovie(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    result = list(db.session.execute(db.select(Movies).order_by(Movies.rating)).scalars().all())
    for i in range(len(result)):
        result[i].ranking = len(result) - i
    db.session.commit()

    return render_template("index.html", movies=result)


@app.route("/update", methods=["GET", "POST"])
def update():
    form = UpdateRating()
    movie_id = request.args.get("id")
    movie_to_update = db.get_or_404(Movies, movie_id)
    if form.validate_on_submit():
        movie_to_update.rating = float(form.rating.data)
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=movie_to_update)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = db.get_or_404(Movies, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        title = form.title.data
        response = requests.get(url, headers=headers, params={"query": title})
        data = response.json()["results"]
        return render_template('select.html', movies=data)
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"https://api.themoviedb.org/3/movie/{movie_api_id}"
        response = requests.get(movie_api_url, headers=headers)
        data = response.json()
        print(data)
        new_movie = Movies(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"https://image.tmdb.org/t/p/w500{data['backdrop_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('update', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
