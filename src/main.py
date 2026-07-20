"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from src.recommender import load_songs, recommend_songs
except ModuleNotFoundError:
    from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Starter example profile
    user_prefs = {"favorite_genre": "pop", "favorite_mood": "happy", "target_energy": 0.8}

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print_recommendations(user_prefs, recommendations)


def print_recommendations(user_prefs, recommendations) -> None:
    """Render recommendations as a clean, readable terminal report."""
    width = 60

    print()
    print("=" * width)
    print("  TOP RECOMMENDATIONS".ljust(width))
    print(
        f"  for: genre={user_prefs.get('favorite_genre', '-')}, "
        f"mood={user_prefs.get('favorite_mood', '-')}, "
        f"energy={user_prefs.get('target_energy', '-')}"
    )
    print("=" * width)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        # Header line: rank, title, artist, and the final score right-aligned.
        title_line = f"{rank}. {song['title']} — {song['artist']}"
        score_tag = f"Score: {score:.2f}"
        print()
        print(f"{title_line}  {score_tag:>{max(0, width - len(title_line) - 2)}}")

        # Each reason on its own indented bullet line.
        for reason in explanation.split("; "):
            print(f"     • {reason}")

    print()
    print("=" * width)


if __name__ == "__main__":
    main()
