"""
RecommendationEngine — hybrid content-based + collaborative filtering.
"""
import pandas as pd
import numpy as np


class RecommendationEngine:
    """Generates movie recommendations from ratings and catalogue data."""

    def __init__(self, all_movies: pd.DataFrame, all_ratings: pd.DataFrame):
        self.__algorithmType = "hybrid"
        self.all_movies = all_movies.copy()
        self.all_ratings = all_ratings.copy()
        self.__userDataMatrix = self._build_user_data_matrix()
        self.__genreWeights = {}

    # Getters
    @property
    def algorithmType(self) -> str:
        return self.__algorithmType

    @property
    def userDataMatrix(self) -> pd.DataFrame:
        return self.__userDataMatrix

    @property
    def genreWeights(self) -> dict:
        return self.__genreWeights

    # ── Private helpers ───

    def _build_user_data_matrix(self) -> pd.DataFrame:
        """User-movie rating pivot matrix for collaborative filtering."""
        if self.all_ratings.empty:
            return pd.DataFrame()
        matrix = self.all_ratings.pivot_table(
            index='userID', columns='movieID', values='rating'
        )
        self.__userDataMatrix = matrix
        return matrix

    def computeGenreWeights(self, user_ratings: pd.DataFrame) -> dict:
        """Build normalised genre weights from a user's ratings."""
        if user_ratings.empty:
            return {}

        weights = {}
        for _, row in user_ratings.iterrows():
            movie = self.all_movies[self.all_movies['movieID'] == row['movieID']]
            if movie.empty:
                continue
            genre = movie.iloc[0]['genre']
            weights[genre] = weights.get(genre, 0) + row['rating']

        total = sum(weights.values())
        if total > 0:
            weights = {g: w / total for g, w in weights.items()}

        self.__genreWeights = weights
        return weights

    def _content_based_score(self, movie_row: pd.Series, genre_weights: dict) -> float:
        """Score a movie by how well its genre matches the user's preferences."""
        genre = movie_row['genre']
        if genre in genre_weights:
            return genre_weights[genre]
        for g, w in genre_weights.items():
            if g.lower() in genre.lower() or genre.lower() in g.lower():
                return w * 0.75
        return 0.1

    def _collaborative_score(self, userID: int, movieID: int) -> float:
        """Score a movie using cosine similarity with other users."""
        if self.__userDataMatrix.empty:
            return 0.0
        if movieID not in self.__userDataMatrix.columns:
            return 0.0

        movie_raters = self.__userDataMatrix[movieID].dropna()
        if movie_raters.empty:
            return 0.0

        if userID not in self.__userDataMatrix.index:
            return float(movie_raters.mean()) / 5.0

        user_row = self.__userDataMatrix.loc[userID].dropna()
        scores = []

        for other_id, other_rating in movie_raters.items():
            if other_id == userID:
                continue
            other_row = self.__userDataMatrix.loc[other_id].dropna()

            common = user_row.index.intersection(other_row.index)
            if len(common) == 0:
                continue

            u = user_row[common].values.astype(float)
            v = other_row[common].values.astype(float)
            norm = np.linalg.norm(u) * np.linalg.norm(v)
            similarity = float(np.dot(u, v) / norm) if norm > 0 else 0.0

            if similarity > 0:
                scores.append((similarity, other_rating))

        if not scores:
            return float(movie_raters.mean()) / 5.0

        weighted = sum(sim * r for sim, r in scores)
        total_sim = sum(sim for sim, _ in scores)
        return (weighted / total_sim) / 5.0 if total_sim > 0 else 0.0

    # ── Public API ───

    def analyseUserBehaviour(self, userID: int, user_ratings: pd.DataFrame) -> dict:
        """Summarise a user's top genres and average rating."""
        self.__genreWeights = self.computeGenreWeights(user_ratings)
        topGenres = sorted(self.__genreWeights.items(), key=lambda x: x[1], reverse=True)[:3]
        avg = user_ratings['rating'].mean() if not user_ratings.empty else 0
        return {
            'topGenres': topGenres,
            'avgRating': round(avg, 2),
            'totalRated': len(user_ratings)
        }

    def rankMovies(self, candidates: pd.DataFrame, scores: dict) -> pd.DataFrame:
        """Attach scores and rank candidates from highest to lowest."""
        candidates = candidates.copy()
        candidates['score'] = candidates['movieID'].map(scores).fillna(0)
        return candidates.sort_values('score', ascending=False)

    def generate_recommendations(self, userID: int, user_ratings: pd.DataFrame) -> pd.DataFrame:
        """Return ranked recommendations for a user."""
        if user_ratings.empty:
            return self.all_movies.sort_values('avgRating', ascending=False).head(8)

        rated_ids = set(user_ratings['movieID'].tolist())
        candidates = self.all_movies[~self.all_movies['movieID'].isin(rated_ids)].copy()

        if candidates.empty:
            return pd.DataFrame()

        self.analyseUserBehaviour(userID, user_ratings)

        scores = {}
        content_scores = {}
        for _, movie in candidates.iterrows():
            cb_score = self._content_based_score(movie, self.__genreWeights)
            cf_score = self._collaborative_score(userID, movie['movieID'])
            scores[movie['movieID']] = 0.5 * cb_score + 0.5 * cf_score
            content_scores[movie['movieID']] = cb_score

        ranked = self.rankMovies(candidates, scores)
        max_weight = max(self.__genreWeights.values()) if self.__genreWeights else 1.0
        ranked['content_score'] = ranked['movieID'].map(content_scores).fillna(0.0)
        ranked['match_pct'] = (ranked['content_score'] / max_weight * 100).clip(0, 100).astype(int)
        return ranked
