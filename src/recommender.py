import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# --- Scoring weights (the point-weighting strategy) -------------------------
# Tune these to change what the recommender prioritizes.
GENRE_MATCH_POINTS = 2.0   # +2.0 when the song's genre matches the user's favorite
MOOD_MATCH_POINTS = 1.0    # +1.0 when the song's mood matches the user's favorite
ENERGY_MATCH_POINTS = 2.0  # up to +2.0 based on how close energy is to the target

# --- Advanced feature weights (new attributes) -----------------------------
TAG_MATCH_POINTS = 0.5      # +0.5 per matching detailed mood tag...
MAX_TAG_POINTS = 1.5        # ...capped so tags can't dominate the score
DECADE_MATCH_POINTS = 1.0   # +1.0 when the song's release decade matches the favorite
POPULARITY_POINTS = 1.0     # up to +1.0 based on the user's mainstream/underground taste
LANGUAGE_MATCH_POINTS = 1.0 # +1.0 when the song's language matches the preference
EXPLICIT_PENALTY = 2.0      # -2.0 when a song is explicit but the user avoids explicit

# --- Diversity penalties (applied while building the top-k list) ------------
# These discourage the top results from piling up on one artist or genre.
ARTIST_DIVERSITY_PENALTY = 1.5  # subtracted per song already chosen from the same artist
GENRE_DIVERSITY_PENALTY = 0.75  # subtracted per song already chosen from the same genre


@dataclass
class ScoringWeights:
    """A bundle of scoring weights — the tunable knobs of a ranking strategy.

    Every RankingStrategy carries one of these. The scoring engine reads the
    weights from here instead of the module constants, so a new ranking mode is
    just a new set of numbers (no duplicated scoring code).
    """
    genre: float = GENRE_MATCH_POINTS
    mood: float = MOOD_MATCH_POINTS
    energy: float = ENERGY_MATCH_POINTS
    tag: float = TAG_MATCH_POINTS
    max_tag: float = MAX_TAG_POINTS
    decade: float = DECADE_MATCH_POINTS
    popularity: float = POPULARITY_POINTS
    language: float = LANGUAGE_MATCH_POINTS
    explicit_penalty: float = EXPLICIT_PENALTY
    # Diversity re-ranking penalties (0.0 disables that penalty)
    artist_penalty: float = ARTIST_DIVERSITY_PENALTY
    genre_penalty: float = GENRE_DIVERSITY_PENALTY


# The default weights reproduce the original balanced scoring behavior.
DEFAULT_WEIGHTS = ScoringWeights()


def parse_tags(value) -> set:
    """Normalize detailed mood tags into a lowercased set.

    Accepts either a list/tuple/set of tags or a delimited string like
    "chill|focused|mellow" (also tolerates commas). Returns an empty set for
    missing/empty input so callers never have to null-check.
    """
    if not value:
        return set()
    if isinstance(value, (list, tuple, set)):
        items = value
    else:
        items = str(value).replace(",", "|").split("|")
    return {str(t).strip().lower() for t in items if str(t).strip()}


def _popularity_points(pref: Optional[str], popularity: float,
                       points: float = POPULARITY_POINTS) -> float:
    """Convert a popularity taste into points (0..points).

    "mainstream"/"popular" rewards high popularity; "underground"/"niche"
    rewards low popularity. Anything else (or no preference) scores 0.
    """
    if not pref:
        return 0.0
    p = pref.lower()
    if p in ("mainstream", "popular"):
        return (popularity / 100.0) * points
    if p in ("underground", "niche"):
        return ((100.0 - popularity) / 100.0) * points
    return 0.0


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
    # Advanced attributes (default so existing tests can omit them)
    popularity: float = 0.0          # 0-100 chart popularity
    release_decade: int = 0          # e.g. 1980, 1990, 2020
    mood_tags: str = ""              # detailed tags, e.g. "chill|focused|mellow"
    language: str = ""               # e.g. "english", "instrumental"
    explicit: bool = False           # explicit-content flag

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
    # Advanced preferences (all optional — omit to ignore that feature)
    favorite_decade: Optional[int] = None      # match a release decade
    mood_tags: Optional[List[str]] = None       # detailed mood tags to reward
    popularity_pref: Optional[str] = None       # "mainstream" or "underground"
    preferred_language: Optional[str] = None    # e.g. "english", "instrumental"
    allow_explicit: bool = True                 # False => penalize explicit songs

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

        # Detailed mood tags: reward each tag the song shares with the user's wishlist
        user_tags = parse_tags(user.mood_tags)
        if user_tags:
            overlap = user_tags & parse_tags(song.mood_tags)
            if overlap:
                tag_points = min(len(overlap) * TAG_MATCH_POINTS, MAX_TAG_POINTS)
                score += tag_points
                reasons.append(f"mood tags match ({', '.join(sorted(overlap))}) (+{tag_points:.1f})")

        # Release decade: flat bonus for the user's favorite era
        if user.favorite_decade is not None and song.release_decade == user.favorite_decade:
            score += DECADE_MATCH_POINTS
            reasons.append(f"from your favorite era ({song.release_decade}s) (+{DECADE_MATCH_POINTS:.1f})")

        # Popularity taste: reward mainstream hits or underground gems
        pop_points = _popularity_points(user.popularity_pref, song.popularity)
        if pop_points > 0:
            score += pop_points
            reasons.append(
                f"{user.popularity_pref.lower()} pick (popularity {song.popularity:.0f}) (+{pop_points:.1f})"
            )

        # Language preference: flat bonus for a matching language/instrumental
        if user.preferred_language and song.language.lower() == user.preferred_language.lower():
            score += LANGUAGE_MATCH_POINTS
            reasons.append(f"language match ({song.language}) (+{LANGUAGE_MATCH_POINTS:.1f})")

        # Explicit filter: penalize explicit songs when the user avoids them
        if not user.allow_explicit and song.explicit:
            score -= EXPLICIT_PENALTY
            reasons.append(f"explicit content you avoid (-{EXPLICIT_PENALTY:.1f})")

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
                "popularity": float(row.get("popularity", 0) or 0),
                "release_decade": int(row.get("release_decade", 0) or 0),
                "mood_tags": row.get("mood_tags", "") or "",
                "language": row.get("language", "") or "",
                "explicit": str(row.get("explicit", "")).strip().lower() == "true",
            })
    return songs

