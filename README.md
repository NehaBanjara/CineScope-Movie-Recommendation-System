# CineScope - Movie Recommendation System

This is a movie recommendation web app I built as part of my learning journey in B.Tech. The idea was simple — I wanted to build something that actually feels useful, not just a tutorial project. So I made an app where you can search for a movie and get recommendations based on it, along with some stats and comparisons.

It is not perfect, but it works, and I learned a lot building it.

---

## What the app does

- Search for any movie and get recommendations similar to it
- See movie details like poster, release date, and rating pulled live from TMDB
- Browse popular, trending, top-rated, and upcoming movies on the home page
- Filter movies by genre, rating, and popularity on the analytics dashboard
- Compare two movies side by side
- Get personalised picks based on the genre you like
- See overall stats about the movie dataset like average ratings, genre distribution, and top 10 most popular movies

---

## How I built it

The backend is built with **FastAPI** (Python). It handles all the API routes, loads the ML data, and talks to the TMDB API to fetch real movie info like posters and details.

For recommendations, I used **TF-IDF** (a text similarity technique from scikit-learn) on movie metadata. Basically it finds movies that are similar based on their descriptions and genres. The results from TF-IDF are combined with TMDB's genre-based discovery to give better suggestions.

The frontend is a **Streamlit** app that calls the FastAPI backend and shows everything in a clean UI.

The movie dataset is a CSV file with metadata for thousands of movies. I preprocessed it and saved the ML models as pickle files so they load faster on startup.

**Main tools and libraries used:**
- FastAPI and Uvicorn (backend server)
- Streamlit (frontend UI)
- scikit-learn (TF-IDF recommendation model)
- pandas and numpy (data processing)
- httpx (making async API calls to TMDB)
- plotly (charts on the analytics dashboard)
- TMDB API (for live movie data, posters, ratings)

---

## Folder structure

```
Movie_recommened__system/
|
|-- main.py                  # FastAPI backend — all the routes and ML logic
|-- app.py                   # Streamlit frontend entry point
|-- pages/                   # Extra Streamlit pages (analytics, compare, etc.)
|-- open_pickle.py           # Script used to generate the pickle files
|-- df.pkl                   # Processed movie dataframe
|-- tfidf_matrix.pkl         # TF-IDF matrix for recommendations
|-- tfidf.pkl                # TF-IDF vectorizer object
|-- indices.pkl              # Movie title to index mapping
|-- movies_metadata.csv      # Raw movie dataset
|-- requirements.txt         # All Python dependencies
|-- .env                     # API keys (not uploaded to GitHub)
|-- runtime.txt              # Python version for deployment
```

---

## How to run it locally

Make sure you have Python 3.11 installed.

**1. Clone the repo**
```bash
git clone https://github.com/NehaBanjara/CineScope-Movie-Recommendation-System.git
cd CineScope-Movie-Recommendation-System
```

**2. Create a virtual environment and activate it**
```bash
python -m venv .venv
.venv\Scripts\activate       # On Windows
source .venv/bin/activate    # On Mac/Linux
```

**3. Install the dependencies**
```bash
pip install -r requirements.txt
```

**4. Add your TMDB API key**

Create a `.env` file in the root folder and add:
```
TMDB_API_KEY=your_api_key_here
```

You can get a free API key from [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)

**5. Start the FastAPI backend**
```bash
uvicorn main:app --reload
```

**6. In a new terminal, start the Streamlit frontend**
```bash
streamlit run app.py
```

Now open your browser and go to `http://localhost:8501`

---

## Why I built this

I wanted to go beyond the usual beginner projects. Most tutorials show you how to build a recommendation system in a notebook, but I wanted to actually deploy something that works like a real app — with an API, a frontend, live data, and actual hosting.

Along the way I learned how TF-IDF works, how to structure a FastAPI project properly, how to handle async calls, and honestly, a lot about debugging deployment errors on Render.

It took more time than expected (especially the deployment part), but I am glad I pushed through it. This project taught me more than any single course did.

---


## API key note

This project uses the TMDB API for movie data. You will need your own free API key to run it locally. The key used in production is stored as an environment variable and is not pushed to GitHub.
