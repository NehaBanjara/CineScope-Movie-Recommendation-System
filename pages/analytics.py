import os
import requests
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
API_BASE = os.getenv("API_BASE", "https://cinescope-movie-recommendation-system.onrender.com")

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="CineScope — Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────
C_BG     = "#0a0a0f"
C_SURFACE= "#12121a"
C_CARD   = "#16161f"
C_BORDER = "#2a2a3d"
C_GOLD   = "#f5c518"
C_PURPLE = "#7c6fcd"
C_TEAL   = "#1db8a0"
C_CORAL  = "#e05c5c"
C_BLUE   = "#4a9eff"
C_TEXT   = "#e8e8f0"
C_MUTED  = "#8888a8"
C_GREEN  = "#22c55e"

def pl(**kw):
    base = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=C_TEXT, size=12),
        title_font=dict(size=14, color=C_TEXT),
        xaxis=dict(gridcolor=C_BORDER, zerolinecolor=C_BORDER, tickfont=dict(color=C_MUTED)),
        yaxis=dict(gridcolor=C_BORDER, zerolinecolor=C_BORDER, tickfont=dict(color=C_MUTED)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=C_MUTED)),
        margin=dict(l=16, r=16, t=40, b=16),
        hoverlabel=dict(bgcolor=C_CARD, font_color=C_TEXT, bordercolor=C_BORDER),
    )
    for k in ("xaxis", "yaxis", "legend"):
        if k in kw:
            base[k] = {**base[k], **kw.pop(k)}
    base.update(kw)
    return base