def score_song(user_prefs: Dict, song: Dict,
               weights: ScoringWeights = DEFAULT_WEIGHTS) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py

    The `weights` bundle sets how strongly each factor counts. Different ranking
    strategies (genre-first, mood-first, energy-focused, ...) pass different
    weights here — the scoring math itself stays the same.

    Point-weighting strategy (with DEFAULT_WEIGHTS):
      +2.0   genre match
      +1.0   mood match
      +0-2.0 energy closeness (rewards being near target_energy)
      +0.5   per matching detailed mood tag (capped at +1.5)
      +1.0   release decade match
      +0-1.0 popularity taste (mainstream vs. underground)
      +1.0   language match
      -2.0   explicit song when the user avoids explicit content
    """
    score = 0.0
    reasons: List[str] = []

    if song["genre"] == user_prefs.get("favorite_genre", user_prefs.get("genre")):
        score += weights.genre
        reasons.append(f"genre match ({song['genre']}) (+{weights.genre:.1f})")

    if song["mood"] == user_prefs.get("favorite_mood", user_prefs.get("mood")):
        score += weights.mood
        reasons.append(f"mood match ({song['mood']}) (+{weights.mood:.1f})")

    target_energy = user_prefs.get("target_energy", user_prefs.get("energy"))
    if target_energy is not None:
        closeness = 1.0 - abs(target_energy - song["energy"])
        energy_points = closeness * weights.energy
        score += energy_points
        if closeness >= 0.85:
            reasons.append(
                f"energy ({song['energy']:.2f}) close to target ({target_energy:.2f}) (+{energy_points:.1f})"
            )

    # Detailed mood tags: reward each tag the song shares with the user's wishlist
    user_tags = parse_tags(user_prefs.get("mood_tags"))
    if user_tags:
        overlap = user_tags & parse_tags(song.get("mood_tags"))
        if overlap:
            tag_points = min(len(overlap) * weights.tag, weights.max_tag)
            score += tag_points
            reasons.append(f"mood tags match ({', '.join(sorted(overlap))}) (+{tag_points:.1f})")

    # Release decade: flat bonus for the user's favorite era
    favorite_decade = user_prefs.get("favorite_decade")
    if favorite_decade is not None and song.get("release_decade") == favorite_decade:
        score += weights.decade
        reasons.append(f"from your favorite era ({song['release_decade']}s) (+{weights.decade:.1f})")

    # Popularity taste: reward mainstream hits or underground gems
    pop_pref = user_prefs.get("popularity_pref")
    pop_points = _popularity_points(pop_pref, song.get("popularity", 0.0), weights.popularity)
    if pop_points > 0:
        score += pop_points
        reasons.append(
            f"{pop_pref.lower()} pick (popularity {song.get('popularity', 0.0):.0f}) (+{pop_points:.1f})"
        )

    # Language preference: flat bonus for a matching language/instrumental
    preferred_language = user_prefs.get("preferred_language")
    if preferred_language and str(song.get("language", "")).lower() == preferred_language.lower():
        score += weights.language
        reasons.append(f"language match ({song['language']}) (+{weights.language:.1f})")

    # Explicit filter: penalize explicit songs when the user avoids them
    if not user_prefs.get("allow_explicit", True) and song.get("explicit", False):
        score -= weights.explicit_penalty
        reasons.append(f"explicit content you avoid (-{weights.explicit_penalty:.1f})")

    if not reasons:
        reasons.append("weak overall match")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5,
                    weights: ScoringWeights = DEFAULT_WEIGHTS) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py

    Pass a `weights` bundle to rank with a specific strategy; the default
    reproduces the original balanced behavior.

    The top-k list is built greedily with a DIVERSITY PENALTY: once a song is
    chosen, other candidates by the same artist or in the same genre are docked
    points, so the list does not fill up with near-duplicates. Set
    weights.artist_penalty / weights.genre_penalty to 0.0 to turn this off.
    """
    # 1. Base score every song once (independent of the diversity re-ranking).
    scored = [
        {"song": song, "base": base, "reasons": reasons}
        for song in songs
        for base, reasons in [score_song(user_prefs, song, weights)]
    ]

    # 2. Greedily pull the best remaining song, penalizing repeats of an
    #    artist/genre that is already present in the chosen list.
    selected: List[Tuple[Dict, float, str]] = []
    artist_counts: Dict[str, int] = {}
    genre_counts: Dict[str, int] = {}
    remaining = list(scored)

    while remaining and len(selected) < k:
        best_idx = 0
        best_adj = None
        best_penalty = 0.0
        for i, item in enumerate(remaining):
            song = item["song"]
            penalty = (artist_counts.get(song["artist"], 0) * weights.artist_penalty
                       + genre_counts.get(song["genre"], 0) * weights.genre_penalty)
            adj = item["base"] - penalty
            # Strict '>' keeps the first (higher base / earlier) song on ties.
            if best_adj is None or adj > best_adj:
                best_idx, best_adj, best_penalty = i, adj, penalty

        item = remaining.pop(best_idx)
        song = item["song"]
        reasons = list(item["reasons"])
        if best_penalty > 0:
            bits = []
            a_hits = artist_counts.get(song["artist"], 0)
            g_hits = genre_counts.get(song["genre"], 0)
            if a_hits:
                bits.append(f"{a_hits} already by {song['artist']}")
            if g_hits:
                bits.append(f"{g_hits} already {song['genre']}")
            reasons.append(f"diversity penalty ({'; '.join(bits)}) (-{best_penalty:.1f})")

        selected.append((song, best_adj, "; ".join(reasons)))
        artist_counts[song["artist"]] = artist_counts.get(song["artist"], 0) + 1
        genre_counts[song["genre"]] = genre_counts.get(song["genre"], 0) + 1

    return selected


