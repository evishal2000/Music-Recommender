"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

Pick a ranking strategy with --mode:
    python -m src.main                     # balanced (default)
    python -m src.main --mode mood-first
    python -m src.main --mode all          # every mode, for comparison
    python -m src.main --list-modes        # show the available modes
"""

import argparse
import textwrap

try:
    from src.recommender import load_songs, get_strategy, STRATEGIES
except ModuleNotFoundError:
    from recommender import load_songs, get_strategy, STRATEGIES


# Example listener profiles, each expressed as a user-preference dictionary.
# The advanced keys (mood_tags, favorite_decade, popularity_pref,
# preferred_language, allow_explicit) are all optional — omit any to ignore it.
PROFILES = {
    "High-Energy Pop": {
        "favorite_genre": "pop", "favorite_mood": "happy", "target_energy": 0.85,
        "mood_tags": ["uplifting", "sunny"], "favorite_decade": 2020,
        "popularity_pref": "mainstream", "allow_explicit": False,
    },
    "Chill Lofi": {
        "favorite_genre": "lofi", "favorite_mood": "chill", "target_energy": 0.35,
        "mood_tags": ["calm", "focused"], "preferred_language": "instrumental",
        "popularity_pref": "underground",
    },
    "Deep Intense Rock": {
        "favorite_genre": "rock", "favorite_mood": "intense", "target_energy": 0.9,
        "mood_tags": ["driving", "dark"], "favorite_decade": 2010,
    },
    "Retro Synthwave Night": {
        "favorite_genre": "synthwave", "favorite_mood": "moody", "target_energy": 0.75,
        "mood_tags": ["nostalgic", "nocturnal"], "favorite_decade": 1980,
        "preferred_language": "instrumental",
    },
}


def main() -> None:
    args = parse_args()

    if args.list_modes:
        print("Available ranking modes:")
        for name, strat in STRATEGIES.items():
            print(f"  {name:<15} {strat.description}")
        print(f"  {'all':<15} Run every mode above, one after another (for comparison).")
        return

    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Choose which strategy (or strategies) to run.
    if args.mode.lower() == "all":
        strategies = list(STRATEGIES.values())
    else:
        if args.mode.lower() not in STRATEGIES:
            print(f"Unknown mode '{args.mode}' — falling back to balanced. "
                  f"Use --list-modes to see options.")
        strategies = [get_strategy(args.mode)]

    # Run each example profile through each chosen strategy.
    for strat in strategies:
        for name, user_prefs in PROFILES.items():
            recommendations = strat.rank(user_prefs, songs, k=5)
            print_recommendations(name, user_prefs, recommendations, strat)


def parse_args() -> argparse.Namespace:
    """Parse command-line options for choosing a ranking mode."""
    parser = argparse.ArgumentParser(description="Music Recommender Simulation")
    parser.add_argument(
        "--mode", default="balanced",
        help="ranking strategy: " + ", ".join(STRATEGIES) + ", or 'all'",
    )
    parser.add_argument(
        "--list-modes", action="store_true",
        help="list the available ranking modes and exit",
    )
    return parser.parse_args()


# Column widths for the recommendations table (inner text width, no padding).
COLUMNS = [
    ("#", 2, "r"),
    ("Song", 24, "l"),
    ("Genre", 10, "l"),
    ("Score", 6, "r"),
    ("Why it matched", 46, "l"),
]


def print_recommendations(profile_name, user_prefs, recommendations, strategy=None) -> None:
    """Render recommendations as a formatted ASCII table with per-song reasons."""
    # --- Summary header -----------------------------------------------------
    title = f"TOP RECOMMENDATIONS — {profile_name}"
    subtitle = (
        f"mode: {strategy.name}   |   " if strategy is not None else ""
    ) + (
        f"genre={user_prefs.get('favorite_genre', '-')}, "
        f"mood={user_prefs.get('favorite_mood', '-')}, "
        f"energy={user_prefs.get('target_energy', '-')}"
    )
    print()
    print(title)
    print(subtitle)

    # --- Build one wrapped-cell row per recommendation ----------------------
    rows = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        song_cell = f"{song['title']} — {song['artist']}"
        # Each reason becomes its own bullet, wrapped to the column width.
        reason_cell = "\n".join(f"• {r}" for r in explanation.split("; "))
        rows.append([str(rank), song_cell, song["genre"], f"{score:.2f}", reason_cell])

    print(_render_table(COLUMNS, rows))


def _render_table(columns, rows) -> str:
    """Render a box-drawing table. Cells wrap to each column's width and may
    span multiple lines; the reasons column uses this to list every reason."""
    headers = [c[0] for c in columns]
    widths = [c[1] for c in columns]
    aligns = [c[2] for c in columns]

    def wrap_cell(text, width):
        """Wrap one cell into a list of lines that each fit `width`."""
        lines = []
        for para in str(text).split("\n"):
            # Keep the "• " hanging indent so wrapped reason lines line up.
            wrapped = textwrap.wrap(
                para, width=width,
                subsequent_indent="  " if para.startswith("• ") else "",
            )
            lines.extend(wrapped or [""])
        return lines

    def pad(text, width, align):
        return text.rjust(width) if align == "r" else text.ljust(width)

    # Horizontal borders, e.g. ├────┼────┤
    def border(left, mid, right):
        return left + mid.join("─" * (w + 2) for w in widths) + right

    def build_row(cells):
        """Turn one logical row (list of cell strings) into printed line(s)."""
        wrapped = [wrap_cell(cells[i], widths[i]) for i in range(len(columns))]
        height = max(len(w) for w in wrapped)
        out = []
        for line_i in range(height):
            parts = []
            for i in range(len(columns)):
                piece = wrapped[i][line_i] if line_i < len(wrapped[i]) else ""
                parts.append(" " + pad(piece, widths[i], aligns[i]) + " ")
            out.append("│" + "│".join(parts) + "│")
        return "\n".join(out)

    lines = [border("┌", "┬", "┐"), build_row(headers), border("├", "┼", "┤")]
    for idx, row in enumerate(rows):
        lines.append(build_row(row))
        # Separator between songs (but not after the last one).
        if idx < len(rows) - 1:
            lines.append(border("├", "┼", "┤"))
    lines.append(border("└", "┴", "┘"))
    return "\n".join(lines)


if __name__ == "__main__":
    main()
