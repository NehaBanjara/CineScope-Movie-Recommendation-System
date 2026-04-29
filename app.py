import os
import requests
import streamlit as st

# ==============================
# CONFIG
# ==============================
API_BASE = os.getenv("API_BASE", "https://cinescope-movie-recommendation-system.onrender.com")
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(
    page_title="CineScope",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================
# STYLES  (unchanged)
# ==============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem; max-width: 1400px; }

.hero {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    border-radius: 16px;
    padding: 2.5rem 2rem 2rem;
    margin: 0.5rem 0 2rem 0;
    text-align: center;
}
.hero h1 { font-size: 2.8rem; font-weight: 700; color: #fff; margin: 0; letter-spacing: -0.5px; }
.hero h1 span { color: #f5c518; }
.hero p { color: #a0aec0; margin: 0.4rem 0 0; font-size: 1rem; }

.stTextInput > div > div > input {
    background: #1a1a2e !important;
    border: 2px solid #302b63 !important;
    border-radius: 50px !important;
    color: #fff !important;
    padding: 0.75rem 1.5rem !important;
    font-size: 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #f5c518 !important;
    box-shadow: 0 0 0 3px rgba(245,197,24,0.15) !important;
}
.stTextInput > label { color: #a0aec0 !important; font-size: 0.85rem !important; }

.stSelectbox > div > div {
    background: #1a1a2e !important;
    border: 1.5px solid #302b63 !important;
    border-radius: 12px !important;
    color: #fff !important;
}

.section-label {
    font-size: 1.2rem; font-weight: 600; color: #fff;
    margin: 1.5rem 0 1rem; display: flex; align-items: center; gap: 0.5rem;
}
.section-label::after {
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(to right, #302b63, transparent); margin-left: 0.75rem;
}

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

section[data-testid="stSidebar"] {
    background: #0f0c29 !important;
    border-right: 1px solid #302b63;
}
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
                if tmdb_id and st.button("▶ Open", key=f"{key_prefix}_{r}_{c}_{idx}_{tmdb_id}"):
                    st.session_state.selected_tmdb_id = int(tmdb_id)
                    st.switch_page("pages/recommendations.py")
                st.markdown("<div style='margin-bottom:0.4rem'></div>", unsafe_allow_html=True)


def parse_tmdb_search_to_cards(data, keyword: str, limit: int = 24):
    keyword_l = keyword.strip().lower()
    if isinstance(data, dict) and "results" in data:
        raw_items = []
        for m in data.get("results") or []:
            title   = (m.get("title") or "").strip()
            tmdb_id = m.get("id")
            if not title or not tmdb_id:
                continue
            raw_items.append({
                "tmdb_id":      int(tmdb_id),
                "title":        title,
                "poster_url":   f"{TMDB_IMG}{m['poster_path']}" if m.get("poster_path") else None,
                "release_date": m.get("release_date", ""),
                "vote_average": m.get("vote_average"),
            })
    elif isinstance(data, list):
        raw_items = []
        for m in data:
            tmdb_id = m.get("tmdb_id") or m.get("id")
            title   = (m.get("title") or "").strip()
            if not title or not tmdb_id:
                continue
            raw_items.append({
                "tmdb_id":      int(tmdb_id),
                "title":        title,
                "poster_url":   m.get("poster_url"),
                "release_date": m.get("release_date", ""),
                "vote_average": m.get("vote_average"),
            })
    else:
        return [], []

    matched    = [x for x in raw_items if keyword_l in x["title"].lower()]
    final_list = matched if matched else raw_items

    suggestions = []
    for x in final_list[:10]:
        year  = (x.get("release_date") or "")[:4]
        label = f"{x['title']} ({year})" if year else x["title"]
        suggestions.append((label, x["tmdb_id"]))

    cards = [
        {
            "tmdb_id":      x["tmdb_id"],
            "title":        x["title"],
            "poster_url":   x["poster_url"],
            "vote_average": x.get("vote_average"),
        }
        for x in final_list[:limit]
    ]
    return suggestions, cards

# ==============================
# GENRE LIST  (fetched from backend overview, cached)
# ==============================
@st.cache_data(ttl=600)
def get_genre_list():
    data, err = api_get("/analytics/overview")
    if err or not data:
        # Fallback static list if backend overview endpoint not available
        return ["Action", "Adventure", "Animation", "Comedy", "Crime",
                "Drama", "Family", "Fantasy", "Horror", "Romance",
                "Science Fiction", "Thriller"]
    return [g["genre"] for g in data.get("genre_stats", [])]

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1.2rem 0 0.8rem'>
        <div style='font-size:2.2rem'>🎬</div>
        <div style='font-size:1.3rem; font-weight:700; color:#f5c518; letter-spacing:1px'>CineScope</div>
        <div style='font-size:0.72rem; color:#718096; margin-top:2px'>Movie Recommender</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<p style='color:#718096; font-size:0.75rem; font-weight:600; letter-spacing:1px; margin-bottom:0.4rem'>GRID COLUMNS</p>", unsafe_allow_html=True)
    grid_cols = st.slider("cols", 3, 8, 5, label_visibility="collapsed")

    # FIX 3: Genre-based home feed — replaces the old "Home Category" selectbox
    st.markdown("<p style='color:#718096; font-size:0.75rem; font-weight:600; letter-spacing:1px; margin: 0.9rem 0 0.4rem'>BROWSE BY GENRE</p>", unsafe_allow_html=True)
    genre_list    = get_genre_list()
    selected_genre = st.selectbox(
        "genre",
        genre_list,
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    # Navigation to Analytics Dashboard
    st.markdown("<p style='color:#718096; font-size:0.75rem; font-weight:600; letter-spacing:1px; margin-bottom:0.5rem'>TOOLS</p>", unsafe_allow_html=True)
    if st.button("📊 Analytics Dashboard", use_container_width=True):
        # FIX 1: correct path — file is analytics.py not Analytics.py
        st.switch_page("pages/analytics.py")

    st.markdown("---")

    # FIX 4: Human-friendly about section
    st.markdown("""
    <div style='background:#12121a; border:1px solid #2a2a3d; border-radius:14px; padding:1rem 1.1rem; margin-top:0.5rem'>
        <div style='font-size:0.78rem; color:#8888a8; line-height:1.8'>
            Hey! I'm <b style='color:#e8e8f0'>Neha Banjara</b> and I built this as a fun project to explore movie data. 🎬<br><br>
            It uses <b style='color:#e8e8f0'>45,447 movies</b> from TMDB, built using Streamlit + FastAPI.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================
# HERO BANNER
# ==============================
st.markdown("""
<div class='hero'>
    <h1>🎬 Cine<span>Scope</span></h1>
    <p>✨ Movie Recommender &nbsp;·&nbsp; Discover movies you'll love</p>
</div>
""", unsafe_allow_html=True)

# ==============================
# SEARCH
# ==============================
col_s, _ = st.columns([3, 1])
with col_s:
    typed = st.text_input(
        "search",
        placeholder="🔍  Search a movie... e.g. Batman, Inception, Interstellar...",
        key="search_query",
        label_visibility="collapsed",
    )

query = (typed or "").strip()

if query:
    if len(query) < 2:
        st.caption("Type at least 2 characters...")
    else:
        with st.spinner("🔍 Searching..."):
            data, err = api_get("/tmdb/search", params={"query": query})

        if err or data is None:
            st.warning("⚠️ Could not reach movie database. Check your internet connection.")
        else:
            suggestions, cards = parse_tmdb_search_to_cards(data, query, limit=24)

            if suggestions:
                col_dd, _ = st.columns([3, 1])
                with col_dd:
                    labels   = ["🎬 Select a movie to see full details →"] + [s[0] for s in suggestions]
                    selected = st.selectbox("pick", labels, index=0, label_visibility="collapsed")
                if selected != "🎬 Select a movie to see full details →":
                    label_to_id = {s[0]: s[1] for s in suggestions}
                    st.session_state.selected_tmdb_id = label_to_id[selected]
                    st.switch_page("pages/recommendations.py")
            else:
                st.info("No results found. Try a different keyword.")

            if cards:
                st.markdown(
                    f"<div class='section-label'>🔍 Results for &quot;{query}&quot;</div>",
                    unsafe_allow_html=True,
                )
                poster_grid(cards, cols=grid_cols, key_prefix="search_results")
    st.stop()

# ==============================
# FIX 3: GENRE-BASED HOME FEED
# Replaces the old trending/popular/top_rated category dropdown.
# Uses /discover/genre endpoint from TMDB via backend.
# ==============================
st.markdown(
    f"<div class='section-label'>🎭 {selected_genre} Movies</div>",
    unsafe_allow_html=True,
)

with st.spinner(f"Loading {selected_genre} movies..."):
    # Use the analytics/recommend endpoint which supports genre filtering
    genre_cards_raw, err = api_get(
        "/analytics/recommend",
        params={"genre": selected_genre, "min_rating": 5.0, "top_n": 50},
    )

if err or not genre_cards_raw:
    # Fallback: try TMDB discover via existing home endpoint with trending
    with st.spinner("Loading movies..."):
        fallback_cards, err2 = api_get("/home", params={"category": "popular", "limit": 24})
    if err2 or not fallback_cards:
        st.warning("⚠️ Could not load movies. Make sure FastAPI backend is running on port 8000.")
        st.stop()
    poster_grid(fallback_cards, cols=grid_cols, key_prefix="home_fallback")
else:
    # Convert analytics/recommend response items to poster_grid format
    # The endpoint returns {total_found, top_picks, highest_rated, trending}
    # We merge top_picks + highest_rated and deduplicate by tmdb_id
    seen_ids  = set()
    all_cards = []
    for bucket in ("top_picks", "highest_rated", "trending"):
        for item in genre_cards_raw.get(bucket, []):
            # Items from analytics/recommend don't have tmdb_id directly;
            # we need to look them up. Instead use the /tmdb/search per title.
            # To keep it fast, build display cards from what we have.
            title = item.get("title", "")
            key   = title.lower().strip()
            if key and key not in seen_ids:
                seen_ids.add(key)
                all_cards.append({
                    "tmdb_id":      None,   # no tmdb_id in this response
                    "title":        title,
                    "poster_url":   item.get("poster_url"),
                    "vote_average": item.get("vote_average"),
                })

    if all_cards:
        poster_grid(all_cards[:24], cols=grid_cols, key_prefix="genre_feed")
    else:
        st.info(f"No movies found for genre '{selected_genre}'. Try another genre.")