# --- Ranking strategies (the Strategy pattern) ------------------------------
# Each strategy is a named bundle of scoring weights plus a shared rank()
# method. Swapping strategies changes what the recommender prioritizes WITHOUT
# touching the scoring engine — that is the whole point of the pattern.

class RankingStrategy:
    """Base strategy. Concrete modes override `name`, `description`, `weights`."""
    name: str = "balanced"
    description: str = "Weighs every factor at its normal strength."
    weights: ScoringWeights = DEFAULT_WEIGHTS

    def score(self, user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
        """Score one song using this strategy's weights."""
        return score_song(user_prefs, song, self.weights)

    def rank(self, user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
        """Return the top-k (song, score, explanation) tuples for this strategy."""
        return recommend_songs(user_prefs, songs, k, self.weights)


class BalancedStrategy(RankingStrategy):
    """The original all-round scorer."""
    name = "balanced"
    description = "Balances genre, mood, and energy evenly (the original scorer)."
    weights = DEFAULT_WEIGHTS


class GenreFirstStrategy(RankingStrategy):
    """Genre dominates; everything else is a tie-breaker."""
    name = "genre-first"
    description = "Locks onto your favorite genre above all else."
    weights = ScoringWeights(genre=4.0, mood=1.0, energy=1.0, tag=0.5,
                             decade=0.5, popularity=0.5, language=0.5)


class MoodFirstStrategy(RankingStrategy):
    """Chases the feeling — mood and detailed mood tags carry the ranking."""
    name = "mood-first"
    description = "Prioritizes mood and detailed mood tags over genre."
    weights = ScoringWeights(genre=1.0, mood=3.0, energy=1.0, tag=1.0, max_tag=3.0,
                             decade=0.5, popularity=0.5, language=0.5)


class EnergyFocusedStrategy(RankingStrategy):
    """Matches your target energy first; genre and mood only break ties."""
    name = "energy-focused"
    description = "Matches your target energy first; genre/mood are tie-breakers."
    weights = ScoringWeights(genre=1.0, mood=0.5, energy=4.0, tag=0.25,
                             decade=0.5, popularity=0.5, language=0.5)


# Registry so callers (e.g. main.py) can pick a strategy by name.
STRATEGIES: Dict[str, RankingStrategy] = {
    strat.name: strat
    for strat in (BalancedStrategy(), GenreFirstStrategy(),
                  MoodFirstStrategy(), EnergyFocusedStrategy())
}


def get_strategy(name: Optional[str]) -> RankingStrategy:
    """Look up a strategy by name (case-insensitive); falls back to balanced."""
    return STRATEGIES.get(str(name).strip().lower(), STRATEGIES["balanced"])
