# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world recommenders (Spotify, YouTube, Netflix) learn from enormous amounts of
behavioral data — what millions of people play, skip, save, and replay — and blend
that with audio analysis and social signals to predict what *you* are likely to enjoy
next. They optimize for engagement and constantly update as your behavior changes. Our
version is a much smaller, transparent simulation: instead of learning from behavior, it
works purely from a stated **taste profile** and a fixed catalog of songs. It prioritizes
**content-based matching** — comparing the measurable attributes of each song to the
user's preferences — and it prioritizes being **explainable**: every recommendation comes
with a reason, so you can see exactly *why* a song was chosen rather than trusting a black box.

The system has two rules working together. A **scoring rule** measures how well a single
song fits the user (rewarding songs whose numerical features are *close* to the user's
target, not just high or low). A **ranking rule** then compares all the scores, sorts them,
and returns the top `k` songs the user actually sees.

### Features used

Each **`Song`** uses:

- `genre` — e.g. pop, lofi, rock, jazz (categorical match)
- `mood` — e.g. happy, chill, intense (categorical match)
- `energy` — how energetic the track feels (0–1)
- `tempo_bpm` — speed in beats per minute (normalized before scoring)
- `valence` — musical positivity / happiness (0–1)
- `danceability` — how suitable it is for dancing (0–1)
- `acousticness` — how acoustic vs. electronic it is (0–1)

Each **`UserProfile`** stores:

- `favorite_genre` — the genre they prefer
- `favorite_mood` — the mood they're looking for
- `target_energy` — the energy level they want (0–1), matched by *closeness*
- `likes_acoustic` — whether they lean toward acoustic tracks

### Data flow

```
Input (User Prefs + CSV) → Process (score every song) → Output (sort, take Top K)
```

1. **Input** — `load_songs()` parses `data/songs.csv` into song records; the user's taste profile is a dictionary of target values.
2. **Process (the loop)** — `score_song()` judges each song *individually* and returns `(score, reasons)`. It never looks at other songs.
3. **Output (the ranking)** — `recommend_songs()` sorts all scored songs and returns the Top `k`, each with a plain-language explanation.

This keeps the **scoring rule** (how good is one song?) separate from the **ranking rule** (which songs win?).

### Algorithm Recipe (finalized)

Each song earns points against the user's profile:

| Rule | Points | How it's computed |
|---|---|---|
| Genre match | **+2.0** | `song.genre == favorite_genre` |
| Mood match | **+1.0** | `song.mood == favorite_mood` |
| Energy closeness | **+0.0 → +2.0** | `(1 - abs(target_energy - song.energy)) * 2.0` |
| Acoustic bonus *(optional)* | **+0.5** | `likes_acoustic and song.acousticness >= 0.6` |

The energy term rewards songs that are *close* to the target — not just high or
low — so a listener wanting calm music isn't handed the most energetic track.
The final score is the sum of these points; higher is better. Weights live as
constants at the top of `src/recommender.py`, so they're easy to tune.

### Potential biases

- **Over-prioritizes genre.** At +2.0, genre is the single heaviest signal. A
  great song that nails the user's mood and energy but sits in a neighboring
  genre can lose to a mediocre same-genre track.
- **Mood is under-weighted.** At +1.0 it can be fully outweighed by the energy
  term, so "chill" requests may still surface higher-energy songs.
- **Popularity/artist blind spots.** The system has no notion of quality or
  popularity, and artists appearing more often in the catalog get more chances
  to be recommended.
- **Cold, narrow catalog.** With a tiny CSV and a single-region taste profile,
  the recommender reinforces one "taste bubble" and rarely surprises the user
  with something outside it.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Running `python3 -m src.main` with the default `pop / happy` profile produces:

```
Loaded songs: 20

============================================================
  TOP RECOMMENDATIONS
  for: genre=pop, mood=happy, energy=0.8
============================================================

1. Sunrise City — Neon Echo                      Score: 4.96
     • genre match (pop) (+2.0)
     • mood match (happy) (+1.0)
     • energy (0.82) close to target (0.80) (+2.0)

2. Gym Hero — Max Pulse                          Score: 3.74
     • genre match (pop) (+2.0)
     • energy (0.93) close to target (0.80) (+1.7)

3. Rooftop Lights — Indigo Parade                Score: 2.92
     • mood match (happy) (+1.0)
     • energy (0.76) close to target (0.80) (+1.9)

4. Groove Machine — Funkadelphia                 Score: 2.00
     • energy (0.80) close to target (0.80) (+2.0)

5. Night Drive Loop — Neon Echo                  Score: 1.90
     • energy (0.75) close to target (0.80) (+1.9)

============================================================
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



