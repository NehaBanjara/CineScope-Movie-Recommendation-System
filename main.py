import os
import pickle
import threading
import asyncio
import ssl
from collections import Counter
from typing import Optional, List, Dict, Any, Tuple

import numpy as np
import pandas as pd
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv


# =========================
# ENV
# =========================
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE    = "https://api.themoviedb.org/3"
TMDB_IMG_500 = "https://image.tmdb.org/t/p/w500"

if not TMDB_API_KEY:
    raise RuntimeError("TMDB_API_KEY missing — add it to your .env file as TMDB_API_KEY=xxxx")


# =========================
# FASTAPI APP
# =========================
app = FastAPI(title="CineScope Movie Recommender API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# PICKLE PATHS
# =========================
BASE_DIR          = os.path.dirname(os.path.abspath(__file__))
DF_PATH           = os.path.join(BASE_DIR, "df.pkl")
INDICES_PATH      = os.path.join(BASE_DIR, "indices.pkl")
TFIDF_MATRIX_PATH = os.path.join(BASE_DIR, "tfidf_matrix.pkl")
TFIDF_PATH        = os.path.join(BASE_DIR, "tfidf.pkl")

df:           Optional[pd.DataFrame]   = None
indices_obj:  Any                      = None
tfidf_matrix: Any                      = None
tfidf_obj:    Any                      = None
TITLE_TO_IDX: Optional[Dict[str, int]] = None
_load_lock  = threading.Lock()


# =========================
# TMDB Genre Name to ID map
# =========================
GENRE_NAME_TO_ID: Dict[str, int] = {
    "Action":            28,
    "Adventure":         12,
    "Animation":         16,
    "Comedy":            35,
    "Crime":             80,
    "Documentary":       99,
    "Drama":             18,
    "Family":         10751,
    "Fantasy":           14,
    "History":           36,
    "Horror":            27,
    "Music":          10402,
    "Mystery":         9648,
    "Romance":        10749,
    "Science":          878,
    "Fiction":          878,
    "Science Fiction":  878,
    "Thriller":          53,
    "War":            10752,
    "Western":           37,
}


# =========================
# MODELS
# =========================
class TMDBMovieCard(BaseModel):
    tmdb_id:      int
    title:        str
    poster_url:   Optional[str]   = None
    release_date: Optional[str]   = None
    vote_average: Optional[float] = None

class TMDBMovieDetails(BaseModel):
    tmdb_id:      int
    title:        str
    overview:     Optional[str] = None
    release_date: Optional[str] = None
    poster_url:   Optional[str] = None
    backdrop_url: Optional[str] = None
    genres:       List[dict]    = []

class TFIDFRecItem(BaseModel):
    title: str
    score: float
    tmdb:  Optional[TMDBMovieCard] = None

class SearchBundleResponse(BaseModel):
    query:                 str
    movie_details:         TMDBMovieDetails
    tfidf_recommendations: List[TFIDFRecItem]
    genre_recommendations: List[TMDBMovieCard]

class RatingBucket(BaseModel):
    range: str
    count: int

class GenreStat(BaseModel):
    genre:      str
    count:      int
    avg_rating: float

class MovieRow(BaseModel):
    title:        str
    vote_average: float
    popularity:   float
    genres:       str

class OverviewStats(BaseModel):
    total_movies:   int
    avg_rating:     float
    avg_popularity: float
    pct_high:       float
    rating_dist:    List[RatingBucket]
    genre_stats:    List[GenreStat]
    top10_popular:  List[MovieRow]

class FilteredStats(BaseModel):
    total:                int
    avg_rating:           float
    avg_popularity:       float
    pct_high:             float
    rating_dist:          List[RatingBucket]
    popularity_by_rating: List[dict]

class RecommendItem(BaseModel):
    title:        str
    vote_average: float
    popularity:   float
    genres:       str
    poster_url:   Optional[str] = None

class RecommendResponse(BaseModel):
    total_found:   int
    top_picks:     List[RecommendItem]
    highest_rated: List[RecommendItem]
    trending:      List[RecommendItem]

class CompareMovieData(BaseModel):
    title:        str
    vote_average: float
    popularity:   float
    genres:       List[str]
    overview_len: int
    poster_url:   Optional[str] = None

class CompareResponse(BaseModel):
    movie1: CompareMovieData
    movie2: CompareMovieData

class AllTitlesResponse(BaseModel):
    titles: List[str]


# =========================
# UTILS
# =========================
def _norm(t: str) -> str:
    return str(t).strip().lower()

def make_img_url(path: Optional[str]) -> Optional[str]:
    return f"{TMDB_IMG_500}{path}" if path else None


def _make_ssl_context() -> ssl.SSLContext:
    """Create a permissive SSL context to avoid certificate verification issues."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


async def tmdb_get(path: str, params: Dict[str, Any], retries: int = 3) -> Dict[str, Any]:
    """
    Fetch from TMDB API with retry logic and robust SSL/connection handling.
    Tries multiple approaches if the first fails.
    """
    q = {**params, "api_key": TMDB_API_KEY}
    url = f"{TMDB_BASE}{path}"
    last_error: Optional[Exception] = None

    # Strategy 1: Standard httpx with verify=False
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(
                verify=False,
                timeout=httpx.Timeout(30.0, connect=10.0),
                follow_redirects=True,
            ) as client:
                r = await client.get(url, params=q)
                if r.status_code == 200:
                    return r.json()
                elif r.status_code == 401:
                    raise HTTPException(401, "Invalid TMDB API key — check your .env file")
                elif r.status_code == 404:
                    raise HTTPException(404, f"TMDB resource not found: {path}")
                elif r.status_code >= 500:
                    last_error = Exception(f"TMDB server error {r.status_code}")
                    if attempt < retries - 1:
                        await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                else:
                    raise HTTPException(502, f"TMDB error {r.status_code}: {r.text[:200]}")
        except HTTPException:
            raise
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            last_error = e
            if attempt < retries - 1:
                await asyncio.sleep(1.5 * (attempt + 1))
            continue
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                await asyncio.sleep(1.0)
            continue

    # Strategy 2: Try with custom SSL context via httpcore transport
    try:
        ssl_ctx = _make_ssl_context()
        transport = httpx.AsyncHTTPTransport(verify=ssl_ctx, retries=2)
        async with httpx.AsyncClient(
            transport=transport,
            timeout=httpx.Timeout(45.0, connect=15.0),
            follow_redirects=True,
        ) as client:
            r = await client.get(url, params=q)
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        last_error = e

    error_msg = str(last_error) if last_error else "Unknown connection error"
    raise HTTPException(
        502,
        f"TMDB unreachable after {retries} attempts. "
        f"Check your internet connection or VPN. Error: {error_msg}"
    )


async def tmdb_cards_from_results(results: List[dict], limit: int = 20) -> List[TMDBMovieCard]:
    return [
        TMDBMovieCard(
            tmdb_id=int(m["id"]),
            title=m.get("title") or m.get("name") or "",
            poster_url=make_img_url(m.get("poster_path")),
            release_date=m.get("release_date"),
            vote_average=m.get("vote_average"),
        )
        for m in (results or [])[:limit]
    ]


async def tmdb_movie_details(movie_id: int) -> TMDBMovieDetails:
    data = await tmdb_get(f"/movie/{movie_id}", {"language": "en-US"})
    return TMDBMovieDetails(
        tmdb_id=int(data["id"]),
        title=data.get("title") or "",
        overview=data.get("overview"),
        release_date=data.get("release_date"),
        poster_url=make_img_url(data.get("poster_path")),
        backdrop_url=make_img_url(data.get("backdrop_path")),
        genres=data.get("genres") or [],
    )


async def tmdb_search_movies(query: str, page: int = 1) -> Dict[str, Any]:
    return await tmdb_get(
        "/search/movie",
        {"query": query, "include_adult": "false", "language": "en-US", "page": page},
    )


async def tmdb_search_first(query: str) -> Optional[dict]:
    try:
        data    = await tmdb_search_movies(query=query, page=1)
        results = data.get("results", [])
        return results[0] if results else None
    except HTTPException:
        return None


async def tmdb_poster_for_title(title: str) -> Optional[str]:
    """Fetch poster with short timeout so batch fetches don't hang."""
    try:
        q = {
            "query": title,
            "include_adult": "false",
            "language": "en-US",
            "page": 1,
            "api_key": TMDB_API_KEY,
        }
        async with httpx.AsyncClient(
            verify=False,
            timeout=httpx.Timeout(8.0, connect=5.0),
            follow_redirects=True,
        ) as client:
            r = await client.get(f"{TMDB_BASE}/search/movie", params=q)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results and results[0].get("poster_path"):
                return make_img_url(results[0]["poster_path"])
    except Exception:
        pass
    return None


# =========================
# TF-IDF HELPERS
# =========================
def build_title_to_idx_map(indices: Any) -> Dict[str, int]:
    out: Dict[str, int] = {}
    try:
        for k, v in indices.items():
            out[_norm(k)] = int(v)
    except Exception:
        raise RuntimeError("indices.pkl must be a dict or pandas Series")
    return out


def get_local_idx(title: str) -> Optional[int]:
    if TITLE_TO_IDX is None:
        return None
    return TITLE_TO_IDX.get(_norm(title))


def tfidf_recommend_titles(query_title: str, top_n: int = 10) -> List[Tuple[str, float]]:
    if df is None or tfidf_matrix is None:
        return []
    idx = get_local_idx(query_title)
    if idx is None:
        return []
    qv     = tfidf_matrix[idx]
    scores = (tfidf_matrix @ qv.T).toarray().ravel()
    order  = np.argsort(-scores)
    out: List[Tuple[str, float]] = []
    for i in order:
        if int(i) == idx:
            continue
        try:
            t = str(df.iloc[int(i)]["title"])
        except Exception:
            continue
        out.append((t, float(scores[int(i)])))
        if len(out) >= top_n:
            break
    return out


async def attach_tmdb_card(title: str) -> Optional[TMDBMovieCard]:
    try:
        m = await tmdb_search_first(title)
        if not m:
            return None
        return TMDBMovieCard(
            tmdb_id=int(m["id"]),
            title=m.get("title") or title,
            poster_url=make_img_url(m.get("poster_path")),
            release_date=m.get("release_date"),
            vote_average=m.get("vote_average"),
        )
    except Exception:
        return None


# =========================
# ANALYTICS HELPERS
# =========================
def _ensure_df():
    if df is None:
        raise HTTPException(503, "ML data still loading — retry in a few seconds")


def _rating_dist(frame: pd.DataFrame) -> List[RatingBucket]:
    bins   = [0, 2, 4, 5, 6, 7, 8, 9, 10.01]
    labels = ["0-2", "2-4", "4-5", "5-6", "6-7", "7-8", "8-9", "9-10"]
    tmp = frame.copy()
    tmp["bucket"] = pd.cut(tmp["vote_average"], bins=bins, labels=labels, right=False)
    counts = tmp["bucket"].value_counts().sort_index()
    return [RatingBucket(range=str(k), count=int(v)) for k, v in counts.items()]


def _genre_stats(frame: pd.DataFrame) -> List[GenreStat]:
    counter: Counter = Counter()
    for g in frame["genres"].dropna():
        for w in str(g).split():
            w = w.strip()
            if w and w != "Fiction":
                counter[w] += 1
    top12 = counter.most_common(12)
    result = []
    for genre, count in top12:
        mask       = frame["genres"].str.contains(genre, na=False)
        avg_rating = round(float(frame[mask]["vote_average"].mean()), 2)
        result.append(GenreStat(genre=genre, count=count, avg_rating=avg_rating))
    return result


def _apply_filters(min_rating: float, max_rating: float, genre: str, min_pop: float) -> pd.DataFrame:
    _ensure_df()
    mask = (
        (df["vote_average"] >= min_rating) &
        (df["vote_average"] <= max_rating) &
        (df["popularity"]   >= min_pop)
    )
    frame = df[mask].copy()
    if genre and genre.lower() != "all":
        frame = frame[frame["genres"].str.contains(genre, na=False)]
    return frame


# =========================
# LAZY LOAD ML DATA
# =========================
def ensure_data_loaded():
    global df, indices_obj, tfidf_matrix, tfidf_obj, TITLE_TO_IDX

    if df is not None:
        return

    with _load_lock:
        if df is not None:
            return

        print("Loading ML data...")
        import sys, numpy
        sys.modules.setdefault("numpy._core",         numpy.core)
        sys.modules.setdefault("numpy._core.numeric", numpy.core.numeric)

        def _pkl(path: str):
            with open(path, "rb") as f:
                return pickle.load(f, encoding="latin1")

        _raw = _pkl(DF_PATH)
        _raw["popularity"]   = pd.to_numeric(_raw["popularity"],   errors="coerce").fillna(0)
        _raw["vote_average"] = pd.to_numeric(_raw["vote_average"], errors="coerce")
        _raw = _raw.dropna(subset=["vote_average"])
        _raw = _raw[_raw["vote_average"] > 0].copy()

        df           = _raw
        indices_obj  = _pkl(INDICES_PATH)
        tfidf_matrix = _pkl(TFIDF_MATRIX_PATH)
        tfidf_obj    = _pkl(TFIDF_PATH)
        TITLE_TO_IDX = build_title_to_idx_map(indices_obj)
        print("ML data loaded successfully!")


# =========================
# STARTUP
# =========================
@app.on_event("startup")
async def startup_event():
    threading.Thread(target=ensure_data_loaded, daemon=True).start()


# =========================
# ROUTES
# =========================
@app.get("/home", response_model=List[TMDBMovieCard])
async def home(
    category: str = Query("popular"),
    limit:    int = Query(24, ge=1, le=50),
):
    try:
        if category == "trending":
            data = await tmdb_get("/trending/movie/day", {"language": "en-US"})
            return await tmdb_cards_from_results(data.get("results", []), limit=limit)
        if category not in {"popular", "top_rated", "upcoming", "now_playing"}:
            raise HTTPException(400, "Invalid category")
        data = await tmdb_get(f"/movie/{category}", {"language": "en-US", "page": 1})
        return await tmdb_cards_from_results(data.get("results", []), limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Home route failed: {e}")


@app.get("/home/genre", response_model=List[TMDBMovieCard])
async def home_by_genre(
    genre: str = Query(...),
    limit: int = Query(24, ge=1, le=50),
    page:  int = Query(1,  ge=1, le=5),
):
    hardcoded = {
        "drama": 18, "comedy": 35, "action": 28, "thriller": 53,
        "romance": 10749, "horror": 27, "animation": 16, "fantasy": 14,
        "crime": 80, "adventure": 12, "family": 10751, "mystery": 9648,
        "history": 36, "war": 10752, "western": 37,
        "music": 10402, "documentary": 99, "science fiction": 878, "science": 878,
    }
    genre_id = GENRE_NAME_TO_ID.get(genre) or hardcoded.get(genre.lower())

    for pg in [page, 1, 2]:
        try:
            if genre_id:
                data = await tmdb_get(
                    "/discover/movie",
                    {"with_genres": genre_id, "language": "en-US",
                     "sort_by": "popularity.desc", "page": pg},
                )
            else:
                data = await tmdb_get("/movie/popular", {"language": "en-US", "page": pg})
            results = data.get("results", [])
            if results:
                return await tmdb_cards_from_results(results, limit=limit)
        except Exception:
            continue

    try:
        data = await tmdb_get("/movie/popular", {"language": "en-US", "page": 1})
        return await tmdb_cards_from_results(data.get("results", []), limit=limit)
    except Exception as e:
        raise HTTPException(502, f"Could not fetch movies: {e}")


@app.get("/tmdb/search")
async def tmdb_search(
    query: str = Query(..., min_length=1),
    page:  int = Query(1, ge=1, le=10),
):
    return await tmdb_search_movies(query=query, page=page)


@app.get("/movie/id/{tmdb_id}", response_model=TMDBMovieDetails)
async def movie_details_route(tmdb_id: int):
    return await tmdb_movie_details(tmdb_id)


@app.get("/recommend/genre", response_model=List[TMDBMovieCard])
async def recommend_genre(
    tmdb_id: int = Query(...),
    limit:   int = Query(18, ge=1, le=50),
):
    details  = await tmdb_movie_details(tmdb_id)
    if not details.genres:
        return []
    genre_id = details.genres[0]["id"]
    discover = await tmdb_get(
        "/discover/movie",
        {"with_genres": genre_id, "language": "en-US", "sort_by": "popularity.desc", "page": 1},
    )
    cards = await tmdb_cards_from_results(discover.get("results", []), limit=limit)
    return [c for c in cards if c.tmdb_id != tmdb_id]


@app.get("/recommend/tfidf")
async def recommend_tfidf(
    title: str = Query(..., min_length=1),
    top_n: int = Query(10, ge=1, le=50),
):
    ensure_data_loaded()
    recs = tfidf_recommend_titles(title, top_n=top_n)
    return [{"title": t, "score": s} for t, s in recs]


@app.get("/movie/search", response_model=SearchBundleResponse)
async def search_bundle(
    query:       str = Query(..., min_length=1),
    tfidf_top_n: int = Query(12, ge=1, le=30),
    genre_limit: int = Query(12, ge=1, le=30),
):
    ensure_data_loaded()

    best = await tmdb_search_first(query)
    if not best:
        raise HTTPException(404, f"No TMDB movie found for: '{query}'")

    tmdb_id = int(best["id"])
    details = await tmdb_movie_details(tmdb_id)

    recs  = tfidf_recommend_titles(details.title, top_n=tfidf_top_n) \
         or tfidf_recommend_titles(query, top_n=tfidf_top_n)
    cards = await asyncio.gather(*[attach_tmdb_card(t) for t, _ in recs])

    tfidf_items = [
        TFIDFRecItem(title=title, score=round(score, 4), tmdb=card)
        for (title, score), card in zip(recs, cards)
    ]

    genre_recs: List[TMDBMovieCard] = []
    if details.genres:
        genre_id = details.genres[0]["id"]
        discover = await tmdb_get(
            "/discover/movie",
            {"with_genres": genre_id, "language": "en-US", "sort_by": "popularity.desc", "page": 1},
        )
        all_cards  = await tmdb_cards_from_results(discover.get("results", []), limit=genre_limit)
        genre_recs = [c for c in all_cards if c.tmdb_id != details.tmdb_id]

    return SearchBundleResponse(
        query=query,
        movie_details=details,
        tfidf_recommendations=tfidf_items,
        genre_recommendations=genre_recs,
    )


# =========================
# ANALYTICS ROUTES
# =========================
@app.get("/analytics/overview", response_model=OverviewStats)
def analytics_overview():
    ensure_data_loaded()
    _ensure_df()
    total       = len(df)
    avg_rating  = round(float(df["vote_average"].mean()), 2)
    avg_pop     = round(float(df["popularity"].mean()), 2)
    pct_high    = round(len(df[df["vote_average"] >= 7]) / total * 100, 1)
    rating_dist = _rating_dist(df)
    genre_stats = _genre_stats(df)
    top10 = df.nlargest(10, "popularity")[["title", "vote_average", "popularity", "genres"]].copy()
    top10_rows = [
        MovieRow(
            title=str(r["title"]),
            vote_average=round(float(r["vote_average"]), 1),
            popularity=round(float(r["popularity"]), 1),
            genres=str(r["genres"]),
        )
        for _, r in top10.iterrows()
    ]
    return OverviewStats(
        total_movies=total, avg_rating=avg_rating, avg_popularity=avg_pop,
        pct_high=pct_high, rating_dist=rating_dist,
        genre_stats=genre_stats, top10_popular=top10_rows,
    )


@app.get("/analytics/filtered", response_model=FilteredStats)
def analytics_filtered(
    min_rating: float = Query(0.0),
    max_rating: float = Query(10.0),
    genre:      str   = Query("All"),
    min_pop:    float = Query(0.0),
):
    ensure_data_loaded()
    frame = _apply_filters(min_rating, max_rating, genre, min_pop)
    if len(frame) == 0:
        return FilteredStats(total=0, avg_rating=0.0, avg_popularity=0.0,
                             pct_high=0.0, rating_dist=[], popularity_by_rating=[])
    total      = len(frame)
    avg_rating = round(float(frame["vote_average"].mean()), 2)
    avg_pop    = round(float(frame["popularity"].mean()), 2)
    pct_high   = round(len(frame[frame["vote_average"] >= 7]) / total * 100, 1)
    rating_dist = _rating_dist(frame)
    pool = frame[frame["popularity"] <= 300].copy()
    bins2   = [0, 2, 4, 5, 6, 7, 8, 9, 10.01]
    labels2 = ["0-2", "2-4", "4-5", "5-6", "6-7", "7-8", "8-9", "9-10"]
    pool["bucket"] = pd.cut(pool["vote_average"], bins=bins2, labels=labels2, right=False)
    grp = pool.groupby("bucket", observed=True)["popularity"].mean().reset_index()
    grp.columns = ["rating_group", "avg_popularity"]
    grp["avg_popularity"] = grp["avg_popularity"].round(2)
    return FilteredStats(
        total=total, avg_rating=avg_rating, avg_popularity=avg_pop,
        pct_high=pct_high, rating_dist=rating_dist,
        popularity_by_rating=grp.to_dict(orient="records"),
    )


@app.get("/analytics/recommend", response_model=RecommendResponse)
async def analytics_recommend(
    genre:      str   = Query(...),
    min_rating: float = Query(6.5),
    top_n:      int   = Query(50, ge=10, le=200),
):
    ensure_data_loaded()
    _ensure_df()
    rec_df = df[
        df["genres"].str.contains(genre, na=False) &
        (df["vote_average"] >= min_rating)
    ].copy()
    total_found = len(rec_df)
    if total_found == 0:
        return RecommendResponse(total_found=0, top_picks=[], highest_rated=[], trending=[])

    rec_df["score"] = (
        rec_df["vote_average"] * 0.7 +
        (rec_df["popularity"] / rec_df["popularity"].max()) * 3
    )
    top_recs_df = rec_df.nlargest(top_n, "score")
    trending_df = rec_df.nlargest(top_n, "popularity")
    similar_df  = (
        rec_df[rec_df["vote_average"] >= min_rating + 0.5].nlargest(top_n, "vote_average")
        if min_rating < 9.5 else rec_df.nlargest(top_n, "vote_average")
    )

    global_seen: set = set()

    def dedup(frame: pd.DataFrame, n: int = 8) -> pd.DataFrame:
        rows = []
        for _, row in frame.iterrows():
            t = str(row["title"]).strip().lower()
            if t not in global_seen:
                global_seen.add(t)
                rows.append(row)
            if len(rows) >= n:
                break
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    top_df      = dedup(top_recs_df)
    similar_df  = dedup(similar_df)
    trending_df = dedup(trending_df)

    all_titles = (
        list(top_df["title"])      if len(top_df)      > 0 else []
    ) + (
        list(similar_df["title"])  if len(similar_df)  > 0 else []
    ) + (
        list(trending_df["title"]) if len(trending_df) > 0 else []
    )
    poster_results = await asyncio.gather(*[tmdb_poster_for_title(t) for t in all_titles])
    poster_map     = dict(zip(all_titles, poster_results))

    def to_items(frame: pd.DataFrame) -> List[RecommendItem]:
        if len(frame) == 0:
            return []
        return [
            RecommendItem(
                title=str(r["title"]),
                vote_average=round(float(r["vote_average"]), 1),
                popularity=round(float(r["popularity"]), 1),
                genres=str(r["genres"]),
                poster_url=poster_map.get(str(r["title"])),
            )
            for _, r in frame.iterrows()
        ]

    return RecommendResponse(
        total_found=total_found,
        top_picks=to_items(top_df),
        highest_rated=to_items(similar_df),
        trending=to_items(trending_df),
    )


@app.get("/analytics/titles", response_model=AllTitlesResponse)
def analytics_titles():
    ensure_data_loaded()
    _ensure_df()
    titles = sorted(df["title"].dropna().unique().tolist())
    return AllTitlesResponse(titles=titles)


@app.get("/analytics/compare", response_model=CompareResponse)
async def analytics_compare(
    title1: str = Query(..., min_length=1),
    title2: str = Query(..., min_length=1),
):
    ensure_data_loaded()
    _ensure_df()

    def get_row(title: str) -> pd.Series:
        matches = df[df["title"] == title]
        if len(matches) == 0:
            raise HTTPException(404, f"Movie not found in dataset: '{title}'")
        return matches.iloc[0]

    r1 = get_row(title1)
    r2 = get_row(title2)

    poster1, poster2 = await asyncio.gather(
        tmdb_poster_for_title(title1),
        tmdb_poster_for_title(title2),
    )

    def build(row: pd.Series, poster: Optional[str]) -> CompareMovieData:
        genres = [w.strip() for w in str(row["genres"]).split() if w.strip()]
        return CompareMovieData(
            title=str(row["title"]),
            vote_average=round(float(row["vote_average"]), 1),
            popularity=round(float(row["popularity"]), 1),
            genres=genres,
            overview_len=len(str(row.get("overview", "")).split()),
            poster_url=poster,
        )

    return CompareResponse(movie1=build(r1, poster1), movie2=build(r2, poster2))