# The Meetup

Static website for our annual meetup of magicians from around the world.
Plain HTML/CSS/JS, no build step, ready for GitHub Pages.

## Structure

```
index.html                     Home: hero, story, Edinburgh 2026, planned events, past meetups
assets/css/style.css           All styles
assets/js/main.js              Photo slots, scroll effects, gallery lightbox
images/hero/                   hero.jpg              → hero background
images/2026-edinburgh/         edinburgh.jpg         → upcoming event photo
                               the-grimoire.jpg      → The Grimoire card
                               activity-welcome.jpg  → Welcome Evening card
                               activity-sessions.jpg → Close-up Sessions card
                               activity-city.jpg     → Exploring Edinburgh card
past/<year-city>/index.html    Gallery page for each past meetup
past/<year-city>/cover.jpg     Cover shown on the home page card
past/<year-city>/photos/       Sorted photos for that gallery
```

Any image slot shows a placeholder until a file with the matching name exists.

## Adding photos

1. Put the sorted photos for each event in `past/<year-city>/photos/`.
2. Optionally add `past/<year-city>/cover.jpg` for the home page card.
3. The gallery entries in each `past/<year-city>/index.html` are then filled in.

Tip: resize photos to about 2000px on the long side before adding them so pages stay fast.

## Local preview

```
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Deploy

GitHub → Settings → Pages → Source: *Deploy from a branch* → `main` / root.
