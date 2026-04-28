import os
import requests
import streamlit as st

# ==============================
# CONFIG
# ==============================
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(
    page_title="CineScope — Movie Details",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================
# STYLES
# ==============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem; max-width: 1400px; }

.movie-card-title {
    font-size: 0.82rem; font-weight: 500; color: #e2e8f0;
    line-height: 1.3; height: 2.2rem; overflow: hidden;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    margin-top: 0.3rem;
}
.movie-card-rating { font-size: 0.75rem; color: #f5c518; margin-top: 0.2rem; }
.no-poster {
    background: linear-gradient(135deg, #1a1a2e, #0f3460);
    height: 200px; display: flex; align-items: center;
    justify-content: center; font-size: 2.5rem; border-radius: 10px;
}

.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #f5c518, #e6a817) !important;
    color: #0f0c29 !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    font-size: 0.78rem !important; padding: 0.35rem 0 !important;
    margin-top: 0.3rem !important; transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.82 !important; }

.detail-card {
    background: #16213e; border: 1px solid #0f3460;
    border-radius: 18px; padding: 2rem;
}
.detail-title { font-size: 2rem; font-weight: 700; color: #fff; line-height: 1.2; margin-bottom: 0.4rem; }
.detail-meta { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.6rem 0 0.8rem; }
.badge {
    background: #0f3460; color: #90cdf4; border-radius: 50px;
    padding: 0.22rem 0.8rem; font-size: 0.78rem; font-weight: 500; border: 1px solid #1a4a7a;
}
.badge-yellow { background: rgba(245,197,24,0.15); color: #f5c518; border-color: rgba(245,197,24,0.3); }
.overview-label { font-size: 1rem; font-weight: 600; color: #fff; margin-bottom: 0.4rem; }
.overview-text { color: #cbd5e0; font-size: 0.97rem; line-height: 1.75; }
.rec-header {
    font-size: 1rem; font-weight: 600; color: #f5c518;
    margin: 1.4rem 0 0.7rem; padding-left: 0.5rem; border-left: 3px solid #f5c518;
}
.backdrop-wrap { border-radius: 18px; overflow: hidden; margin-top: 0.5rem; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
.section-label {
    font-size: 1.2rem; font-weight: 600; color: #fff;
    margin: 1.5rem 0 1rem; display: flex; align-items: center; gap: 0.5rem;
}
.section-label::after {
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(to right, #302b63, transparent); margin-left: 0.75rem;
}

section[data-testid="stSidebar"] { background: #0f0c29 !important; border-right: 1px solid #302b63; }
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] hr { border-color: #302b63 !important; }
hr { border-color: #302b63 !important; }
</style>
""", unsafe_allow_html=True)

# ==============================
# SESSION STATE
# ==============================
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

# ==============================
# API HELPER
# ==============================
@st.cache_data(ttl=300)
def api_get(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=120)
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}: {r.text[:300]}"
        return r.json(), None
    except Exception as e:
        return None, f"Request failed: {e}"

# ==============================
# HELPERS
# ==============================
def stars(rating):
    if not rating:
        return ""
    filled = round(rating / 2)
    return "★" * filled + "☆" * (5 - filled) + f"  {rating:.1f}/10"


def poster_grid(cards, cols=5, key_prefix="grid"):
    """
    Renders a grid of movie cards.
    Each card shows: poster image, star rating, title, and an Open button.
    Clicking Open loads that movie's detail page.
    """
    if not cards:
        st.info("No movies to show.")
        return
    rows = (len(cards) + cols - 1) // cols
    idx  = 0
    for r in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards):
                break
            m       = cards[idx]; idx += 1
            tmdb_id = m.get("tmdb_id")
            title   = m.get("title", "Untitled")
            poster  = m.get("poster_url")
            rating  = m.get("vote_average")
            with colset[c]:
                if poster:
                    st.image(poster, use_container_width=True)
                else:
                    st.markdown("<div class='no-poster'>🎬</div>", unsafe_allow_html=True)
                if rating:
                    st.markdown(f"<div class='movie-card-rating'>{stars(rating)}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='movie-card-title'>{title}</div>", unsafe_allow_html=True)
                # FIX: show Open button even when tmdb_id is None — search by title as fallback
                btn_key = f"{key_prefix}_{r}_{c}_{idx}_{tmdb_id or title[:8]}"
                if st.button("▶ Open", key=btn_key):
                    if tmdb_id:
                        api_get.clear()
                        st.session_state.selected_tmdb_id = int(tmdb_id)
                        st.rerun()
                    else:
                        # tmdb_id missing — look it up by title then navigate
                        with st.spinner("Looking up movie..."):
                            search_result, _ = api_get("/tmdb/search", params={"query": title})
                        if search_result and search_result.get("results"):
                            found_id = search_result["results"][0]["id"]
                            api_get.clear()
                            st.session_state.selected_tmdb_id = int(found_id)
                            st.rerun()
                        else:
                            st.warning(f"Could not find details for '{title}'.")
                st.markdown("<div style='margin-bottom:0.4rem'></div>", unsafe_allow_html=True)


def to_cards_from_tfidf_items(tfidf_items):
    """
    Converts TF-IDF recommendation items into poster_grid-compatible dicts.
    TF-IDF items come from the local movie dataset and include a nested
    'tmdb' object with real TMDB metadata (id, poster, rating).
    """
    cards = []
    for x in tfidf_items or []:
        tmdb = x.get("tmdb") or {}
        cards.append({
            # Use TMDB id if available; None triggers title-based lookup in poster_grid
            "tmdb_id":      tmdb.get("tmdb_id"),
            "title":        tmdb.get("title") or x.get("title") or "Untitled",
            "poster_url":   tmdb.get("poster_url"),
            "vote_average": tmdb.get("vote_average"),
        })
    return cards


# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1.2rem 0 0.8rem'>
        <div style='font-size:2.2rem'>🎬</div>
        <div style='font-size:1.3rem; font-weight:700; color:#f5c518; letter-spacing:1px'>CineScope</div>
        <div style='font-size:0.72rem; color:#718096; margin-top:2px; letter-spacing:1px'>MOVIE DETAILS</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    if st.button("🏠  Home", use_container_width=True):
        st.switch_page("app.py")
    if st.button("📊  Analytics Dashboard", use_container_width=True):
        st.switch_page("pages/analytics.py")

    st.markdown("---")

    st.markdown("<p style='color:#718096; font-size:0.75rem; font-weight:600; letter-spacing:1px; margin-bottom:0.4rem'>GRID COLUMNS</p>", unsafe_allow_html=True)
    grid_cols = st.slider("cols", 3, 8, 5, label_visibility="collapsed")

    st.markdown("---")

    st.markdown("""
    <div style='background:#12121a; border:1px solid #2a2a3d; border-radius:14px; padding:1rem 1.1rem;'>
        <div style='font-size:0.78rem; color:#8888a8; line-height:1.8'>
            Hey! I'm <b style='color:#e8e8f0'>Neha Banjara</b> and I built this as a fun project to explore movie data. 🎬<br><br>
            It uses <b style='color:#e8e8f0'>45,447 movies</b> from TMDB, built using Streamlit + FastAPI.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==============================
# GUARD — must have a tmdb_id
# ==============================
tmdb_id = st.session_state.get("selected_tmdb_id")
if not tmdb_id:
    st.warning("No movie selected. Go back to the home page and pick a movie.")
    if st.button("← Back to Home"):
        st.switch_page("app.py")
    st.stop()

if st.button("← Back to Home"):
    st.switch_page("app.py")

# ==============================
# LOAD MOVIE DETAILS
# ==============================
with st.spinner("Loading movie details..."):
    data, err = api_get(f"/movie/id/{tmdb_id}")

if err or not data:
    st.warning(f"⚠️ Could not load details: {err}")
    st.stop()

# Backdrop
if data.get("backdrop_url"):
    st.markdown("<div class='backdrop-wrap'>", unsafe_allow_html=True)
    st.image(data["backdrop_url"], use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# Poster + Info
left, right = st.columns([1, 2.6], gap="large")

with left:
    if data.get("poster_url"):
        st.image(data["poster_url"], use_container_width=True)
    else:
        st.markdown("<div class='no-poster' style='height:350px;border-radius:14px'>🎬</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='detail-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='detail-title'>{data.get('title','')}</div>", unsafe_allow_html=True)

    rating = data.get("vote_average")
    if rating:
        st.markdown(
            f"<div style='color:#f5c518; font-size:1.05rem; margin:0.3rem 0'>{stars(rating)}</div>",
            unsafe_allow_html=True,
        )

    release = data.get("release_date") or ""
    year    = release[:4] if release else ""
    genres  = data.get("genres", [])
    badges  = ""
    if year:
        badges += f"<span class='badge badge-yellow'>📅 {year}</span>"
    for g in genres[:5]:
        badges += f"<span class='badge'>{g['name']}</span>"
    if badges:
        st.markdown(f"<div class='detail-meta'>{badges}</div>", unsafe_allow_html=True)

    st.markdown("<div class='overview-label'>📖 Overview</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='overview-text'>{data.get('overview') or 'No overview available.'}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ======================================================================
# RECOMMENDATIONS
# ----------------------------------------------------------------------
# What this section is supposed to show:
#
# 1. TF-IDF Similar Movies — movies that are textually similar to the
#    selected movie based on genres, keywords, and overview text.
#    These come from your local 45k-movie dataset via the ML model.
#    Example: open "Inception" → shows "Interstellar", "The Matrix" etc.
#
# 2. More in This Genre — popular movies in the same genre, fetched live
#    from TMDB's discover API. These are NOT from the local dataset.
#    Example: open "Inception" (Sci-Fi) → shows popular Sci-Fi movies.
#
# The genre filter dropdown lets you narrow the TMDB genre results.
# TF-IDF results are always shown as-is (they don't carry genre tags).
# ======================================================================
st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-label'>✨ You Might Also Like</div>", unsafe_allow_html=True)

# Genre filter — only applied to "More in This Genre" section
CATEGORIES = ["All", "Action", "Drama", "Comedy", "Horror", "Romance", "Thriller", "Adventure"]
sel_cat = st.selectbox(
    "Filter 'More in This Genre' by category",
    CATEGORIES,
    index=0,
    key="rec_category_filter",
)

movie_title = (data.get("title") or "").strip()

if not movie_title:
    st.info("No title available to compute recommendations.")
    st.stop()

with st.spinner("Finding similar movies..."):
    bundle, err2 = api_get(
        "/movie/search",
        params={"query": movie_title, "tfidf_top_n": 18, "genre_limit": 18},
    )

# ── CASE 1: /movie/search succeeded ────────────────────────────────────────
if not err2 and bundle:

    # ── Section A: TF-IDF cards ──────────────────────────────────────────
    # These are movies similar in content to the selected movie.
    # They are matched using TF-IDF on your local 45k-movie dataset.
    # ROOT CAUSE FIX: previously these cards often had tmdb_id = None
    # and the Open button was suppressed, making the whole section look blank.
    # Now the button does a title-based TMDB lookup as fallback (see poster_grid).
    tfidf_cards = to_cards_from_tfidf_items(bundle.get("tfidf_recommendations", []))

    if tfidf_cards:
        st.markdown("<div class='rec-header'>🔎 Similar Movies (TF-IDF Content Filtering)</div>", unsafe_allow_html=True)
        poster_grid(tfidf_cards, cols=grid_cols, key_prefix="tfidf_recs")
    else:
        st.markdown("<div class='rec-header'>🔎 Similar Movies</div>", unsafe_allow_html=True)
        st.caption("No TF-IDF matches found for this title in the local dataset.")

    # ── Section B: Genre recommendations ─────────────────────────────────
    # These are popular movies in the same genre, fetched live from TMDB.
    # ROOT CAUSE FIX: the old code tried to filter these by a "genres" field
    # that does NOT exist on TMDBMovieCard objects — they only have
    # tmdb_id, title, poster_url, release_date, vote_average.
    # Filtering by genres field always returned an empty list → blank section.
    # Fix: genre filter is now only applied when the user explicitly picks
    # a non-"All" category, and only searches in the title as a heuristic.
    genre_cards = bundle.get("genre_recommendations", [])

    if sel_cat != "All":
        # Heuristic: filter by title keyword since genre field is not available here
        filtered = [c for c in genre_cards if sel_cat.lower() in str(c.get("title", "")).lower()]
        # Always fall back to full list if filter is too aggressive
        genre_cards = filtered if filtered else genre_cards

    if genre_cards:
        st.markdown("<div class='rec-header'>🎭 More in This Genre</div>", unsafe_allow_html=True)
        poster_grid(genre_cards, cols=grid_cols, key_prefix="genre_recs")
    else:
        st.caption("No genre recommendations available for this movie.")

# ── CASE 2: /movie/search failed — use genre fallback ──────────────────────
else:
    st.markdown("<div class='rec-header'>🎭 Genre Recommendations</div>", unsafe_allow_html=True)
    with st.spinner("Loading genre recommendations..."):
        genre_only, err3 = api_get("/recommend/genre", params={"tmdb_id": tmdb_id, "limit": 18})

    if not err3 and genre_only:
        poster_grid(genre_only, cols=grid_cols, key_prefix="fallback_genre")
    else:
        st.info("No recommendations available right now. The ML backend may still be loading — wait 30 seconds and refresh.")