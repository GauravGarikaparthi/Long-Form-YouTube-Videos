"""
Picks a background-music track for the video from a small, hand-curated,
locally-committed folder of royalty-free tracks (music/*.mp3 at the repo
root) -- not a live API call. This is deliberate: Pixabay's documented API
(pixabay.com/api/docs) only covers Images and Videos, not Music, so there's
no stable API contract to build an automated fetch on top of. Downloading a
handful of tracks once, by hand, and committing them keeps every run
offline-safe and removes any dependency on a third-party audio API staying
up or rate-limiting a job that runs 6x/day.

One-time setup:
  1. Go to https://pixabay.com/music/ (free account; per Pixabay's Content
     License/FAQ, no attribution is required for commercial use)
  2. Pick 6-10 instrumental tracks that suit your niche -- for
     facts/motivation content, understated mid-tempo, non-vocal beds work
     best (vocals compete with narration for attention)
  3. Download each as .mp3 into a `music/` folder at the repo root
  4. Commit them -- a few MB each, and it keeps audio fully network-free

Rotation: a track is chosen at random per run, but the same track is never
picked twice in a row across consecutive scheduled runs (tracked via a
small state file), so a 6x/day schedule doesn't repeat a bed back-to-back.
"""

from __future__ import annotations

import json
import os
import random

MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "music")
STATE_FILE = os.path.join(MUSIC_DIR, ".last_used.json")


def pick_track() -> str | None:
    """Returns a random track path from music/, avoiding an immediate repeat
    of the last one used. Returns None if the folder is empty or missing --
    callers should treat that as "no background music" rather than fail."""
    if not os.path.isdir(MUSIC_DIR):
        print("[select_music] No music/ folder found -- skipping background music.")
        return None

    tracks = [
        os.path.join(MUSIC_DIR, f)
        for f in sorted(os.listdir(MUSIC_DIR))
        if f.lower().endswith((".mp3", ".wav", ".m4a"))
    ]
    if not tracks:
        print("[select_music] No tracks in music/ -- skipping background music.")
        return None

    last_used = None
    try:
        with open(STATE_FILE) as f:
            last_used = json.load(f).get("last_track")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    candidates = [t for t in tracks if t != last_used] or tracks
    chosen = random.choice(candidates)

    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"last_track": chosen}, f)
    except OSError as e:
        print(f"[select_music] Couldn't persist rotation state ({e}) -- non-fatal.")

    return chosen


if __name__ == "__main__":
    print(pick_track())
