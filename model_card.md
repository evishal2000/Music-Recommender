# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 1.0**

It matches songs to your vibe. Give it a genre, a mood, and an energy level, and it finds songs that fit.

---

## 2. Intended Use

VibeMatch suggests songs from a small catalog. You tell it what you like. It ranks the songs and shows the top 5 with reasons.

It assumes the user knows their favorite genre, mood, and energy level. It also assumes those three things line up (for example, calm and low energy go together).

This is built for classroom exploration, not real users. It is a learning tool for studying how a simple scoring recommender behaves. It should not be used to power a real music app.

**Non-intended use:** It is not for real listeners, not for large music libraries, and not for making claims about anyone's taste. It cannot handle streaming data or learn from listening history.

---

## 3. How the Model Works

Every song gets a score. Higher scores go to the top.

The score is built from three things:

- **Genre.** If the song's genre matches your favorite, it gets +2 points.
- **Mood.** If the song's mood matches your favorite, it gets +1 point.
- **Energy.** The closer a song's energy is to your target, the more points it gets, up to +2. A perfect match gets the full +2. The opposite end gets close to 0.

We add these up. The song with the highest total wins. Each song also shows short reasons, so you can see why it ranked where it did.

Think of it like packing a bag for a trip. Genre is the biggest item, energy is about the same size, and mood is a small extra. That is why matching the genre and energy matters most.

The catalog also stores tempo, valence (happiness), danceability, and acousticness for each song. Right now the main recommender does not use these in the score. There is a separate object-based version that also gives a small +0.5 bonus for acoustic songs if you ask for it.

---

## 4. Data

The catalog has **20 songs**. It is a small, made-up dataset stored in a CSV file.

Each song has 10 fields: id, title, artist, genre, mood, energy, tempo, valence, danceability, and acousticness.

There are many genres, each with only one or two songs: pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip hop, classical, reggae, country, edm, blues, metal, folk, funk, and r&b. Moods are just as varied: happy, chill, intense, melancholy, dreamy, and more.

We did not add or remove songs. We used the starter catalog as-is.

**What's missing:** With only 20 songs, most genres appear once. There is no way to find "another song like this one" in the same style. The data also mixes energy and mood together — happy songs are always high energy, and sad songs are always low energy. So some real tastes, like "happy but calm," simply do not exist in the catalog.

---

## 5. Strengths

The system works well for clear, consistent listeners.

- **High-Energy Pop, Chill Lofi, and Deep Intense Rock** all got sensible top picks. The song we expected landed at #1 every time.
- The energy score does a good job of grouping songs. Calm requests pull calm songs. High-energy requests pull loud, fast songs.
- When two users want similar energy, genre and mood act as good tie-breakers. High-Energy Pop and Deep Intense Rock share some songs, but each still gets its own #1.
- The reasons shown for each song match the score. It is easy to see why a song ranked where it did.

In short, if a listener's genre, mood, and energy all point the same way, the results feel right.

---

## 6. Limitations and Bias

Where the system struggles or behaves unfairly.

Prompts:

- Features it does not consider
- Genres or moods that are underrepresented
- Cases where the system overfits to one preference
- Ways the scoring might unintentionally favor some users

### Discovered weakness: energy and mood are coupled, creating unreachable "dead zones"

During experiments I found that energy is strongly correlated with mood across the 20-song
catalog: every song labeled `happy` (Sunrise City at 0.82, Rooftop Lights at 0.76) is high
energy, and every `melancholy`/`romantic` song (Moonlit Sonata Drift at 0.30, Velvet Heartache
at 0.44) is low energy. Because the scorer adds genre, mood, and energy points independently,
these correlated signals reinforce each other instead of adding new information, so a user with
a cross-cutting taste — such as "happy but calm" or "energetic but sad" — has no song that can
satisfy them. The `Sad-but-Hyped` adversarial profile made this concrete: asking for a
melancholy mood at 0.95 energy returned the intense pop track "Gym Hero" as the #1 pick, because
the +1.0 mood weight is easily buried under the +2.0 genre and up to +2.0 energy points. As a
result, the system quietly favors listeners whose preferences are internally consistent (chill +
low energy, intense + high energy) and effectively ignores anyone whose emotional and energy
preferences pull in different directions.

