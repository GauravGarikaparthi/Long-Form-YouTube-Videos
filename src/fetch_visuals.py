"""
Downloads stock video clips for each keyword, trying providers in this order
so one provider having no match (or a rate limit) doesn't shrink the video:
  1. Pexels (primary; PEXELS_API_KEY)
  2. Pixabay (documented Videos API at pixabay.com/api/videos/; optional
     PIXABAY_API_KEY) -- unlike Pixabay's Music library, Images and Videos
     are real, stable, documented endpoints
  3. A small, hand-curated local Mixkit folder (mixkit/<orientation>/*.mp4)
     -- Mixkit has no public API at all, so this is a manually-downloaded
fallback library, same approach as select_music.py takes for music
"""

from __future__ import annotations

import os
import random
import requests

from _sanitize import sanitize_credential

PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"
PIXABAY_SEARCH_URL = "https://pixabay.com/api/videos/"
MIXKIT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mixkit")
FALLBACK_QUERY = "cinematic b-roll"


def _target_dimension(width: int, height: int, orientation: str) -> int:
    return height if orientation == "portrait" else width


def _download(url: str, out_path: str) -> None:
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def _fetch_from_pexels(query, out_path, api_key, orientation, per_page=1) -> bool:
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": per_page, "orientation": orientation}
    resp = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    videos = resp.json().get("videos", [])
    if not videos:
        return False

    video_files = sorted(
        videos[0]["video_files"],
        key=lambda v: _target_dimension(v.get("width", 0), v.get("height", 0), orientation),
    )
    candidates = [
        v for v in video_files
        if 1000 <= _target_dimension(v.get("width", 0), v.get("height", 0), orientation) <= 1920
    ]
    chosen = candidates[0] if candidates else video_files[-1]
    _download(chosen["link"], out_path)
    return True


def _fetch_from_pixabay(query, out_path, api_key, orientation, per_page=3) -> bool:
    """
    Pixabay's Videos API has no orientation filter (unlike its Images API),
    so a hit is only accepted if one of its size variants actually matches
    the requested orientation by aspect ratio. Most Pixabay video
    contributions are landscape, so a "portrait" search legitimately
    returning nothing here is expected -- the caller moves on to Mixkit.
    """
    params = {"key": api_key, "q": query, "per_page": max(per_page, 3), "safesearch": "true"}
    resp = requests.get(PIXABAY_SEARCH_URL, params=params, timeout=30)
    resp.raise_for_status()
    hits = resp.json().get("hits", [])

    for hit in hits:
        variants = [v for v in hit.get("videos", {}).values() if v.get("width") and v.get("height")]
        if orientation == "portrait":
            variants = [v for v in variants if v["height"] > v["width"]]
        else:
            variants = [v for v in variants if v["width"] >= v["height"]]
        if not variants:
            continue
        variants.sort(key=lambda v: _target_dimension(v["width"], v["height"], orientation))
        candidates = [
            v for v in variants
            if 1000 <= _target_dimension(v["width"], v["height"], orientation) <= 1920
        ]
        chosen = candidates[0] if candidates else variants[-1]
        _download(chosen["url"], out_path)
        return True

    return False


def _fetch_from_mixkit_library(out_path, orientation) -> bool:
    """
    Reads from a small, hand-downloaded local library instead of a live API
    call (Mixkit has none). Populate mixkit/landscape/ and mixkit/portrait/
    with a handful of generic b-roll clips (city, nature, abstract motion)
    downloaded by hand from mixkit.co/free-stock-video/ -- this is a
    last-resort fallback, so exact keyword matching isn't expected here.
    """
    folder = os.path.join(MIXKIT_DIR, orientation)
    if not os.path.isdir(folder):
        return False
    clips = [f for f in os.listdir(folder) if f.lower().endswith(".mp4")]
    if not clips:
        return False
    src_path = os.path.join(folder, random.choice(clips))
    with open(src_path, "rb") as src, open(out_path, "wb") as dst:
        dst.write(src.read())
    return True


def fetch_clips(
    keywords: list[str],
    out_dir: str,
    api_key: str | None = None,
    pixabay_api_key: str | None = None,
    clips_per_keyword: int = 1,
    orientation: str = "landscape",
):
    """
    Downloads one clip per keyword into out_dir, trying Pexels -> Pixabay ->
    local Mixkit library -> a generic fallback query, in that order. Returns
    local file paths in the same order as keywords (skipping any keyword
    that fails on every provider).
    """
    pexels_key = sanitize_credential(api_key or os.environ["PEXELS_API_KEY"])
    raw_pixabay_key = pixabay_api_key or os.environ.get("PIXABAY_API_KEY", "")
    pixabay_key = sanitize_credential(raw_pixabay_key) if raw_pixabay_key.strip() else None

    os.makedirs(out_dir, exist_ok=True)
    paths = []

    for i, keyword in enumerate(keywords):
        out_path = os.path.join(out_dir, f"clip_{i:02d}.mp4")
        found = False

        for query in (keyword, FALLBACK_QUERY):
            try:
                if _fetch_from_pexels(query, out_path, pexels_key, orientation, clips_per_keyword):
                    found = True
                    break
            except requests.RequestException as e:
                print(f"[fetch_visuals] Pexels request failed for '{query}': {e}")

        if not found and pixabay_key:
            for query in (keyword, FALLBACK_QUERY):
                try:
                    if _fetch_from_pixabay(query, out_path, pixabay_key, orientation, clips_per_keyword):
                        found = True
                        break
                except requests.RequestException as e:
                    print(f"[fetch_visuals] Pixabay request failed for '{query}': {e}")

        if not found:
            found = _fetch_from_mixkit_library(out_path, orientation)
            if found:
                print(f"[fetch_visuals] Used local Mixkit fallback clip for '{keyword}'.")

        if not found:
            print(f"[fetch_visuals] No clip found for '{keyword}' on any provider, skipping.")
            continue

        paths.append(out_path)

    return paths


if __name__ == "__main__":
    result = fetch_clips(["ocean waves", "city traffic at night"], "test_clips")
    print(result)