# ─────────────────────────────────────────
# STYLES  (identical to original dashboard)
# ─────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap');
html,body,[class*="css"]{{font-family:'DM Sans',sans-serif;background:{C_BG};color:{C_TEXT};}}
.block-container{{padding:0 2rem 3rem;max-width:1500px;}}
section[data-testid="stSidebar"]{{background:{C_SURFACE}!important;border-right:1px solid {C_BORDER};}}
section[data-testid="stSidebar"] *{{color:{C_TEXT}!important;}}
section[data-testid="stSidebar"] hr{{border-color:{C_BORDER}!important;}}
#MainMenu,footer,header{{visibility:hidden;}}
.stSelectbox>div>div{{background:{C_CARD}!important;border:1px solid {C_BORDER}!important;border-radius:10px!important;}}
.stTabs [data-baseweb="tab-list"]{{background:{C_SURFACE};border-radius:12px;padding:4px;gap:4px;border:1px solid {C_BORDER};}}
.stTabs [data-baseweb="tab"]{{background:transparent;border-radius:8px;color:{C_MUTED};font-size:0.85rem;padding:6px 16px;}}
.stTabs [aria-selected="true"]{{background:{C_GOLD}!important;color:#0a0a0f!important;font-weight:600;}}
hr{{border-color:{C_BORDER}!important;}}
.metric-card{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:16px;padding:1.4rem 1.2rem;text-align:center;transition:transform .2s,border-color .2s;}}
.metric-card:hover{{transform:translateY(-3px);border-color:{C_GOLD};}}
.metric-num{{font-size:2rem;font-weight:700;color:{C_GOLD};font-family:'DM Serif Display';}}
.metric-label{{font-size:0.78rem;color:{C_MUTED};text-transform:uppercase;letter-spacing:1px;margin-top:4px;}}
.metric-sub{{font-size:0.82rem;color:{C_TEAL};margin-top:6px;font-weight:500;}}
.section-hdr{{font-family:'DM Serif Display';font-size:1.4rem;color:{C_TEXT};margin:1.8rem 0 1rem;display:flex;align-items:center;gap:.6rem;}}
.section-hdr span{{font-size:0.7rem;font-family:'DM Sans';color:{C_MUTED};letter-spacing:1.5px;text-transform:uppercase;border:1px solid {C_BORDER};padding:3px 10px;border-radius:20px;}}
.chart-card{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:16px;padding:1.2rem;}}
.movie-table{{width:100%;border-collapse:collapse;}}
.movie-table th{{background:{C_SURFACE};color:{C_MUTED};font-size:0.72rem;letter-spacing:1px;text-transform:uppercase;padding:10px 14px;text-align:left;border-bottom:1px solid {C_BORDER};}}
.movie-table td{{padding:10px 14px;font-size:0.88rem;color:{C_TEXT};border-bottom:1px solid {C_BORDER}33;}}
.movie-table tr:hover td{{background:{C_BORDER}33;}}
.rating-pill{{background:rgba(245,197,24,0.15);color:{C_GOLD};padding:3px 10px;border-radius:20px;font-size:0.8rem;font-weight:600;}}
.genre-tag{{background:rgba(124,111,205,0.15);color:{C_PURPLE};padding:2px 8px;border-radius:20px;font-size:0.75rem;display:inline-block;margin:1px;}}
.pop-bar{{height:6px;border-radius:3px;background:linear-gradient(to right,{C_TEAL},{C_BLUE});display:inline-block;}}
.dash-banner{{background:linear-gradient(135deg,#0f0c29,#1a1040,#0a1628);border-radius:0 0 20px 20px;padding:1.8rem 2rem 1.5rem;margin:-1rem -2rem 1.5rem;border-bottom:1px solid {C_BORDER};display:flex;align-items:center;justify-content:space-between;}}
.dash-title{{font-family:'DM Serif Display';font-size:1.8rem;color:{C_TEXT};}}
.dash-title span{{color:{C_GOLD};}}
.dash-sub{{font-size:0.82rem;color:{C_MUTED};margin-top:4px;}}
.dash-stat{{text-align:right;}}
.dash-stat-num{{font-size:1.5rem;font-weight:700;color:{C_GOLD};}}
.dash-stat-label{{font-size:0.72rem;color:{C_MUTED};}}
.rec-movie-card{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:14px;padding:1rem;margin-bottom:.6rem;transition:border-color .2s,transform .2s;}}
.rec-movie-card:hover{{border-color:{C_GOLD};transform:translateX(4px);}}
.rec-title{{font-weight:600;font-size:.95rem;color:{C_TEXT};}}
.rec-meta{{font-size:.8rem;color:{C_MUTED};margin-top:.3rem;}}
.rec-rating{{color:{C_GOLD};font-weight:600;font-size:.85rem;}}
.compare-card{{background:{C_CARD};border:2px solid {C_BORDER};border-radius:18px;padding:1.5rem;text-align:center;}}
.compare-card.winner{{border-color:{C_GOLD};}}
.compare-title{{font-size:1.2rem;font-weight:700;color:{C_TEXT};margin-bottom:.5rem;}}
.compare-big{{font-size:2.2rem;font-weight:700;color:{C_GOLD};}}
.compare-label{{font-size:.75rem;color:{C_MUTED};text-transform:uppercase;letter-spacing:1px;}}
.win-badge{{background:{C_GOLD};color:#0a0a0f;padding:3px 12px;border-radius:20px;font-size:.75rem;font-weight:700;display:inline-block;margin-bottom:.5rem;}}
.info-box{{background:{C_CARD};border:1px solid {C_BORDER};border-left:3px solid {C_GOLD};border-radius:0 12px 12px 0;padding:.8rem 1rem;font-size:.85rem;color:{C_MUTED};margin-top:.5rem;}}
.sb-about{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:14px;padding:1rem 1.1rem;margin-top:.5rem;}}
.sb-about-text{{font-size:.78rem;color:{C_MUTED};line-height:1.8;}}
.sb-about-text b{{color:{C_TEXT};font-weight:600;}}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# API HELPER
# ─────────────────────────────────────────
@st.cache_data(ttl=300)
def api_get(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=30)
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}: {r.text[:200]}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────
# LOAD GLOBAL OVERVIEW
# ─────────────────────────────────────────
with st.spinner("Loading analytics data..."):
    overview, ov_err = api_get("/analytics/overview")

if ov_err or not overview:
    st.error(f"⚠️ Could not reach backend: {ov_err}. Make sure FastAPI is running on {API_BASE}")
    st.stop()

ALL_GENRES   = ["All"] + [g["genre"] for g in overview["genre_stats"]]
TOTAL_MOVIES = overview["total_movies"]


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center;padding:1.2rem 0 0.8rem'>
        <div style='font-size:2rem'>🎬</div>
        <div style='font-family:"DM Serif Display";font-size:1.4rem;color:{C_GOLD}'>CineScope</div>
        <div style='font-size:0.72rem;color:{C_MUTED};letter-spacing:1px'>ANALYTICS DASHBOARD</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # ── Back navigation ──
    if st.button("🏠  Back to Home", use_container_width=True):
        st.switch_page("app.py")
    st.markdown("---")

    st.markdown(f"<p style='color:{C_MUTED};font-size:.72rem;letter-spacing:1px;font-weight:600'>RATING FILTER</p>", unsafe_allow_html=True)
    rating_range = st.slider("Rating", 0.0, 10.0, (0.0, 10.0), 0.5, label_visibility="collapsed")

    st.markdown(f"<p style='color:{C_MUTED};font-size:.72rem;letter-spacing:1px;font-weight:600;margin-top:1rem'>GENRE FILTER</p>", unsafe_allow_html=True)
    selected_genre = st.selectbox("Genre", ALL_GENRES, label_visibility="collapsed")

    st.markdown(f"<p style='color:{C_MUTED};font-size:.72rem;letter-spacing:1px;font-weight:600;margin-top:1rem'>MIN POPULARITY</p>", unsafe_allow_html=True)
    min_pop = st.slider("Min popularity", 0.0, 100.0, 0.0, 1.0, label_visibility="collapsed")

    st.markdown("---")
    st.markdown(
        f"<div class='sb-about'>"
        f"<div class='sb-about-text'>"
        f"Hey! I'm <b>Neha Banjara</b> and I built this as a fun project to explore movie data. 🎬<br><br>"
        f"It uses <b>{TOTAL_MOVIES:,} movies</b> from TMDB, put together with Streamlit + Plotly."
        f"</div></div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────
# FETCH FILTERED STATS
# ─────────────────────────────────────────
filtered_stats, fs_err = api_get("/analytics/filtered", params={
    "min_rating": rating_range[0],
    "max_rating": rating_range[1],
    "genre":      selected_genre,
    "min_pop":    min_pop,
})

if fs_err or not filtered_stats or filtered_stats.get("total", 0) == 0:
    st.warning("⚠️ No movies match your filters. Please adjust the sidebar sliders.")
    st.stop()

f_total    = filtered_stats["total"]
f_avg_r    = filtered_stats["avg_rating"]
f_avg_p    = filtered_stats["avg_popularity"]
f_pct_hi   = filtered_stats["pct_high"]
f_rat_dist = filtered_stats["rating_dist"]
f_pop_by_r = filtered_stats["popularity_by_rating"]


# ─────────────────────────────────────────
# BANNER + KPI
# ─────────────────────────────────────────
st.markdown(f"""
<div class='dash-banner'>
    <div>
        <div class='dash-title'>Cine<span>Scope</span> Analytics</div>
        <div class='dash-sub'>Movie dataset insights — {TOTAL_MOVIES:,} films analyzed</div>
    </div>
    <div class='dash-stat'>
        <div class='dash-stat-num'>{f_total:,}</div>
        <div class='dash-stat-label'>movies in current filter</div>
    </div>
</div>
""", unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)
for col, num, label, sub in [
    (k1, f"{f_total:,}", "Total Movies",   "in selection"),
    (k2, f_avg_r,        "Avg Rating",     "out of 10"),
    (k3, f_avg_p,        "Avg Popularity", "TMDB score"),
    (k4, f"{f_pct_hi}%", "Rated 7+",      "high quality"),
    (k5, "12",           "Genres",         "analyzed"),
]:
    with col:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-num'>{num}</div>
            <div class='metric-label'>{label}</div>
            <div class='metric-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────
# TABS
# ─────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🎭 Genre Analysis",
    "⭐ Ratings",
    "🎬 Recommend Me",
    "⚡ Compare Movies",
])


# ══════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════
with tab1:
    st.markdown("<div class='section-hdr'>Overview <span>DATASET SNAPSHOT</span></div>", unsafe_allow_html=True)

    global_rat_dist = overview["rating_dist"]
    genre_stats     = overview["genre_stats"]

    c1, c2 = st.columns(2)

    with c1:
        ranges = [b["range"] for b in global_rat_dist]
        counts = [b["count"] for b in global_rat_dist]
        fig = go.Figure(go.Bar(
            x=ranges, y=counts,
            marker=dict(color=counts,
                        colorscale=[[0, C_PURPLE], [0.5, C_GOLD], [1, C_TEAL]],
                        showscale=False, line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>Movies: %{y:,}<extra></extra>",
        ))
        fig.update_layout(pl(title=f"Rating Distribution — All {TOTAL_MOVIES:,} Movies",
                             xaxis_title="Rating Range", yaxis_title="Count", bargap=0.15))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        top6     = genre_stats[:6]
        g_labels = [g["genre"] for g in top6]
        g_counts = [g["count"] for g in top6]
        fig2 = go.Figure(go.Pie(
            labels=g_labels, values=g_counts, hole=0.55,
            marker=dict(colors=[C_GOLD, C_PURPLE, C_TEAL, C_CORAL, C_BLUE, "#a78bfa"],
                        line=dict(color=C_BG, width=2)),
            textinfo="label+percent", textfont=dict(size=11, color=C_TEXT),
            hovertemplate="<b>%{label}</b><br>%{value:,} movies (%{percent})<extra></extra>",
        ))
        fig2.add_annotation(text=f"<b>{TOTAL_MOVIES:,}</b><br>movies", x=0.5, y=0.5,
                            showarrow=False, font=dict(size=13, color=C_TEXT))
        fig2.update_layout(pl(title="Genre Distribution (Top 6)",
                              legend=dict(orientation="v", x=1.05, y=0.5)))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div class='section-hdr'>Popularity vs Rating <span>BY GROUP</span></div>", unsafe_allow_html=True)
    if f_pop_by_r:
        rg_labels = [r["rating_group"]   for r in f_pop_by_r]
        rg_vals   = [r["avg_popularity"] for r in f_pop_by_r]
        fig3 = go.Figure(go.Bar(
            x=rg_labels, y=rg_vals,
            marker=dict(color=rg_vals,
                        colorscale=[[0, C_PURPLE], [0.5, C_GOLD], [1, C_TEAL]],
                        showscale=False, line=dict(width=0)),
            text=[f"{v:.1f}" for v in rg_vals],
            textposition="outside", textfont=dict(color=C_MUTED, size=11),
            hovertemplate="<b>Rating %{x}</b><br>Avg Popularity: %{y:.2f}<extra></extra>",
        ))
        fig3.update_layout(pl(title="Average Popularity per Rating Group",
                              xaxis_title="Rating Range", yaxis_title="Avg Popularity", bargap=0.2))
        st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════
# TAB 2 — GENRE ANALYSIS
# ══════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-hdr'>Genre Analysis <span>BREAKDOWN</span></div>", unsafe_allow_html=True)

    genre_stats  = overview["genre_stats"]
    g_names      = [g["genre"]      for g in genre_stats]
    g_counts     = [g["count"]      for g in genre_stats]
    g_avg_rating = [g["avg_rating"] for g in genre_stats]

    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure(go.Bar(
            y=g_names, x=g_counts, orientation="h",
            marker=dict(color=g_counts,
                        colorscale=[[0, C_PURPLE], [1, C_GOLD]],
                        showscale=False, line=dict(width=0)),
            text=[f"{v:,}" for v in g_counts],
            textposition="outside", textfont=dict(color=C_MUTED, size=11),
            hovertemplate="<b>%{y}</b><br>%{x:,} movies<extra></extra>",
        ))
        fig.update_layout(pl(title="Movies per Genre", height=400,
                             yaxis=dict(autorange="reversed")))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        paired         = sorted(zip(g_avg_rating, g_names), key=lambda x: x[0])
        sorted_ratings = [p[0] for p in paired]
        sorted_names   = [p[1] for p in paired]
        fig2 = go.Figure(go.Bar(
            y=sorted_names, x=sorted_ratings, orientation="h",
            marker=dict(color=sorted_ratings,
                        colorscale=[[0, C_CORAL], [0.5, C_GOLD], [1, C_TEAL]],
                        showscale=False, line=dict(width=0)),
            text=[f"{v:.2f}" for v in sorted_ratings],
            textposition="outside", textfont=dict(color=C_MUTED, size=11),
            hovertemplate="<b>%{y}</b><br>Avg Rating: %{x:.2f}<extra></extra>",
        ))
        fig2.update_layout(pl(title="Avg Rating by Genre", height=400,
                              xaxis=dict(range=[5.0, 6.8]),
                              yaxis=dict(autorange="reversed")))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div class='section-hdr'>Genre × Rating Heatmap <span>DEPTH VIEW</span></div>", unsafe_allow_html=True)
    top8_genres   = [g["genre"] for g in genre_stats[:8]]
    bucket_labels = ["0-4", "4-5", "5-6", "6-7", "7-8", "8-10"]
    bucket_ranges = [(0.0, 4.0), (4.0, 5.0), (5.0, 6.0), (6.0, 7.0), (7.0, 8.0), (8.0, 10.0)]

    heat_data = []
    for genre in top8_genres:
        row_vals = []
        for bmin, bmax in bucket_ranges:
            cell, _ = api_get("/analytics/filtered", params={
                "min_rating": bmin,
                "max_rating": bmax,
                "genre":      genre,
                "min_pop":    0.0,
            })
            row_vals.append(cell["total"] if cell else 0)
        heat_data.append(row_vals)

    fig_heat = go.Figure(go.Heatmap(
        z=heat_data, x=bucket_labels, y=top8_genres,
        colorscale=[[0, C_SURFACE], [0.3, C_PURPLE], [0.7, C_GOLD], [1, C_TEAL]],
        hovertemplate="Genre: <b>%{y}</b><br>Rating: <b>%{x}</b><br>Movies: <b>%{z:,}</b><extra></extra>",
        text=[[f"{v:,}" for v in row] for row in heat_data],
        texttemplate="%{text}",
        textfont=dict(size=10, color=C_TEXT),
    ))
    fig_heat.update_layout(pl(title="Number of Movies — Genre vs Rating Range", height=380))
    st.plotly_chart(fig_heat, use_container_width=True)


# ══════════════════════════════════════════
# TAB 3 — RATINGS
# ══════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-hdr'>Ratings Deep Dive <span>ANALYSIS</span></div>", unsafe_allow_html=True)

    mean_r  = f_avg_r
    total_f = f_total

    st.markdown("<div class='section-hdr'>Rating Spread <span>HOW MOVIES ARE SCORED</span></div>", unsafe_allow_html=True)

    rd_ranges = [b["range"] for b in f_rat_dist]
    rd_counts = [b["count"] for b in f_rat_dist]
    rd_pcts   = [round(c / total_f * 100, 1) if total_f > 0 else 0 for c in rd_counts]

    colors_rd = [C_CORAL, C_CORAL, C_PURPLE, C_PURPLE, C_GOLD, C_TEAL, C_TEAL, C_BLUE]
    fig_rd = go.Figure(go.Bar(
        x=rd_ranges, y=rd_counts,
        marker=dict(color=colors_rd[:len(rd_ranges)], opacity=0.88, line=dict(width=0)),
        text=[f"{c:,}\n({p}%)" for c, p in zip(rd_counts, rd_pcts)],
        textposition="outside", textfont=dict(color=C_MUTED, size=11),
        hovertemplate="<b>Rating %{x}</b><br>%{y:,} movies<extra></extra>",
    ))
    mean_bucket_idx = min(range(len(rd_ranges)),
                          key=lambda i: abs(float(rd_ranges[i].split("-")[0]) - mean_r)) if rd_ranges else 0
    fig_rd.add_vline(
        x=mean_bucket_idx, line_dash="dot", line_color=C_GOLD, line_width=1.5,
        annotation_text=f"Mean ≈ {mean_r}", annotation_font_color=C_GOLD,
        annotation_position="top right",
    )
    fig_rd.update_layout(pl(
        title="Rating Distribution",
        xaxis_title="Rating Range", yaxis_title="Number of Movies", bargap=0.18, height=420,
    ))
    st.plotly_chart(fig_rd, use_container_width=True)

    st.markdown("<div class='section-hdr'>Quality Tiers <span>AT A GLANCE</span></div>", unsafe_allow_html=True)

    bucket_map  = {b["range"]: b["count"] for b in f_rat_dist}
    masterpiece = bucket_map.get("9-10", 0)
    excellent   = bucket_map.get("8-9",  0)
    good        = bucket_map.get("7-8",  0)
    average     = bucket_map.get("5-6",  0) + bucket_map.get("6-7", 0)
    below_avg   = bucket_map.get("0-2",  0) + bucket_map.get("2-4", 0) + bucket_map.get("4-5", 0)

    tiers = [
        ("⭐ Masterpiece  (9–10)", masterpiece, C_TEAL),
        ("🥇 Excellent    (8–9)",  excellent,   C_GOLD),
        ("👍 Good         (7–8)",  good,        C_BLUE),
        ("😐 Average      (5–7)",  average,     C_PURPLE),
        ("👎 Below Avg   (0–5)",   below_avg,   C_CORAL),
    ]
    tier_labels = [t[0] for t in tiers]
    tier_counts = [t[1] for t in tiers]
    tier_colors = [t[2] for t in tiers]
    tier_pcts   = [round(c / total_f * 100, 1) if total_f > 0 else 0 for c in tier_counts]

    fig_tier = go.Figure(go.Bar(
        y=tier_labels, x=tier_counts, orientation="h",
        marker=dict(color=tier_colors, opacity=0.88, line=dict(width=0)),
        text=[f"{c:,}  ({p}%)" for c, p in zip(tier_counts, tier_pcts)],
        textposition="outside", textfont=dict(color=C_TEXT, size=12),
        hovertemplate="<b>%{y}</b><br>%{x:,} movies<extra></extra>",
    ))
    fig_tier.update_layout(pl(
        title="Quality Tiers",
        height=320, yaxis=dict(autorange="reversed"),
        xaxis=dict(title="Number of Movies"), showlegend=False,
    ))
    st.plotly_chart(fig_tier, use_container_width=True)


# ══════════════════════════════════════════
# TAB 4 — RECOMMEND ME
# ══════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-hdr'>Recommend Me Movies <span>Personalized</span></div>", unsafe_allow_html=True)

    rc1, rc2 = st.columns(2)
    with rc1:
        genre_options = [g["genre"] for g in overview["genre_stats"]]
        rec_genre     = st.selectbox("Pick a Genre", genre_options, key="rec_genre")
    with rc2:
        rec_rating = st.slider("Minimum Rating", 0.0, 10.0, 6.5, 0.5, key="rec_rating")

    with st.spinner("Loading recommendations..."):
        rec_data, rec_err = api_get("/analytics/recommend", params={
            "genre":      rec_genre,
            "min_rating": rec_rating,
            "top_n":      50,
        })

    if rec_err or not rec_data:
        st.warning("⚠️ Could not load recommendations. Check backend connection.")
    elif rec_data["total_found"] == 0:
        st.warning("No movies found. Try lowering the rating filter.")
    else:
        st.markdown(f"""<div class='info-box' style='margin-bottom:1rem'>
            Found <b style='color:{C_GOLD}'>{rec_data['total_found']:,} movies</b> matching your preferences.
            Showing top picks sorted by rating + popularity.
        </div>""", unsafe_allow_html=True)

        r1, r2, r3 = st.columns(3)
        for col, title_lbl, color, bucket_key in [
            (r1, "🎬 Top Picks",                 C_GOLD,  "top_picks"),
            (r2, "⭐ Highest Rated",             C_TEAL,  "highest_rated"),
            (r3, f"🔥 Trending in {rec_genre}",  C_CORAL, "trending"),
        ]:
            with col:
                st.markdown(
                    f"<div style='color:{color};font-weight:600;font-size:.9rem;margin-bottom:.6rem'>{title_lbl}</div>",
                    unsafe_allow_html=True,
                )
                for item in rec_data[bucket_key]:
                    genres_short = " · ".join(str(item["genres"]).split()[:2])
                    poster_url   = item.get("poster_url")
                    if poster_url:
                        poster_block = (
                            f"<img src='{poster_url}' style='"
                            f"width:52px;height:76px;object-fit:cover;"
                            f"border-radius:6px;flex-shrink:0;"
                            f"border:1px solid {C_BORDER}' />"
                        )
                    else:
                        poster_block = (
                            f"<div style='width:52px;height:76px;flex-shrink:0;"
                            f"border-radius:6px;border:1px dashed {C_BORDER};"
                            f"background:{C_SURFACE};display:flex;align-items:center;"
                            f"justify-content:center;text-align:center;"
                            f"font-size:.6rem;color:{C_MUTED};padding:4px;'>"
                            f"No Poster Available</div>"
                        )
                    st.markdown(
                        f"<div class='rec-movie-card' style='display:flex;gap:.75rem;align-items:center;'>"
                        f"{poster_block}"
                        f"<div style='flex:1;min-width:0;'>"
                        f"<div class='rec-title'>{item['title']}</div>"
                        f"<div class='rec-meta'>{genres_short}</div>"
                        f"<div class='rec-rating'>★ {item['vote_average']} &nbsp;|&nbsp; Pop: {item['popularity']}</div>"
                        f"</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )


# ══════════════════════════════════════════
# TAB 5 — COMPARE MOVIES
# ══════════════════════════════════════════
with tab5:
    st.markdown("<div class='section-hdr'>Compare Movies <span>HEAD TO HEAD</span></div>", unsafe_allow_html=True)

    with st.spinner("Loading movie titles..."):
        titles_data, titles_err = api_get("/analytics/titles")

    if titles_err or not titles_data:
        st.warning("⚠️ Could not load movie titles from backend.")
        st.stop()

    all_titles = titles_data["titles"]

    cc1, cc2 = st.columns(2)
    with cc1:
        movie1 = st.selectbox(
            "🎬 Movie 1", all_titles,
            index=all_titles.index("Inception") if "Inception" in all_titles else 0,
            key="m1",
        )
    with cc2:
        movie2 = st.selectbox(
            "🎬 Movie 2", all_titles,
            index=all_titles.index("The Dark Knight") if "The Dark Knight" in all_titles else 1,
            key="m2",
        )

    with st.spinner("Comparing movies..."):
        compare_data, cmp_err = api_get("/analytics/compare", params={
            "title1": movie1,
            "title2": movie2,
        })

    if cmp_err or not compare_data:
        st.warning(f"⚠️ Could not compare movies: {cmp_err}")
    else:
        m1 = compare_data["movie1"]
        m2 = compare_data["movie2"]

        rating1 = m1["vote_average"]
        rating2 = m2["vote_average"]
        pop1    = m1["popularity"]
        pop2    = m2["popularity"]
        genres1 = m1["genres"]
        genres2 = m2["genres"]
        common  = set(genres1) & set(genres2)
        ov_len1 = m1["overview_len"]
        ov_len2 = m2["overview_len"]
        rating_winner = movie1 if rating1 >= rating2 else movie2
        pop_winner    = movie1 if pop1    >= pop2    else movie2

        def poster_html(url):
            if url:
                return (
                    f"<img src='{url}' style='width:120px;height:178px;object-fit:cover;"
                    f"border-radius:10px;margin-bottom:.8rem;border:2px solid {C_BORDER}' />"
                )
            return "<div style='height:10px'></div>"

        p1_html = poster_html(m1.get("poster_url"))
        p2_html = poster_html(m2.get("poster_url"))

        w1     = "winner" if rating1 >= rating2 and pop1 >= pop2 else ""
        w2     = "winner" if rating2 > rating1  and pop2 > pop1  else ""
        badge1 = '<div class="win-badge">WINNER</div>' if w1 else '<div style="height:24px"></div>'
        badge2 = '<div class="win-badge">WINNER</div>' if w2 else '<div style="height:24px"></div>'
        g1_str = " · ".join(genres1[:4])
        g2_str = " · ".join(genres2[:4])

        col1, mid, col2 = st.columns([5, 1, 5])
        with col1:
            st.markdown(
                f"<div class='compare-card {w1}'>"
                f"{badge1}{p1_html}"
                f"<div class='compare-title'>{movie1}</div>"
                f"<div class='compare-big'>{rating1}</div>"
                f"<div class='compare-label'>Rating</div><br>"
                f"<div class='compare-big' style='font-size:1.5rem;color:{C_TEAL}'>{round(pop1,1)}</div>"
                f"<div class='compare-label'>Popularity</div><br>"
                f"<div style='font-size:.85rem;color:{C_MUTED}'>{g1_str}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with mid:
            st.markdown(
                f"<div style='display:flex;align-items:center;justify-content:center;"
                f"height:100%;font-size:1.5rem;color:{C_MUTED};padding-top:3rem'>VS</div>",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"<div class='compare-card {w2}'>"
                f"{badge2}{p2_html}"
                f"<div class='compare-title'>{movie2}</div>"
                f"<div class='compare-big'>{rating2}</div>"
                f"<div class='compare-label'>Rating</div><br>"
                f"<div class='compare-big' style='font-size:1.5rem;color:{C_TEAL}'>{round(pop2,1)}</div>"
                f"<div class='compare-label'>Popularity</div><br>"
                f"<div style='font-size:.85rem;color:{C_MUTED}'>{g2_str}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("<div class='section-hdr'>Detailed Comparison <span>METRICS</span></div>", unsafe_allow_html=True)

        def diff_color(a, b):
            return C_GREEN if a >= b else C_CORAL

        st.markdown(f"""
        <div class='chart-card'>
        <table class='movie-table'>
            <thead><tr><th>Metric</th><th>{movie1}</th><th>{movie2}</th><th>Difference</th><th>Winner</th></tr></thead>
            <tbody>
            <tr>
                <td>⭐ Rating</td>
                <td style='color:{diff_color(rating1,rating2)};font-weight:600'>{rating1}</td>
                <td style='color:{diff_color(rating2,rating1)};font-weight:600'>{rating2}</td>
                <td>{abs(round(rating1-rating2,1))}</td>
                <td><span class='rating-pill'>{rating_winner}</span></td>
            </tr>
            <tr>
                <td>🔥 Popularity</td>
                <td style='color:{diff_color(pop1,pop2)};font-weight:600'>{round(pop1,1)}</td>
                <td style='color:{diff_color(pop2,pop1)};font-weight:600'>{round(pop2,1)}</td>
                <td>{abs(round(pop1-pop2,1))}</td>
                <td><span class='rating-pill'>{pop_winner}</span></td>
            </tr>
            <tr>
                <td>🎭 Genres</td>
                <td>{" · ".join(genres1[:3])}</td>
                <td>{" · ".join(genres2[:3])}</td>
                <td>—</td><td>—</td>
            </tr>
            <tr>
                <td>🔗 Common Genres</td>
                <td colspan='3'>{", ".join(common) if common else "None"}</td>
                <td>{"✅ Match" if common else "❌ None"}</td>
            </tr>
            <tr>
                <td>📖 Overview Length</td>
                <td>{ov_len1} words</td>
                <td>{ov_len2} words</td>
                <td>{abs(ov_len1-ov_len2)} words</td>
                <td>—</td>
            </tr>
            </tbody>
        </table>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)