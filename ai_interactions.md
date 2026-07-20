# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I asked the agent (Claude Code) to add 5+ advanced song attributes to the dataset and make the
recommender actually score them. This was a multi-file change: it had to edit the data file, both
scoring paths in the code, and the demo profiles, then prove the changes worked.

**Prompts used:**

> Add Advanced Song Features. Introduce 5 or more complex attributes to the dataset that are not
> currently present in the baseline data, such as Song Popularity (0-100), Release Decade, or
> Detailed Mood Tags (e.g., "nostalgic," "aggressive," "euphoric"). Update both data/songs.csv and
> the scoring logic in src/recommender.py so scoring accounts for the new attributes. Document the
> agentic workflow in ai_interactions.md.

**What did the agent generate or change?**

The agent added **5 new attributes** to all 20 songs and wired each into scoring:

- `popularity` (0-100) → scored by a `popularity_pref` of "mainstream" vs "underground" (up to +1.0)
- `release_decade` (e.g. 1980, 2010, 2020) → +1.0 when it matches the user's `favorite_decade`
- `mood_tags` (detailed pipe-separated tags like `nostalgic|nocturnal`) → +0.5 per shared tag, capped at +1.5
- `language` (english / instrumental) → +1.0 on a `preferred_language` match
- `explicit` (true/false) → −2.0 penalty when the user sets `allow_explicit: False`

Files changed:

- `data/songs.csv` — added the 5 columns to the header and every row.
- `src/recommender.py` — new weight constants; a `parse_tags()` and `_popularity_points()` helper;
  new fields on the `Song` and `UserProfile` dataclasses (all with defaults); new scoring blocks
  in **both** `Recommender._score` (OOP) and `score_song` (functional); and new column parsing in
  `load_songs`.
- `src/main.py` — enriched the three demo profiles with the new preferences and added a fourth
  "Retro Synthwave Night" profile to show decade + language + tags working together.

**What did you verify or fix manually?**

- **Ran the existing tests.** `tests/test_recommender.py` builds `Song`/`UserProfile` without the
  new fields. I confirmed the agent gave every new field a default value, so the tests still pass
  (they do — both pass).
- **Ran the app** (`python -m src.main`) and read the output. The reasons lines now show the new
  bonuses (e.g. "from your favorite era (1980s) (+1.0)", "language match (instrumental) (+1.0)"),
  which confirmed the features actually reach the score and aren't just stored.
- **Checked the explicit penalty end-to-end.** With no filter, the explicit track "Gym Hero" scores
  5.00 and ranks #1. With `allow_explicit: False`, its score drops to 3.00 and a clean song
  ("Sunrise City") takes #1. That is exactly the −2.0 swing I expected.
- **One thing to watch:** the agent kept `main.py`'s scoring live, so the specific scores quoted in
  `model_card.md` (sections 6-7) are now out of date. That is expected after adding features, but
  it is a manual follow-up — the model card should be re-run and updated separately.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

<!-- e.g., Strategy, Factory, Observer, etc. -->

**How did AI help you brainstorm or implement it?**

<!-- Describe the conversation or suggestions that led to your decision -->

**How does the pattern appear in your final code?**

<!-- Point to the relevant class or method -->
