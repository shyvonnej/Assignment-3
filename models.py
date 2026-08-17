"""
OOP models for Cineverse: User, RegisteredUser, and Movie.
"""
import hashlib
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class User:
    """Base user class for authentication and ratings."""

    def __init__(self, userID: int, userName: str, email: str, passwordHash: str):
        self.__userID = userID
        self.__userName = userName
        self.__email = email
        self.__password = passwordHash
        self.__watchHistory = []

    @property
    def userID(self) -> int:
        return self.__userID

    @property
    def userName(self) -> str:
        return self.__userName

    @property
    def email(self) -> str:
        return self.__email

    @property
    def watchHistory(self) -> List:
        return self.__watchHistory

    @staticmethod
    def __hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def register(userName: str, email: str, password: str, preferences: str = "", db_path: str = "mrs_database.db") -> Tuple[bool, str]:
        """Create a new user account."""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            passwordHash = User.__hash_password(password)
            c.execute(
                "INSERT INTO users (userName, email, passwordHash, preferences) VALUES (?,?,?,?)",
                (userName, email, passwordHash, preferences)
            )
            conn.commit()
            conn.close()
            return True, "Account created successfully!"
        except sqlite3.IntegrityError:
            return False, "Username or email already exists."
        except Exception as e:
            return False, f"Registration failed: {str(e)}"

    @staticmethod
    def login(userName: str, password: str, db_path: str = "mrs_database.db") -> Optional['User']:
        """Authenticate a user and return a User/RegisteredUser instance."""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            passwordHash = User.__hash_password(password)
            c.execute(
                "SELECT userID, userName, email, passwordHash, preferences FROM users WHERE userName=? AND passwordHash=?",
                (userName, passwordHash)
            )
            result = c.fetchone()
            conn.close()

            if result:
                userID, userName, email, passwordHash, preferences = result
                if preferences:
                    return RegisteredUser(userID, userName, email, passwordHash, preferences)
                return User(userID, userName, email, passwordHash)
            return None
        except Exception as e:
            print(f"Login error: {e}")
            return None

    def rateMovie(self, movieID: int, rating: float, db_path: str = "mrs_database.db") -> bool:
        """Record a rating and update watch history."""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()

            c.execute(
                "SELECT ratingID FROM ratings WHERE userID=? AND movieID=?",
                (self.__userID, movieID)
            )
            existing = c.fetchone()

            if existing:
                c.execute(
                    "UPDATE ratings SET rating=?, ratedAt=? WHERE userID=? AND movieID=?",
                    (rating, datetime.now().isoformat(), self.__userID, movieID)
                )
            else:
                c.execute(
                    "INSERT INTO ratings (userID, movieID, rating) VALUES (?,?,?)",
                    (self.__userID, movieID, rating)
                )

            c.execute(
                "INSERT OR IGNORE INTO watchHistory (userID, movieID) VALUES (?,?)",
                (self.__userID, movieID)
            )

            conn.commit()
            conn.close()

            if movieID not in self.__watchHistory:
                self.__watchHistory.append(movieID)

            return True
        except Exception as e:
            print(f"Rating error: {e}")
            return False


class RegisteredUser(User):
    """User with preferences, subscription status, and recommendations."""

    def __init__(self, userID: int, userName: str, email: str, passwordHash: str, preferences: str = ""):
        super().__init__(userID, userName, email, passwordHash)
        self.__preferences = preferences
        self.__subscriptionStatus = True
        self.__recommendationList = []

    @property
    def preferences(self) -> str:
        return self.__preferences

    @property
    def subscriptionStatus(self) -> bool:
        return self.__subscriptionStatus

    @property
    def recommendationList(self) -> List:
        return self.__recommendationList

    def getDashboard(self, db_path: str = "mrs_database.db") -> Dict:
        """Fetch dashboard stats for the user."""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()

            c.execute("SELECT COUNT(*) FROM ratings WHERE userID=?", (self.userID,))
            totalRatings = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM watchHistory WHERE userID=?", (self.userID,))
            totalWatched = c.fetchone()[0]

            c.execute("SELECT AVG(rating) FROM ratings WHERE userID=?", (self.userID,))
            avgRating = c.fetchone()[0] or 0

            conn.close()

            return {
                'userName': self.userName,
                'email': self.email,
                'preferences': self.__preferences,
                'subscriptionStatus': self.__subscriptionStatus,
                'totalRatings': totalRatings,
                'totalWatched': totalWatched,
                'avgRating': round(avgRating, 2),
                'recommendations': self.__recommendationList
            }
        except Exception as e:
            print(f"Dashboard error: {e}")
            return {}

    def getMovieRecommendation(self, engine, db_path: str = "mrs_database.db") -> List[Dict]:
        """Generate and store personalised recommendations."""
        try:
            import pandas as pd
            conn = sqlite3.connect(db_path)

            user_ratings = pd.read_sql(
                "SELECT movieID, rating FROM ratings WHERE userID=?",
                conn,
                params=(self.userID,)
            )

            recommendations = engine.generate_recommendations(self.userID, user_ratings)

            conn.close()

            self.__recommendationList = recommendations.to_dict('records')

            return self.__recommendationList
        except Exception as e:
            print(f"Recommendation error: {e}")
            return []

    def updatePreferences(self, new_preferences: str, db_path: str = "mrs_database.db") -> bool:
        """Update the user's genre preferences."""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute(
                "UPDATE users SET preferences=? WHERE userID=?",
                (new_preferences, self.userID)
            )
            conn.commit()
            conn.close()

            self.__preferences = new_preferences
            return True
        except Exception as e:
            print(f"Update preferences error: {e}")
            return False