---

## 7. Evaluation

How you checked whether the recommender behaved as expected.

Prompts:

- Which user profiles you tested
- What you looked for in the recommendations
- What surprised you
- Any simple tests or comparisons you ran

No need for numeric metrics unless you created some.

### Profiles tested

Two families of profiles were run. The three **standard profiles** in `src/main.py` represent
realistic, internally-consistent listeners:

- **High-Energy Pop** — `genre=pop, mood=happy, target_energy=0.85`
- **Chill Lofi** — `genre=lofi, mood=chill, target_energy=0.35`
- **Deep Intense Rock** — `genre=rock, mood=intense, target_energy=0.90`

A second family of seven **adversarial profiles** (documented further below) deliberately broke
the assumptions — conflicting mood/energy, out-of-range values, wrong casing, and missing fields.

I was looking for three things: (1) does the intended song land at #1, (2) does the _tail_ of
the list degrade gracefully into similar songs, and (3) do the printed explanations honestly
match the score.

**What surprised me:** the standard profiles all behaved well, but tuning turned out to matter
much less than expected — a weight-shift experiment (energy ×2, genre ÷2) changed every score
yet left all three top-5 orderings **identical**, because the intended songs already match on
energy too. The bigger surprise was how easily mood gets buried: the +1.0 mood weight loses to
genre + energy (+4.0), so a "sad but energetic" request returns an upbeat gym track. I was also
surprised that three catalog features (`tempo_bpm`, `valence`, `danceability`) are read from the
CSV but never used in scoring.

### Pairwise comparisons

Comparing the standard profiles against each other shows each preference field is doing real,
explainable work:

- **High-Energy Pop vs. Chill Lofi** — Opposite ends of the energy axis (0.85 vs 0.35) with
  opposite genres. Pop pulls high-energy, danceable tracks (Sunrise City 0.82, Gym Hero 0.93);
  Lofi pulls calm, acoustic-leaning tracks (Library Rain 0.35, Midnight Coding 0.42). The lists
  share **zero songs**, which is exactly right — these are genuinely different listeners, and the
  energy-closeness term cleanly separates the catalog's two clusters.
- **High-Energy Pop vs. Deep Intense Rock** — Both are high-energy (0.85 vs 0.90), so they
  _overlap_: Storm Runner, Gym Hero, and Sunrise City appear in both top-5s. What separates them
  is genre + mood — Pop tops out at happy pop (Sunrise City, 4.94) while Rock tops out at
  Storm Runner (4.98). This makes sense: when two users want similar energy, the genre/mood
  bonuses are the tie-breakers that personalize an otherwise-shared pool of energetic songs.
- **Chill Lofi vs. Deep Intense Rock** — The most extreme contrast (0.35 vs 0.90 energy, calm vs
  intense). No shared songs, and the fallback picks reveal the design: when Lofi runs out of lofi
  it reaches for ambient/jazz at the same low energy, while Rock reaches for edm/metal at high
  energy. Each stays inside its energy neighborhood — valid behavior that keeps the "vibe"
  consistent down the list.

A telling adversarial pair:

- **High-Energy Pop vs. Sad-but-Hyped** — Same high energy, but the mood flips from `happy` to
  `melancholy`. The output barely changes: "Gym Hero" and "Sunrise City" still lead, because the
  catalog has no high-energy sad song and mood is too weak to redirect the ranking. This confirms
  the mood signal is under-weighted — the profiles that _should_ produce different results
  produce nearly the same one.

### Adversarial / edge-case profiles

To stress-test the scoring logic, seven "adversarial" profiles were run — profiles built
to trick the scorer or expose unintended behavior (conflicting preferences, out-of-range
inputs, wrong casing, missing fields). Below is the actual terminal output for each.

**1. `Sad-but-Hyped`** — wants _melancholy_ mood but _high_ energy. Finding: mood (+1.0)
is overpowered by genre + energy (+4.0). Top pick is an _intense_ pop song — the emotional
opposite of the request.

