# MovieGrid Practice (The Reel Ledger)

A single-file, browser-based practice version of [MovieGrid.io](https://moviegrid.io)'s daily puzzle. Instead of waiting for one puzzle a day, deal a new 3×3 grid (3 actors × 3 categories) whenever you want and practice naming films that satisfy each actor/category pairing.

## How it works

- Open `index.html` directly in a browser — no build step, no server required.
- Paste a free [TMDb](https://www.themoviedb.org) API key (v3 auth) into the setup box. It's saved only in that browser's `localStorage`.
- Click **Deal a new puzzle** to get 3 random actors and 3 random categories (genre, decade, director, franchise/collection, or co-star).
- Type a film title into a cell — an autocomplete dropdown (powered by TMDb search) helps you pick the right one. Submit to check it.
- Scoring per correct cell: 50 points for a valid answer + 1–50 rarity points on a log scale of the film's TMDb vote count (obscure picks score higher). Each film can only be used once per grid.

## Getting a TMDb API key

1. Create a free account at [themoviedb.org/signup](https://www.themoviedb.org/signup).
2. Go to your profile → **Settings** → **API**.
3. Click **Create** under "Request an API Key," choose **Developer**, and fill in the short form (any personal/non-commercial description works).
4. Copy the **API Key (v3 auth)** string and paste it into the app.

## Notes / known limitations

- Data comes from TMDb, not IMDb — TMDb has no direct IMDb review-count equivalent, so rarity is based on TMDb's own vote count.
- The actor pool (~200 names) and category pool (genres, decades, directors, franchises) are hardcoded near the top of the `<script>` in `index.html` — edit the `ACTORS`, `DIRECTORS`, and `COLLECTIONS` arrays to tune who/what shows up.
- Franchise/collection matching is a loose string match against TMDb's `belongs_to_collection` field and can occasionally miss films TMDb doesn't tag into a collection.
- No award-based categories (e.g. Oscar nominations) since TMDb doesn't track those — would need a separate static dataset to add them.
