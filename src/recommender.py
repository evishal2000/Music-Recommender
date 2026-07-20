import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# --- Scoring weights (the point-weighting strategy) -------------------------
# Tune these to change what the recommender prioritizes.
GENRE_MATCH_POINTS = 2.0   # +2.0 when the song's genre matches the user's favorite
MOOD_MATCH_POINTS = 1.0    # +1.0 when the song's mood matches the user's favorite
ENERGY_MATCH_POINTS = 2.0  # up to +2.0 based on how close energy is to the target


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        """Store the song catalog this recommender will rank."""
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        """Score a single Song against a UserProfile. Returns (score, reasons)."""
        score = 0.0
        reasons: List[str] = []

        # Genre match: flat point bonus
        if song.genre == user.favorite_genre:
            score += GENRE_MATCH_POINTS
            reasons.append(f"genre match ({song.genre}) (+{GENRE_MATCH_POINTS:.1f})")

        # Mood match: flat point bonus
        if song.mood == user.favorite_mood:
            score += MOOD_MATCH_POINTS
            reasons.append(f"mood match ({song.mood}) (+{MOOD_MATCH_POINTS:.1f})")

        # Energy closeness: rewards being NEAR the target, not just high/low.
        # closeness is 1.0 at a perfect match and 0.0 at the opposite end.
        closeness = 1.0 - abs(user.target_energy - song.energy)
        energy_points = closeness * ENERGY_MATCH_POINTS
        score += energy_points
        if closeness >= 0.85:
            reasons.append(
                f"energy ({song.energy:.2f}) close to target ({user.target_energy:.2f}) (+{energy_points:.1f})"
            )

        # Acoustic preference: nudge toward/away from acoustic tracks
        if user.likes_acoustic and song.acousticness >= 0.6:
            score += 0.5
            reasons.append("acoustic, which you like (+0.5)")

        if not reasons:
            reasons.append("weak overall match")

        return score, reasons

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k songs for the user, ranked by score (highest first)."""
        ranked = sorted(self.songs, key=lambda s: self._score(user, s)[0], reverse=True)
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a one-line, human-readable explanation of a song's score."""
        score, reasons = self._score(user, song)
        return f"Score {score:.2f} — " + "; ".join(reasons)

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("id"):  # skip blank trailing lines
                continue
            songs.append({
                "id": int(row["id"]),
                "title": row["title"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mood": row["mood"],
                "energy": float(row["energy"]),
                "tempo_bpm": float(row["tempo_bpm"]),
                "valence": float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py

    Point-weighting strategy:
      +2.0  genre match
      +1.0  mood match
      +0-2.0 energy closeness (rewards being near target_energy)
    """
    score = 0.0
    reasons: List[str] = []

    if song["genre"] == user_prefs.get("favorite_genre", user_prefs.get("genre")):
        score += GENRE_MATCH_POINTS
        reasons.append(f"genre match ({song['genre']}) (+{GENRE_MATCH_POINTS:.1f})")

    if song["mood"] == user_prefs.get("favorite_mood", user_prefs.get("mood")):
        score += MOOD_MATCH_POINTS
        reasons.append(f"mood match ({song['mood']}) (+{MOOD_MATCH_POINTS:.1f})")

    target_energy = user_prefs.get("target_energy", user_prefs.get("energy"))
    if target_energy is not None:
        closeness = 1.0 - abs(target_energy - song["energy"])
        energy_points = closeness * ENERGY_MATCH_POINTS
        score += energy_points
        if closeness >= 0.85:
            reasons.append(
                f"energy ({song['energy']:.2f}) close to target ({target_energy:.2f}) (+{energy_points:.1f})"
            )

    if not reasons:
        reasons.append("weak overall match")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        scored.append((song, score, "; ".join(reasons)))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]