```
============================================================
  TOP RECOMMENDATIONS — Sad-but-Hyped
  for: genre=pop, mood=melancholy, energy=0.95
============================================================

1. Gym Hero — Max Pulse                          Score: 3.96
     • genre match (pop) (+2.0)
     • energy (0.93) close to target (0.95) (+2.0)

2. Sunrise City — Neon Echo                      Score: 3.74
     • genre match (pop) (+2.0)
     • energy (0.82) close to target (0.95) (+1.7)

3. Neon Overdrive — Pulsegrid                    Score: 2.00
     • energy (0.95) close to target (0.95) (+2.0)

4. Iron Requiem — Blacktide                      Score: 1.96
     • energy (0.97) close to target (0.95) (+2.0)

5. Storm Runner — Voltline                       Score: 1.92
     • energy (0.91) close to target (0.95) (+1.9)
============================================================
```

**2. `Impossible Energy`** — `target_energy = 5.0`, outside the [0,1] range. Finding: the
energy term is never clamped, so scores go deeply **negative** (down to −6.36). A real bug.

```
============================================================
  TOP RECOMMENDATIONS — Impossible Energy
  for: genre=rock, mood=intense, energy=5.0
============================================================

1. Storm Runner — Voltline                      Score: -3.18
     • genre match (rock) (+2.0)
     • mood match (intense) (+1.0)

2. Gym Hero — Max Pulse                         Score: -5.14
     • mood match (intense) (+1.0)

3. Iron Requiem — Blacktide                     Score: -6.06
     • weak overall match

4. Neon Overdrive — Pulsegrid                   Score: -6.10
     • weak overall match

5. Sunrise City — Neon Echo                     Score: -6.36
     • weak overall match
============================================================
```

**3. `Lofi-at-Full-Blast`** — lofi genre but max energy (lofi is inherently low-energy).
Finding: genre + mood (+3.0) still wins, so the top picks are correct-genre but the _wrong_
energy — the energy request is effectively ignored for matching songs.

```
============================================================
  TOP RECOMMENDATIONS — Lofi-at-Full-Blast
  for: genre=lofi, mood=chill, energy=0.95
============================================================

1. Midnight Coding — LoRoom                      Score: 3.94
     • genre match (lofi) (+2.0)
     • mood match (chill) (+1.0)

2. Library Rain — Paper Lanterns                 Score: 3.80
     • genre match (lofi) (+2.0)
     • mood match (chill) (+1.0)

3. Focus Flow — LoRoom                           Score: 2.90
     • genre match (lofi) (+2.0)

4. Neon Overdrive — Pulsegrid                    Score: 2.00
     • energy (0.95) close to target (0.95) (+2.0)

5. Gym Hero — Max Pulse                          Score: 1.96
     • energy (0.93) close to target (0.95) (+2.0)
============================================================
```

**4. `Ghost Taste`** — genre and mood that don't exist in the catalog. Finding: graceful
degradation — ranking collapses to pure energy closeness, no crash.

```
============================================================
  TOP RECOMMENDATIONS — Ghost Taste
  for: genre=polka, mood=triumphant, energy=0.5
============================================================

1. Dusty Backroads — Hollow Pines                Score: 1.96
     • energy (0.48) close to target (0.50) (+2.0)

2. After Hours Soul — Midnight Ivory             Score: 1.96
     • energy (0.52) close to target (0.50) (+2.0)

3. Island Time — Sun Cadence                     Score: 1.90
     • energy (0.55) close to target (0.50) (+1.9)

4. Velvet Heartache — Ruby Slow                  Score: 1.88
     • energy (0.44) close to target (0.50) (+1.9)

5. Midnight Coding — LoRoom                      Score: 1.84
     • energy (0.42) close to target (0.50) (+1.8)
============================================================
```

**5. `Right-Taste-Wrong-Case`** — `"Pop"` / `"Happy"` with capital letters. Finding: exact
string matching is case-sensitive, so both genre and mood silently score 0. The user "clearly"
wants happy pop but is ranked on energy alone.

