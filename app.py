import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime
from recommended_engine import RecommendationEngine
from models import User, RegisteredUser, Movie

# ─── Page Config ───
st.set_page_config(
    page_title="Cineverse – Movie Recommendation System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap');

    :root {
        --bg: #0A0E14;
        --surface: #121820;
        --surface2: #1A2230;
        --accent: #0088FF;
        --accent2: #0066CC;
        --text: #FFFFFF;
        --muted: #B3B3B3;
        --border: #2A3A4A;
    }

    .stApp { background-color: var(--bg); }

    .main .block-container { padding: 2rem 2.5rem; max-width: 1200px; }

    h1, h2, h3 { font-family: 'Playfair Display', serif; color: var(--text); }
    p, label, .stMarkdown { color: var(--text); font-family: 'Inter', sans-serif; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--surface);
        border-right: 1px solid var(--border);
    }
    
    /* ChatGPT-style Sidebar Navigation */
    [data-testid="stSidebar"] .stButton {
        margin-bottom: 0.25rem;
    }
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        border: none !important;
        color: #E8E8ED !important;
        text-align: left !important;
        padding: 0.65rem 0.75rem !important;
        font-size: 0.95rem !important;
        font-weight: 400 !important;
        border-radius: 6px !important;
        transition: background-color 0.15s ease !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: rgba(0, 136, 255, 0.15) !important;
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background-color: rgba(0, 136, 255, 0.25) !important;
    }
    [data-testid="stSidebar"] .stButton > button:active,
    [data-testid="stSidebar"] .stButton > button:focus {
        box-shadow: none !important;
        border: none !important;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background-color: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: 8px !important;
    }

    /* Multiselect styling - purple color */
    .stMultiSelect [data-testid="stMultiSelect"] > div > div {
        background-color: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: 8px !important;
    }
    .stMultiSelect [data-testid="stMultiSelect"] [role="listbox"] {
        background-color: var(--surface2) !important;
        border: 1px solid var(--border) !important;
    }
    .stMultiSelect [data-testid="stMultiSelect"] [role="option"][aria-selected="true"] {
        background-color: #7851A9 !important;
        color: white !important;
    }
    .stMultiSelect [data-testid="stMultiSelect"] [role="option"]:hover {
        background-color: rgba(120, 81, 169, 0.3) !important;
    }
    /* Selected item tags/chips - purple */
    .stMultiSelect [data-testid="stMultiSelect"] div[data-baseweb="tag"],
    .stMultiSelect [data-testid="stMultiSelect"] span[data-baseweb="tag"],
    .stMultiSelect [data-testid="stMultiSelect"] .stTag {
        background-color: #7851A9 !important;
        color: white !important;
        border: 1px solid #7851A9 !important;
    }
    .stMultiSelect [data-testid="stMultiSelect"] div[data-baseweb="tag"] button,
    .stMultiSelect [data-testid="stMultiSelect"] span[data-baseweb="tag"] button,
    .stMultiSelect [data-testid="stMultiSelect"] .stTag button {
        color: white !important;
    }
    /* Additional tag styling */
    .stMultiSelect [data-testid="stMultiSelect"] .tag {
        background-color: #7851A9 !important;
        color: white !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: var(--accent) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
        transition: background-color 0.2s !important;
    }
    .stButton > button:hover { background-color: #0066CC !important; }

    /* Cards */
    .movie-card {
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
    }
    .movie-card h4 { margin: 0 0 0.25rem 0; color: var(--text); font-family: 'Inter', sans-serif; font-weight: 600; }
    .movie-card p { margin: 0; color: var(--muted); font-size: 0.85rem; }
    .badge {
        display: inline-block;
        background: var(--accent);
        color: white;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 4px;
        box-shadow: 0 0 8px rgba(0, 136, 255, 0.4);
    }
    .badge-gold { background: #0066CC; color: #FFFFFF; box-shadow: 0 0 8px rgba(0, 102, 204, 0.4); }

    /* Hero */
    .hero {
        background: linear-gradient(135deg, #121820 0%, #0A0E14 60%);
        border: 1px solid #0088FF40;
        border-radius: 16px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 0 20px rgba(0, 136, 255, 0.15);
    }
    .hero h1 { font-size: 2.8rem; margin-bottom: 0.5rem; }
    .hero h1 span { color: #0088FF; }
    .hero p { color: var(--muted); font-size: 1.1rem; }

    /* Stat cards */
    .stat-card {
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .stat-card .number { font-size: 2rem; font-weight: 700; color: #0088FF; font-family: 'Playfair Display', serif; }
    .stat-card .label { color: var(--muted); font-size: 0.85rem; font-family: 'Inter', sans-serif; }

    /* Divider */
    hr { border-color: var(--border) !important; }

    /* Success/info */
    .stSuccess, .stInfo, .stWarning { border-radius: 8px !important; }

    /* Slider */
    .stSlider { color: var(--text) !important; }

    /* Tables */
    .stDataFrame { background: var(--surface2) !important; border-radius: 12px !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background: var(--surface); border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: var(--muted) !important; font-family: 'Inter', sans-serif; }
    .stTabs [aria-selected="true"] { color: var(--text) !important; }

    /* Section headers */
    .section-header {
        font-family: 'Playfair Display', serif;
        font-size: 1.4rem;
        color: var(--text);
        border-left: 3px solid #0088FF;
        padding-left: 0.75rem;
        margin: 1.5rem 0 1rem 0;
    }

    /* Navigation tiles */
    .nav-tile {
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        transition: all 0.2s;
    }
    .nav-tile:hover {
        background: var(--accent);
        border-color: var(--accent);
    }
</style>
""", unsafe_allow_html=True)

# ─── Database Setup ────
DB_PATH = "mrs_database.db"


def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            userID INTEGER PRIMARY KEY AUTOINCREMENT,
            userName TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            passwordHash TEXT NOT NULL,
            preferences TEXT DEFAULT '',
            subscriptionStatus TEXT DEFAULT 'active',
            recommendationList TEXT DEFAULT '',
            createdAt TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            movieID INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT NOT NULL,
            releaseYear INTEGER,
            director TEXT,
            description TEXT,
            avgRating REAL DEFAULT 0.0,
            ratingCount INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            ratingID INTEGER PRIMARY KEY AUTOINCREMENT,
            userID INTEGER,
            movieID INTEGER,
            rating INTEGER,
            ratedAt TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (userID) REFERENCES users(userID),
            FOREIGN KEY (movieID) REFERENCES movies(movieID),
            UNIQUE (userID, movieID)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS watchHistory (
            historyID INTEGER PRIMARY KEY AUTOINCREMENT,
            userID INTEGER,
            movieID INTEGER,
            watchedAt TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (userID) REFERENCES users(userID),
            FOREIGN KEY (movieID) REFERENCES movies(movieID)
        )
    """)

    # Seed movies if empty
    c.execute("SELECT COUNT(*) FROM movies")
    if c.fetchone()[0] == 0:
        seed_movies = [
            ("The Dark Knight", "Action/Thriller", 2008, "Christopher Nolan",
             "Batman faces the Joker, a criminal mastermind."),
            ("Inception", "Sci-Fi/Thriller", 2010, "Christopher Nolan",
             "A thief enters people's dreams to steal secrets."),
            ("Parasite", "Drama/Thriller", 2019, "Bong Joon-ho", "Class tensions explode between two Korean families."),
            ("Interstellar", "Sci-Fi/Drama", 2014, "Christopher Nolan", "Astronauts seek a new home for humanity."),
            ("The Shawshank Redemption", "Drama", 1994, "Frank Darabont", "Two imprisoned men bond over years."),
            ("Pulp Fiction", "Crime/Drama", 1994, "Quentin Tarantino", "Interlocking tales of crime in LA."),
            ("The Matrix", "Sci-Fi/Action", 1999, "Wachowski Sisters", "A hacker discovers reality is a simulation."),
            ("Spirited Away", "Animation/Fantasy", 2001, "Hayao Miyazaki", "A girl enters a magical spirit world."),
            ("Get Out", "Horror/Thriller", 2017, "Jordan Peele", "A Black man uncovers a disturbing secret."),
            ("Whiplash", "Drama/Music", 2014, "Damien Chazelle", "A drummer chases greatness under a brutal teacher."),
            ("Mad Max: Fury Road", "Action/Sci-Fi", 2015, "George Miller",
             "A high-octane chase through a post-apocalyptic desert."),
            ("Her", "Sci-Fi/Romance", 2013, "Spike Jonze", "A man falls in love with an AI operating system."),
            ("La La Land", "Romance/Musical", 2016, "Damien Chazelle",
             "A jazz musician and an actress chase their dreams."),
            ("Avengers: Endgame", "Action/Sci-Fi", 2019, "Russo Brothers",
             "The Avengers reassemble to reverse Thanos's snap."),
            ("Knives Out", "Mystery/Comedy", 2019, "Rian Johnson",
             "A detective investigates a wealthy family after their patriarch dies."),
            ("Everything Everywhere All at Once", "Sci-Fi/Comedy", 2022, "Daniels",
             "A woman must save the multiverse while doing her taxes."),
            ("Dune", "Sci-Fi/Adventure", 2021, "Denis Villeneuve",
             "A noble family is entrusted with a dangerous desert planet."),
            ("The Godfather", "Crime/Drama", 1972, "Francis Ford Coppola", "The aging patriarch of a crime dynasty."),
            ("Arrival", "Sci-Fi/Drama", 2016, "Denis Villeneuve",
             "A linguist works to communicate with alien visitors."),
            ("Joker", "Crime/Drama", 2019, "Todd Phillips", "A failed comedian descends into madness."),
            ("Titanic", "Romance/Drama", 1997, "James Cameron", "A romance unfolds aboard the ill-fated luxury liner."),
            ("Forrest Gump", "Drama/Romance", 1994, "Robert Zemeckis", "A simple man leads an extraordinary life through American history."),
            ("The Silence of the Lambs", "Thriller/Crime", 1991, "Jonathan Demme", "An FBI trainee enlists a cannibalistic serial killer to catch another."),
            ("Gladiator", "Action/Drama", 2000, "Ridley Scott", "A betrayed Roman general seeks revenge in the arena."),
            ("The Lion King", "Animation/Drama", 1994, "Roger Allers", "A young lion prince flees his pride believing he killed his father."),
            ("Back to the Future", "Sci-Fi/Comedy", 1985, "Robert Zemeckis", "A teenager travels back in time and must save his existence."),
            ("Goodfellas", "Crime/Drama", 1990, "Martin Scorsese", "A mob associate rises and falls within the Mafia."),
            ("Schindler's List", "Drama/History", 1993, "Steven Spielberg", "A businessman saves Jews during the Holocaust."),
            ("The Grand Budapest Hotel", "Comedy/Drama", 2014, "Wes Anderson", "A legendary concierge and his lobby boy become entangled in murder."),
            ("Coco", "Animation/Fantasy", 2017, "Lee Unkrich", "A boy journeys to the Land of the Dead to find his great-great-grandfather."),
            ("Black Panther", "Action/Sci-Fi", 2018, "Ryan Coogler", "A king must defend his technologically advanced African nation."),
            ("The Social Network", "Drama", 2010, "David Fincher", "The founding of Facebook and the lawsuits that followed."),
            ("Blade Runner 2049", "Sci-Fi/Thriller", 2017, "Denis Villeneuve", "A young blade runner discovers a secret that could plunge society into chaos."),
            ("The Departed", "Crime/Thriller", 2006, "Martin Scorsese", "An undercover cop and a mole hunt each other in Boston's underworld."),
            ("WALL-E", "Animation/Sci-Fi", 2008, "Andrew Stanton", "A lonely waste-collecting robot falls in love and embarks on a space journey."),
            ("Inglourious Basterds", "War/Drama", 2009, "Quentin Tarantino", "A group of Jewish soldiers plot to assassinate Nazi leaders."),
            ("The Truman Show", "Drama/Comedy", 1998, "Peter Weir", "A man discovers his entire life is a television show."),
            ("Eternal Sunshine of the Spotless Mind", "Romance/Sci-Fi", 2004, "Michel Gondry", "A couple undergoes a procedure to erase memories of their failed relationship."),
            ("1917", "War/Drama", 2019, "Sam Mendes", "Two soldiers must cross enemy territory to deliver a vital message."),
            ("Spider-Man: Into the Spider-Verse", "Animation/Action", 2018, "Bob Persichetti", "Teenager Miles Morales becomes Spider-Man and meets alternate versions of the hero."),
        ]
        c.executemany(
            "INSERT INTO movies (title, genre, releaseYear, director, description) VALUES (?,?,?,?,?)",
            seed_movies
        )

    conn.commit()
    conn.close()

# ─── Data Helpers ───
def get_all_movies():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM movies ORDER BY avgRating DESC", conn)
    conn.close()
    return df


def search_movies(query):
    """Search movies and return a DataFrame."""
    movies = Movie.search(query=query, db_path=DB_PATH)
    if not movies:
        return pd.DataFrame()
    movie_dicts = [m.getMovieDetails() for m in movies]
    return pd.DataFrame(movie_dicts)


def submit_rating(user_obj, movieID, rating):
    """Submit a rating and update the movie's average."""
    success = user_obj.rateMovie(movieID, rating, db_path=DB_PATH)
    if success:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM movies WHERE movieID=?", (movieID,))
        row = c.fetchone()
        conn.close()

        if row:
            movie = Movie(
                movieID=row[0],
                title=row[1],
                genre=row[2],
                releaseYear=row[3] or 0,
                avgRating=row[6] or 0.0,
                director=row[4] or "",
                description=row[5] or ""
            )
            movie.updateMovieRating(db_path=DB_PATH)
    return success


def get_user_ratings(userID):
    conn = get_db()
    df = pd.read_sql("""
                     SELECT m.title, m.genre, r.rating, r.ratedAt
                     FROM ratings r
                     JOIN movies m ON r.movieID = m.movieID
                     WHERE r.userID = ?
                     ORDER BY r.ratedAt DESC
                     """, conn, params=(userID,))
    conn.close()
    return df


def get_watchHistory(userID):
    conn = get_db()
    df = pd.read_sql("""
                     SELECT m.title, m.genre, m.releaseYear, h.watchedAt
                     FROM watchHistory h
                     JOIN movies m ON h.movieID = m.movieID
                     WHERE h.userID = ?
                     ORDER BY h.watchedAt DESC LIMIT 20
                     """, conn, params=(userID,))
    conn.close()
    return df


def get_recommendations(user_obj):
    """Return personalised recommendations for a user."""
    conn = get_db()
    all_movies = pd.read_sql("SELECT * FROM movies", conn)
    all_ratings = pd.read_sql("SELECT * FROM ratings", conn)
    conn.close()

    engine = RecommendationEngine(all_movies, all_ratings)

    if isinstance(user_obj, RegisteredUser):
        recs_list = user_obj.getMovieRecommendation(engine, db_path=DB_PATH)
        if recs_list:
            return pd.DataFrame(recs_list)

    user_ratings = pd.read_sql(
        "SELECT movieID, rating FROM ratings WHERE userID=?",
        get_db(),
        params=(user_obj.userID,)
    )
    recs = engine.generate_recommendations(user_obj.userID, user_ratings)

    if not recs.empty:
        cached = ",".join(recs.head(8)["title"].tolist())
        cache_recommendationList(user_obj.userID, cached)

    return recs


def cache_recommendationList(userID, titles_csv):
    """Cache the latest recommendation list for a user."""
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET recommendationList=? WHERE userID=?", (titles_csv, userID))
    conn.commit()
    conn.close()


def update_preferences(user_obj, new_preferences):
    """Update a user's genre preferences."""
    if isinstance(user_obj, RegisteredUser):
        return user_obj.updatePreferences(new_preferences, db_path=DB_PATH)
    else:
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE users SET preferences=? WHERE userID=?", (new_preferences, user_obj.userID))
        conn.commit()
        conn.close()
        return True


def update_subscriptionStatus(userID, status):
    """Update a user's subscription status."""
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET subscriptionStatus=? WHERE userID=?", (status, userID))
    conn.commit()
    conn.close()


def get_user_profile(userID):
    """Return a user's profile record."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE userID=?", (userID,))
    row = c.fetchone()
    cols = [desc[0] for desc in c.description]
    conn.close()
    return dict(zip(cols, row)) if row else {}


def get_trending():
    conn = get_db()
    df = pd.read_sql("""
                     SELECT m.title, m.genre, COUNT(r.ratingID) as watchCount, AVG(r.rating) as avgRating
                     FROM movies m
                     LEFT JOIN ratings r ON m.movieID = r.movieID
                     GROUP BY m.movieID
                     ORDER BY watchCount DESC, avgRating DESC LIMIT 10
                     """, conn)
    conn.close()
    return df


def get_genre_stats():
    conn = get_db()
    df = pd.read_sql("""
                     SELECT m.genre, COUNT(r.ratingID) as totalRatings, AVG(r.rating) as avgRating
                     FROM movies m
                     LEFT JOIN ratings r ON m.movieID = r.movieID
                     GROUP BY m.genre
                     ORDER BY totalRatings DESC
                     """, conn)
    conn.close()
    return df


# ─── Admin Helpers ───
ADMIN_KEY = "CINEMATIC2026"


def add_movie(title, genre, year, director, description):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO movies (title, genre, releaseYear, director, description) VALUES (?,?,?,?,?)",
        (title, genre, year, director, description)
    )
    conn.commit()
    conn.close()


def update_movie(movieID, title, genre, year, director, description):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "UPDATE movies SET title=?, genre=?, releaseYear=?, director=?, description=? WHERE movieID=?",
        (title, genre, year, director, description, movieID)
    )
    conn.commit()
    conn.close()


def delete_movie(movieID):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM movies WHERE movieID=?", (movieID,))
    c.execute("DELETE FROM ratings WHERE movieID=?", (movieID,))
    c.execute("DELETE FROM watchHistory WHERE movieID=?", (movieID,))
    conn.commit()
    conn.close()


def get_engagement_stats():
    conn = get_db()
    most_watched = pd.read_sql("""
                               SELECT m.title, m.genre, COUNT(h.historyID) as watchCount
                               FROM movies m
                               LEFT JOIN watchHistory h ON m.movieID = h.movieID
                               GROUP BY m.movieID
                               ORDER BY watchCount DESC LIMIT 10
                               """, conn)
    user_activity = pd.read_sql("""
                                SELECT u.userName, COUNT(r.ratingID) as ratingsGiven
                                FROM users u
                                LEFT JOIN ratings r ON u.userID = r.userID
                                GROUP BY u.userID
                                ORDER BY ratingsGiven DESC
                                """, conn)
    conn.close()
    return most_watched, user_activity


# ─── Session State Init ────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "user_obj" not in st.session_state:
    st.session_state.user_obj = None
if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False
if "page" not in st.session_state:
    st.session_state.page = "Home"

init_db()

# ─── Sidebar ───
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1.5rem 0 1rem 0;'>
        <span style='font-size:2.2rem;'>🎬</span>
        <h2 style='margin:0; font-family: Playfair Display, serif; color:#0088FF; font-weight: 900; font-size: 1.8rem; letter-spacing: 0.5px;'>Cineverse</h2>
        <p style='color:#B3B3B3; font-size:0.8rem; margin:0;'>AI Movie Recommendations</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.logged_in:
        st.markdown(f"""
        <div style='padding: 1rem 0.5rem; border-top: 1px solid #2A3A4A; border-bottom: 1px solid #2A3A4A; margin-bottom: 1rem;'>
            <p style='color:#B3B3B3; font-size:0.85rem; margin:0;'>👤 {st.session_state.user[1]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        current_nav = st.session_state.get("nav", "🏠 Home")
        
        menu_items = [
            ("🏠", "Home", "🏠 Home"),
            ("📊", "My Dashboard", "📊 My Dashboard"),
            ("🔍", "Browse & Rate", "🔍 Browse & Rate"),
            ("⚙️", "Admin Console", "⚙️ Admin Console")
        ]
        
        for icon, label, nav_key in menu_items:
            is_active = current_nav == nav_key
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{nav_key}",
                width='stretch',
                type="primary" if is_active else "secondary"
            ):
                st.session_state.nav = nav_key
                st.rerun()
        
        nav = st.session_state.get("nav", "🏠 Home")
        
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        if st.button("🚪  Log Out", width='stretch'):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.user_obj = None
            st.session_state.admin_mode = False
            st.rerun()
    else:
        st.markdown("<div style='border-top: 1px solid #2A3A4A; margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
        
        # navigation for guests
        current_nav = st.session_state.get("nav", "🏠 Home")
        
        menu_items = [
            ("🏠", "Home", "🏠 Home"),
            ("🔍", "Browse & Rate", "🔍 Browse & Rate")
        ]
        
        for icon, label, nav_key in menu_items:
            is_active = current_nav == nav_key
            if st.button(
                f"{icon}  {label}",
                key=f"nav_guest_{nav_key}",
                width='stretch',
                type="primary" if is_active else "secondary"
            ):
                st.session_state.nav = nav_key
                st.rerun()
        
        nav = st.session_state.get("nav", "🏠 Home")

# ─── Pages ───

# ══ HOME ═══
if nav == "🏠 Home":
    st.markdown("""
    <div class='hero'>
        <h1>Cineverse</h1>
        <p>AI-powered recommendations tailored to your taste. Rate movies, discover new favourites.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.logged_in:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
            
            with tab1:
                st.markdown("<br>", unsafe_allow_html=True)
                login_user_input = st.text_input("Username", key="login_user")
                login_pass_input = st.text_input("Password", type="password", key="login_pass")
                if st.button("Sign In", width='stretch'):
                    user_obj = User.login(login_user_input, login_pass_input, db_path=DB_PATH)
                    if user_obj:
                        st.session_state.logged_in = True
                        st.session_state.user_obj = user_obj
                        st.session_state.user = (user_obj.userID, user_obj.userName, user_obj.email)
                        st.success(f"Welcome back, {user_obj.userName}!")
                        st.rerun()
                    else:
                        st.error("Invalid userName or password.")

            with tab2:
                st.markdown("<br>", unsafe_allow_html=True)
                reg_user = st.text_input("Username", key="reg_user")
                reg_email = st.text_input("Email", key="reg_email")
                reg_pass = st.text_input("Password", type="password", key="reg_pass")
                
                if reg_email:
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, reg_email):
                        st.error("Please enter a valid email address.")
                
                if reg_pass:
                    if len(reg_pass) < 8:
                        st.error("Password must be at least 8 characters long.")
                    elif not any(c.isupper() for c in reg_pass):
                        st.error("Password must contain at least one uppercase letter.")
                    elif not any(c.islower() for c in reg_pass):
                        st.error("Password must contain at least one lowercase letter.")
                    elif not any(c.isdigit() for c in reg_pass):
                        st.error("Password must contain at least one digit.")
                
                genres = ["Action", "Drama", "Sci-Fi", "Comedy", "Horror", "Romance", "Animation", "Crime", "Thriller"]
                reg_prefs = st.multiselect("Favourite genres (optional)", genres)
                
                if st.button("Create Account", width='stretch'):
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    
                    if not reg_user or not reg_email or not reg_pass:
                        st.warning("Please fill in all required fields.")
                    elif not re.match(email_pattern, reg_email):
                        st.error("Please enter a valid email address.")
                    elif len(reg_pass) < 8:
                        st.error("Password must be at least 8 characters long.")
                    elif not any(c.isupper() for c in reg_pass):
                        st.error("Password must contain at least one uppercase letter.")
                    elif not any(c.islower() for c in reg_pass):
                        st.error("Password must contain at least one lowercase letter.")
                    elif not any(c.isdigit() for c in reg_pass):
                        st.error("Password must contain at least one digit.")
                    else:
                        ok, msg = User.register(reg_user, reg_email, reg_pass, ",".join(reg_prefs), db_path=DB_PATH)
                        if ok:
                            st.success(msg + " Please sign in.")
                        else:
                            st.error(msg)
    else:
        movies_df = get_all_movies()
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"<div class='stat-card'><div class='number'>{len(movies_df)}</div><div class='label'>Movies in Library</div></div>",
                unsafe_allow_html=True)
        conn = get_db()
        n_users = pd.read_sql("SELECT COUNT(*) as n FROM users", conn).iloc[0]['n']
        n_ratings = pd.read_sql("SELECT COUNT(*) as n FROM ratings", conn).iloc[0]['n']
        n_genres = movies_df['genre'].nunique()
        conn.close()
        with c2:
            st.markdown(
                f"<div class='stat-card'><div class='number'>{n_users}</div><div class='label'>Registered Users</div></div>",
                unsafe_allow_html=True)
        with c3:
            st.markdown(
                f"<div class='stat-card'><div class='number'>{n_ratings}</div><div class='label'>Ratings Submitted</div></div>",
                unsafe_allow_html=True)
        with c4:
            st.markdown(
                f"<div class='stat-card'><div class='number'>{n_genres}</div><div class='label'>Genres Available</div></div>",
                unsafe_allow_html=True)

        st.markdown("<div class='section-header'>🎯 Top Rated Movies</div>", unsafe_allow_html=True)
        top = movies_df[movies_df['avgRating'] > 0].head(5)
        if top.empty:
            st.info("No ratings yet. Be the first to rate movies!")
        else:
            for _, row in top.iterrows():
                stars = "⭐" * int(round(row['avgRating']))
                st.markdown(f"""
                <div class='movie-card'>
                    <h4>{row['title']} ({row['releaseYear']})</h4>
                    <p>{stars} {row['avgRating']:.1f}/5 &nbsp;·&nbsp; <span class='badge'>{row['genre']}</span> &nbsp;·&nbsp; {row['director']}</p>
                    <p style='margin-top:0.4rem;'>{row['description']}</p>
                </div>
                """, unsafe_allow_html=True)

# ══ BROWSE & RATE ═══
elif nav == "🔍 Browse & Rate":
    st.markdown("<h2 style='margin-bottom:0.25rem;'>Browse & Rate Movies</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8e8e9a;'>Search our library and rate movies to personalise your recommendations.</p>",
                unsafe_allow_html=True)

    search_query = st.text_input("🔍 Search by title, genre, or director",
                                 placeholder="e.g. Nolan, Sci-Fi, Inception...")

    if search_query:
        results = search_movies(search_query)
        st.markdown(f"<p style='color:#8e8e9a;'>{len(results)} result(s) for <b>'{search_query}'</b></p>",
                    unsafe_allow_html=True)
    else:
        results = get_all_movies()
        st.markdown(f"<p style='color:#8e8e9a;'>Showing all {len(results)} movies</p>", unsafe_allow_html=True)

    genre_options = ["All"] + sorted(results['genre'].unique().tolist()) if not results.empty else ["All"]
    genre_filter = st.selectbox("Filter by genre", genre_options)
    if genre_filter != "All":
        results = results[results['genre'] == genre_filter]

    if results.empty:
        st.info("No movies found. Try a different search.")
    else:
        for _, row in results.iterrows():
            with st.container():
                if st.session_state.logged_in:
                    col_info, col_rate = st.columns([3, 1])
                    with col_info:
                        rating_display = f"⭐ {row['avgRating']:.1f}" if row['avgRating'] > 0 else "Not yet rated"
                        st.markdown(f"""
                        <div class='movie-card'>
                            <h4>{row['title']} ({row['releaseYear']})</h4>
                            <p><span class='badge'>{row['genre']}</span> · {row['director']} · {rating_display} ({int(row['ratingCount'])} ratings)</p>
                            <p style='margin-top:0.4rem; color:#b0b0bc;'>{row['description']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_rate:
                        rating_val = st.select_slider(
                            f"Rate",
                            options=[1, 2, 3, 4, 5],
                            value=3,
                            key=f"slider_{row['movieID']}"
                        )
                        if st.button("Submit", key=f"rate_{row['movieID']}"):
                            # Submit the rating
                            if submit_rating(st.session_state.user_obj, row['movieID'], rating_val):
                                st.success("Rated!")
                                st.rerun()
                            else:
                                st.error("Failed to submit rating.")
                else:
                    rating_display = f"⭐ {row['avgRating']:.1f}" if row['avgRating'] > 0 else "Not yet rated"
                    st.markdown(f"""
                    <div class='movie-card'>
                        <h4>{row['title']} ({row['releaseYear']})</h4>
                        <p><span class='badge'>{row['genre']}</span> · {row['director']} · {rating_display} ({int(row['ratingCount'])} ratings)</p>
                        <p style='margin-top:0.4rem; color:#b0b0bc;'>{row['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)

# ══ MY DASHBOARD ═══
elif nav == "📊 My Dashboard":
    if not st.session_state.logged_in:
        st.warning("Please sign in to access your dashboard.")
        st.stop()

    user = st.session_state.user
    st.markdown(f"<h2>Welcome back, {user[1]} 👋</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8e8e9a;'>Your personalised movie dashboard.</p>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Recommendations", "🔥 Trending", "📋 Watch History", "📈 Visualisations", "👤 My Profile"])

    # ── Tab 1: Recommendations
    with tab1:
        st.markdown("<div class='section-header'>AI-Powered Picks For You</div>", unsafe_allow_html=True)
        user_ratings = get_user_ratings(user[0])
        if len(user_ratings) < 1:
            st.info("Rate at least 1 movie in Browse & Rate to get personalised recommendations!")
        else:
            recs = get_recommendations(st.session_state.user_obj)
            if recs.empty:
                st.info("You've rated everything! More movies coming soon.")
            else:
                for _, row in recs.head(8).iterrows():
                    match_pct = int(row.get('match_pct', 0))
                    st.markdown(f"""
                    <div class='movie-card'>
                        <h4>{row['title']} <span class='badge badge-gold'>Match {match_pct}%</span></h4>
                        <p><span class='badge'>{row['genre']}</span> · {row['releaseYear']} · {row['director']}</p>
                        <p style='margin-top:0.4rem; color:#b0b0bc;'>{row['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)

    # ── Tab 2: Trending
    with tab2:
        st.markdown("<div class='section-header'>Trending Now</div>", unsafe_allow_html=True)
        trending = get_trending()
        if trending['watchCount'].sum() == 0:
            st.info("No trending data yet — start rating movies!")
        else:
            for i, row in trending.head(10).iterrows():
                rank_badge = ["🥇", "🥈", "🥉"] + ["🎬"] * 7
                avg = f"⭐ {row['avgRating']:.1f}" if row['avgRating'] else "—"
                st.markdown(f"""
                <div class='movie-card'>
                    <h4>{rank_badge[i]} {row['title']}</h4>
                    <p><span class='badge'>{row['genre']}</span> · {int(row['watchCount'])} watches · {avg}</p>
                </div>
                """, unsafe_allow_html=True)

    # ── Tab 3: Watch History
    with tab3:
        st.markdown("<div class='section-header'>Watch History & Rating Logs</div>", unsafe_allow_html=True)
        col_h, col_r = st.columns(2)

        with col_h:
            st.markdown("**Watch History**")
            history = get_watchHistory(user[0])
            if history.empty:
                st.info("No watch history yet.")
            else:
                st.dataframe(
                    history.rename(columns={"title": "Title", "genre": "Genre",
                                            "releaseYear": "Year", "watchedAt": "Watched At"}),
                    width='stretch', hide_index=True
                )

        with col_r:
            st.markdown("**Rating Logs**")
            ratings = get_user_ratings(user[0])
            if ratings.empty:
                st.info("No ratings submitted yet.")
            else:
                st.dataframe(
                    ratings.rename(columns={"title": "Title", "genre": "Genre",
                                            "rating": "Rating", "ratedAt": "Rated At"}),
                    width='stretch', hide_index=True
                )

    # ── Tab 4: Visualisations
    with tab4:
        st.markdown("<div class='section-header'>Data Insights</div>", unsafe_allow_html=True)

        col_v1, col_v2 = st.columns(2)

        with col_v1:
            user_ratings_df = get_user_ratings(user[0])
            if not user_ratings_df.empty:
                genre_counts = user_ratings_df['genre'].value_counts().reset_index()
                genre_counts.columns = ['Genre', 'Count']
                cool_palette = ['#60A5FA', '#22D3EE', '#818CF8', '#38BDF8', '#A78BFA', '#67E8F9', '#93C5FD']
                fig1 = px.bar(genre_counts, x='Genre', y='Count',
                              title="<b>Your Ratings by Genre</b>",
                              color='Genre',
                              color_discrete_sequence=cool_palette,
                              template="plotly_dark",
                              text='Count')
                fig1.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#e8e8ed', showlegend=False,
                    title_x=0.5, margin=dict(t=60, b=40)
                )
                fig1.update_traces(textposition='outside', textfont_size=13,
                                   marker_line_color='#ffffff', marker_line_width=1.2,
                                   opacity=0.92)
                st.plotly_chart(fig1, width='stretch')
            else:
                st.info("Rate some movies to see your genre breakdown.")

        with col_v2:
            if not user_ratings_df.empty:
                rating_dist = user_ratings_df['rating'].value_counts().sort_index().reset_index()
                rating_dist.columns = ['Stars', 'Count']
                fig2 = px.bar(rating_dist, x='Stars', y='Count',
                              title="<b>Your Rating Distribution</b>",
                              color='Stars',
                              color_continuous_scale=['#1E3A8A', '#2563EB', '#3B82F6', '#60A5FA', '#93C5FD'],
                              template="plotly_dark",
                              text='Count')
                fig2.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#e8e8ed', showlegend=False,
                    coloraxis_showscale=False,
                    title_x=0.5, margin=dict(t=60, b=40)
                )
                fig2.update_traces(textposition='outside', textfont_size=13,
                                   marker_line_color='#ffffff', marker_line_width=1.2,
                                   opacity=0.92)
                st.plotly_chart(fig2, width='stretch')
            else:
                st.info("Rate some movies to see your rating distribution.")

        st.markdown("---")
        genre_stats = get_genre_stats()
        if genre_stats['totalRatings'].sum() > 0:
            genre_stats = genre_stats.sort_values('totalRatings', ascending=True)
            fig3 = px.bar(genre_stats, x='totalRatings', y='genre',
                          title="<b>Most Popular Genres (All Users)</b>",
                          color='avgRating',
                          color_continuous_scale=['#1E3A8A', '#2563EB', '#3B82F6', '#60A5FA', '#A5F3FC'],
                          template="plotly_dark",
                          orientation='h',
                          text='totalRatings',
                          labels={'genre': 'Genre', 'totalRatings': 'Total Ratings', 'avgRating': 'Avg Rating'})
            fig3.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font_color='#e8e8ed', coloraxis_showscale=True,
                title_x=0.5, margin=dict(t=60, b=40),
                coloraxis_colorbar=dict(title='Avg<br>Rating', thickness=15)
            )
            fig3.update_traces(textposition='outside', textfont_size=12,
                               marker_line_color='#ffffff', marker_line_width=1.2,
                               opacity=0.92)
            st.plotly_chart(fig3, width='stretch')

            conn = get_db()
            timeline = pd.read_sql("""
                                   SELECT DATE (ratedAt) as date, COUNT (*) as ratings
                                   FROM ratings
                                   GROUP BY DATE (ratedAt)
                                   ORDER BY date
                                   """, conn)
            conn.close()
            if not timeline.empty:
                fig4 = px.area(timeline, x='date', y='ratings',
                               title="<b>Platform Ratings Activity Over Time</b>",
                               template="plotly_dark",
                               color_discrete_sequence=["#38BDF8"],
                               line_shape='spline')
                fig4.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#e8e8ed', showlegend=False,
                    title_x=0.5, margin=dict(t=60, b=40)
                )
                fig4.update_traces(line=dict(width=3), marker=dict(size=8, color='#ffffff',
                                    line=dict(width=2, color='#38BDF8')),
                                    fillcolor='rgba(56, 189, 248, 0.25)')
                st.plotly_chart(fig4, width='stretch')
        else:
            st.info("Global visualisations appear once multiple users have rated movies.")

    # ── Tab 5: My Profile
    with tab5:
        st.markdown("<div class='section-header'>Account & Preferences</div>", unsafe_allow_html=True)
        profile = get_user_profile(user[0])

        # ── Account info
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("**Account Details**")
            st.markdown(f"""
            <div class='movie-card'>
                <h4>👤 {profile.get('userName', '—')}</h4>
                <p>📧 {profile.get('email', '—')}</p>
                <p>📅 Member since: {profile.get('createdAt', '—')[:10]}</p>
                <p>✅ Status: <b>{profile.get('subscriptionStatus', 'active').capitalize()}</b></p>
            </div>
            """, unsafe_allow_html=True)

        with col_p2:
            st.markdown("**Subscription Status**")
            current_status = profile.get('subscriptionStatus', 'active')
            new_status = st.selectbox(
                "Account status",
                ["Active", "Inactive"],
                index=0 if current_status == "active" else 1,
                key="sub_status_select"
            )
            if st.button("Update Status"):
                update_subscriptionStatus(st.session_state.user_obj.userID, new_status.lower())
                st.success(f"Status updated to '{new_status}'.")
                st.rerun()

        st.markdown("---")

        # ── Update Preferences
        st.markdown("**Update Genre Preferences**")
        st.markdown("<p style='color:#8e8e9a; font-size:0.9rem;'>Updating your preferences recalibrates your recommendation engine — the system will weight your selected genres more heavily on your next visit.</p>", unsafe_allow_html=True)

        genres = ["Action", "Drama", "Sci-Fi", "Comedy", "Horror", "Romance", "Animation", "Crime", "Thriller", "Mystery", "Adventure", "Music"]
        current_prefs = profile.get('preferences', '')
        current_prefs_list = [p.strip() for p in current_prefs.split(",") if p.strip()] if current_prefs else []

        new_prefs = st.multiselect(
            "Select your favourite genres",
            genres,
            default=[p for p in current_prefs_list if p in genres],
            key="pref_multiselect"
        )
        if st.button("💾 Save Preferences"):
            if update_preferences(st.session_state.user_obj, ",".join(new_prefs)):
                st.success("Preferences updated! Your recommendations will reflect this on your next visit.")
                st.rerun()
            else:
                st.error("Failed to update preferences.")

        st.markdown("---")

        # ── Cached Recommendation List
        st.markdown("**Last Cached Recommendations**")
        st.markdown("<p style='color:#8e8e9a; font-size:0.9rem;'>Your most recently generated recommendation list, stored to your profile for quick access without re-running the algorithm.</p>", unsafe_allow_html=True)
        cached = profile.get('recommendationList', '')
        if cached:
            cached_titles = [t.strip() for t in cached.split(",") if t.strip()]
            for i, title in enumerate(cached_titles, 1):
                st.markdown(f"""
                <div class='movie-card' style='padding: 0.6rem 1rem;'>
                    <h4 style='font-size:0.95rem;'>#{i} &nbsp; {title}</h4>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No cached recommendations yet. Visit the Recommendations tab to generate your first list.")

# ══ ADMIN CONSOLE ═══
elif nav == "⚙️ Admin Console":
    st.markdown("<h2>Admin Console</h2>", unsafe_allow_html=True)

    if not st.session_state.admin_mode:
        st.markdown("<p style='color:#8e8e9a;'>This area is restricted to system administrators.</p>",
                    unsafe_allow_html=True)
        admin_input = st.text_input("Enter Admin Access Key", type="password")
        if st.button("Authenticate"):
            if admin_input == ADMIN_KEY:
                st.session_state.admin_mode = True
                st.success("Access granted.")
                st.rerun()
            else:
                st.error("Invalid admin key.")
    else:
        st.markdown(f"<p style='color:#0066CC;'>🔐 Authenticated as Administrator</p>", unsafe_allow_html=True)
        if st.button("🔒 Lock Admin Console"):
            st.session_state.admin_mode = False
            st.rerun()

        admin_tab1, admin_tab2, admin_tab3 = st.tabs(["➕ Add Movie", "✏️ Edit / Remove", "📊 Engagement Analytics"])

        # ── Admin Tab 1: Add Movie
        with admin_tab1:
            st.markdown("<div class='section-header'>Add New Movie</div>", unsafe_allow_html=True)

            form_defaults = {
                "a_title": "",
                "a_genre": "",
                "a_year": 2024,
                "a_director": "",
                "a_desc": "",
            }

            if "add_movie_success" in st.session_state:
                st.success(st.session_state.pop("add_movie_success"))
                for key, default in form_defaults.items():
                    st.session_state[key] = default
            else:
                for key, default in form_defaults.items():
                    if key not in st.session_state:
                        st.session_state[key] = default

            a_title = st.text_input("Movie Title", key="a_title")
            a_genre = st.text_input("Genre (e.g. Action/Sci-Fi)", key="a_genre")
            a_year = st.number_input("Release Year", min_value=1900, max_value=2030, key="a_year")
            a_director = st.text_input("Director", key="a_director")
            a_desc = st.text_area("Description", key="a_desc")

            if st.button("Add Movie"):
                if a_title and a_genre:
                    try:
                        add_movie(a_title, a_genre, a_year, a_director, a_desc)
                        st.session_state.add_movie_success = f"'{a_title}' added to the movie database."
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to add movie: {e}")
                else:
                    st.warning("Title and genre are required.")

        # ── Admin Tab 2: Edit / Remove
        with admin_tab2:
            if "edit_movie_success" in st.session_state:
                st.success(st.session_state.pop("edit_movie_success"))
            if "delete_movie_success" in st.session_state:
                st.success(st.session_state.pop("delete_movie_success"))

            st.markdown("<div class='section-header'>Edit or Remove Movies</div>", unsafe_allow_html=True)
            movies_df = get_all_movies()
            movie_options = {f"{row['title']} (ID: {row['movieID']})": row['movieID']
                             for _, row in movies_df.iterrows()}
            selected_label = st.selectbox("Select a movie", list(movie_options.keys()), key="admin_select_movie")
            selected_id = movie_options[selected_label]
            selected_row = movies_df[movies_df['movieID'] == selected_id].iloc[0]

            if st.session_state.get("admin_prev_movie") != selected_label:
                st.session_state.e_title = selected_row['title']
                st.session_state.e_genre = selected_row['genre']
                st.session_state.e_year = int(selected_row['releaseYear'])
                st.session_state.e_dir = selected_row['director']
                st.session_state.e_desc = selected_row['description']
                st.session_state.admin_prev_movie = selected_label

            e_title = st.text_input("Title", key="e_title")
            e_genre = st.text_input("Genre", key="e_genre")
            e_year = st.number_input("Year", min_value=1900, max_value=2030, key="e_year")
            e_director = st.text_input("Director", key="e_dir")
            e_desc = st.text_area("Description", key="e_desc")

            col_edit, col_del = st.columns(2)
            with col_edit:
                if st.button("💾 Save Changes"):
                    try:
                        update_movie(selected_id, e_title, e_genre, e_year, e_director, e_desc)
                        st.session_state.edit_movie_success = "Movie updated successfully."
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update movie: {e}")
            with col_del:
                if st.button("🗑️ Delete Movie", type="secondary"):
                    try:
                        delete_movie(selected_id)
                        st.session_state.delete_movie_success = f"'{selected_row['title']}' deleted successfully."
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete movie: {e}")

        # ── Admin Tab 3: Engagement Analytics
        with admin_tab3:
            st.markdown("<div class='section-header'>User Engagement Analytics</div>", unsafe_allow_html=True)
            most_watched, user_activity = get_engagement_stats()

            col_e1, col_e2 = st.columns(2)
            with col_e1:
                st.markdown("**Most Watched Movies**")
                fig_e1 = px.bar(
                    most_watched, x='watchCount', y='title', orientation='h',
                    title="Top 10 Most Watched",
                    color='watchCount',
                    color_continuous_scale=["#121820", "#0088FF"],
                    template="plotly_dark"
                )
                fig_e1.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#e8e8ed', showlegend=False,
                    coloraxis_showscale=False, yaxis_title="", xaxis_title="Watch Count"
                )
                st.plotly_chart(fig_e1, width='stretch')

            with col_e2:
                st.markdown("**Most Active Users**")
                if not user_activity.empty and user_activity['ratingsGiven'].sum() > 0:
                    fig_e2 = px.bar(
                        user_activity, x='userName', y='ratingsGiven',
                        title="Ratings per User",
                        color='ratingsGiven',
                        color_continuous_scale=["#121820", "#0066CC"],
                        template="plotly_dark"
                    )
                    fig_e2.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#e8e8ed', showlegend=False,
                        coloraxis_showscale=False
                    )
                    st.plotly_chart(fig_e2, width='stretch')
                else:
                    st.info("No user activity data yet.")

            st.markdown("---")
            st.markdown("**Raw Engagement Data**")
            st.dataframe(most_watched.rename(columns={"title": "Movie", "genre": "Genre", "watchCount": "Watches"}),
                         width='stretch', hide_index=True)