class Movie:
    """Movie record with ratings and search capability."""

    def __init__(self, movieID: int, title: str, genre: str, releaseYear: int = 0,
                 avgRating: float = 0.0, director: str = "", description: str = "",
                 ratingCount: int = 0):
        self.__movieID = movieID
        self.__title = title
        self.__genre = genre
        self.__releaseYear = releaseYear
        self.__avgRating = avgRating
        self.__director = director
        self.__description = description
        self.__ratingCount = ratingCount

    @property
    def movieID(self) -> int:
        return self.__movieID

    @property
    def title(self) -> str:
        return self.__title

    @property
    def genre(self) -> str:
        return self.__genre

    @property
    def releaseYear(self) -> int:
        return self.__releaseYear

    @property
    def avgRating(self) -> float:
        return self.__avgRating

    @property
    def ratingCount(self) -> int:
        return self.__ratingCount

    def getMovieDetails(self) -> Dict:
        """Return all movie attributes as a dictionary."""
        return {
            'movieID': self.__movieID,
            'title': self.__title,
            'genre': self.__genre,
            'releaseYear': self.__releaseYear,
            'avgRating': round(self.__avgRating, 2),
            'director': self.__director,
            'description': self.__description,
            'ratingCount': self.__ratingCount
        }

    def updateMovieRating(self, db_path: str = "mrs_database.db") -> bool:
        """Recalculate and store the movie's average rating and rating count."""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()

            c.execute(
                "SELECT AVG(rating), COUNT(rating) FROM ratings WHERE movieID=?",
                (self.__movieID,)
            )
            avg, count = c.fetchone()

            self.__ratingCount = int(count or 0)
            if avg is not None:
                self.__avgRating = float(avg)

            c.execute(
                "UPDATE movies SET avgRating=?, ratingCount=? WHERE movieID=?",
                (self.__avgRating, self.__ratingCount, self.__movieID)
            )
            conn.commit()

            conn.close()
            return True
        except Exception as e:
            print(f"Update rating error: {e}")
            return False

    @staticmethod
    def search(query: str = "", genre: str = "", director: str = "", db_path: str = "mrs_database.db") -> List['Movie']:
        """Search movies by title, genre, or director."""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()

            sql = "SELECT movieID, title, genre, releaseYear, avgRating, director, description, ratingCount FROM movies WHERE 1=1"
            params = []

            if query:
                sql += " AND (title LIKE ? OR genre LIKE ? OR director LIKE ?)"
                params.extend([f"%{query}%"] * 3)

            if genre:
                sql += " AND genre LIKE ?"
                params.append(f"%{genre}%")

            if director:
                sql += " AND director LIKE ?"
                params.append(f"%{director}%")

            c.execute(sql, params)
            results = c.fetchall()
            conn.close()

            movies = []
            for row in results:
                movie = Movie(
                    movieID=row[0],
                    title=row[1],
                    genre=row[2],
                    releaseYear=row[3] or 0,
                    avgRating=row[4] or 0.0,
                    director=row[5] or "",
                    description=row[6] or "",
                    ratingCount=row[7] or 0
                )
                movies.append(movie)

            return movies
        except Exception as e:
            print(f"Search error: {e}")
            return []