```
============================================================
  TOP RECOMMENDATIONS — Right-Taste-Wrong-Case
  for: genre=Pop, mood=Happy, energy=0.82
============================================================

1. Sunrise City — Neon Echo                      Score: 2.00
     • energy (0.82) close to target (0.82) (+2.0)

2. Groove Machine — Funkadelphia                 Score: 1.96
     • energy (0.80) close to target (0.82) (+2.0)

3. Rooftop Lights — Indigo Parade                Score: 1.88
     • energy (0.76) close to target (0.82) (+1.9)

4. Night Drive Loop — Neon Echo                  Score: 1.86
     • energy (0.75) close to target (0.82) (+1.9)

5. Storm Runner — Voltline                       Score: 1.82
     • energy (0.91) close to target (0.82) (+1.8)
============================================================
```

**6. `No Energy Opinion`** — `target_energy` omitted. Finding: the energy block is skipped
entirely, so scores reduce to genre/mood only and many songs tie at 0.00 (order then depends
on sort stability).

```
============================================================
  TOP RECOMMENDATIONS — No Energy Opinion
  for: genre=pop, mood=happy, energy=-
============================================================

1. Sunrise City — Neon Echo                      Score: 3.00
     • genre match (pop) (+2.0)
     • mood match (happy) (+1.0)

2. Gym Hero — Max Pulse                          Score: 2.00
     • genre match (pop) (+2.0)

3. Rooftop Lights — Indigo Parade                Score: 1.00
     • mood match (happy) (+1.0)

4. Midnight Coding — LoRoom                      Score: 0.00
     • weak overall match

5. Storm Runner — Voltline                       Score: 0.00
     • weak overall match
============================================================
```

**7. `Acoustic Lover (Ignored)`** — sets `likes_acoustic: True`. Finding: the functional
`recommend_songs` path **ignores this flag entirely** (only the OOP `Recommender._score`
honors it). Output is identical with or without the flag — the top acoustic-heavy pick wins
on genre + mood + energy, not on acousticness.

```
============================================================
  TOP RECOMMENDATIONS — Acoustic Lover (Ignored)
  for: genre=folk, mood=dreamy, energy=0.33
============================================================

1. Paper Boats — Willow Ffield                   Score: 5.00
     • genre match (folk) (+2.0)
     • mood match (dreamy) (+1.0)
     • energy (0.33) close to target (0.33) (+2.0)

2. Library Rain — Paper Lanterns                 Score: 1.96
     • energy (0.35) close to target (0.33) (+2.0)

3. Moonlit Sonata Drift — Clara Vale             Score: 1.94
     • energy (0.30) close to target (0.33) (+1.9)

4. Coffee Shop Stories — Slow Stereo             Score: 1.92
     • energy (0.37) close to target (0.33) (+1.9)

5. Spacewalk Thoughts — Orbit Bloom              Score: 1.90
     • energy (0.28) close to target (0.33) (+1.9)
============================================================
```

**What surprised us:** the two most serious issues are (1) mood is so cheap it gets buried
under genre + energy (`Sad-but-Hyped`), and (2) energy is never clamped, producing nonsensical
negative scores for out-of-range input (`Impossible Energy`).

---

## 8. Future Work

If we kept building this, I would change three things:

1. **Clamp and rebalance the scoring.** Right now energy is never bounded, so an out-of-range target gives negative scores. We would limit energy to 0–1 and give mood more weight, so a "sad but energetic" request is not overrun by genre and energy.
2. **Use the features we already have.** The catalog stores tempo, valence, danceability, and acousticness but the scorer ignores them. We would fold these in to catch tastes like "danceable" or "acoustic."
3. **Handle messy input.** Matching is case-sensitive, so "Pop" scores zero. We would lowercase inputs and handle missing fields, so small mistakes do not break the results.

We would also add more songs per genre so the top 5 has real variety instead of one obvious pick.

---

## 9. Personal Reflection

I learned that a recommender is only as good as the weights and data behind it. Small choices, like giving mood just +1 point, quietly shape every result.

The biggest surprise was how mood got buried. Asking for a "sad but hyped" song returned an upbeat gym track, because genre and energy drowned out the mood. I also found that the data itself has hidden bias — happy songs are always high energy, so some tastes are impossible to satisfy.

This changed how I see real music apps. When a playlist feels a little off, it is not magic going wrong. It is scoring rules and biased data making trade-offs I never used to notice.
