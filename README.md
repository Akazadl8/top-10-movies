# 🎬 My Top 10 Movies

A Flask web app for keeping a ranked list of your favourite films. Search for a movie by name, pick the right one, and the app pulls its poster, year and description from The Movie Database (TMDB). Give it a rating and a short review and the list re-ranks itself automatically.

## Features

- Search movies through the TMDB API
- Flip-card layout with posters
- Rate (0-10) and review each movie
- Automatic ranking by rating
- Edit and delete movies
- SQLite database with SQLAlchemy

## Built with

Python, Flask, SQLAlchemy, Flask-WTF, Bootstrap 5, TMDB API

## How to run

Requires Python 3.10+.

1. Get a free API key from [themoviedb.org](https://www.themoviedb.org/settings/api).
2. Set it and start the app:

```bash
pip install -r requirements.txt
# Windows (PowerShell):  $env:TMDB_API_KEY="your_key"
# macOS / Linux:         export TMDB_API_KEY="your_key"
python main.py
```

Then open **http://127.0.0.1:5000**.
