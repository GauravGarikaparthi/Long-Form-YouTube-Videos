# Long-Form AI Video Engine

Fully automated pipeline: takes a text topic → writes a high-CTR script → generates
a voiceover → creates AI-generated visuals → animates scenes → assembles a
long-form video → packages everything with AI-generated metadata as a downloadable
GitHub Actions artifact.

YouTube upload is **not** automated — the pipeline ends at final video assembly.
The GitHub Actions workflow packages the MP4, AI-generated metadata (title, description,
tags, thumbnail), and logs as downloadable run artifacts for manual publishing.

## How it works

### Long-Form Pipeline (orchestrator.py)

```
Stage 1: Script Expansion & Visual Scene Breakdown
  Input: raw topic -> LLM API (Gemini / Claude / Groq) -> structured JSON script
  Output: title, hook, description, tags, thumbnail prompt, voiceover text,
          image prompts, animation parameters per scene

Stage 2: Voiceover Generation
  Input: script sections -> TTS (Kokoro / Piper / Edge-TTS / ElevenLabs) -> WAV narration

Stage 3: Asset & Image Generation
  Input: structured visual prompts -> Image API (Flux via Replicate / Together AI) -> high-res base frames
  (Parallel: all scenes generated concurrently)

Stage 4: Image-to-Video Animation & Extension
  Input: base frames + motion params -> Video API -> animated video segments
  (Parallel: all scenes animated concurrently)

Stage 5: Video Assembly & Production
  Input: video segments + narration -> MoviePy / FFmpeg -> final compiled MP4

Stage 6: Metadata & Thumbnail Packaging
  Input: script metadata -> LLM refinement + AI image gen -> metadata.json + thumbnail.png
```

### Shorts Pipeline (main.py + src/)

```
trend_fetch.py       -> picks a trending topic (Google Trends, with fallback list)
generate_script.py   -> Groq writes title/description/tags/narration/keywords
generate_voiceover.py -> Kokoro (local TTS; Piper fallback) turns narration into a WAV
fetch_visuals.py      -> Pexels / Pixabay / Mixkit downloads matching stock clips
generate_illustrations.py -> Pollinations.ai generates AI illustration clips
assemble_video.py     -> ffmpeg stitches clips + voiceover + title card + captions
generate_thumbnail.py -> Pillow makes a 1280x720 thumbnail from a video frame
main.py               -> runs all of the above in order, then packages metadata
```

## Setup

### GitHub Actions Secrets

Add these under **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Used For | Required If |
|--------|----------|-------------|
| `GEMINI_API_KEY` | Script expansion (LLM) | `LLM_PROVIDER=gemini` |
| `ANTHROPIC_API_KEY` | Script expansion (LLM) | `LLM_PROVIDER=claude` |
| `GROQ_API_KEY` | Script expansion (LLM) | `LLM_PROVIDER=groq` |
| `ELEVENLABS_API_KEY` | Voiceover (TTS) | `TTS_PROVIDER=elevenlabs` |
| `ELEVENLABS_VOICE_ID` | Voiceover voice selection | `TTS_PROVIDER=elevenlabs` |
| `REPLICATE_API_TOKEN` | Image gen + Video gen | `IMAGE_GEN_PROVIDER=replicate_flux` or `VIDEO_GEN_PROVIDER=replicate` |
| `TOGETHER_API_KEY` | Image gen + Video gen | `IMAGE_GEN_PROVIDER=together_flux` or `VIDEO_GEN_PROVIDER=together` |
| `HUGGINGFACE_API_KEY` | Video gen (fallback) | `VIDEO_GEN_PROVIDER=huggingface` |
| `PEXELS_API_KEY` | Stock footage (Shorts pipeline) | `VISUAL_STYLE=pexels` |
| `PIXABAY_API_KEY` | Stock footage fallback (Shorts pipeline) | optional |

### Environment Variables

These can be set in the workflow YAML or as repository-level `Settings → Variables`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `gemini` | LLM for script generation |
| `TTS_PROVIDER` | `kokoro` | TTS provider: kokoro \| piper \| elevenlabs \| edge_tts |
| `KOKORO_VOICE` | `am_adam` | Kokoro voice ID (only for `TTS_PROVIDER=kokoro`) |
| `PIPER_VOICE` | `en_US-amy-low` | Piper voice model (only for `TTS_PROVIDER=piper`) |
| `IMAGE_GEN_PROVIDER` | `replicate_flux` | Image generator |
| `VIDEO_GEN_PROVIDER` | `replicate` | Video/animation provider |
| `TARGET_DURATION_SECONDS` | `180` | Desired final video length |
| `RESOLUTION` | `1920x1080` | Output resolution |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

### Local Run (Long-Form Pipeline)

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...
export REPLICATE_API_TOKEN=...
python orchestrator.py
```

Outputs are written to `output/`:
- `final_video.mp4` — the assembled video
- `metadata.json` — AI-generated title, description, tags, thumbnail
- `thumbnail.png` — high-CTR thumbnail image

### Local Run (Shorts Pipeline)

```bash
pip install -r requirements.txt
# also install ffmpeg locally (brew install ffmpeg / apt install ffmpeg)
export GROQ_API_KEY=...
export PEXELS_API_KEY=...
python main.py
```

## GitHub Actions

- **Long-Form**: Go to **Actions** tab → *Generate Long-Form AI Video* → *Run workflow*,
  set your topic and provider options, then run. The output is a downloadable artifact
  containing the MP4, metadata JSON, and thumbnail.
- **Daily Shorts**: The `daily_video.yml` workflow runs on a schedule.

## Error Handling & Retries

- All external API calls use **exponential backoff** with up to 5 retries on 429 / 5xx / timeout.
- Pipeline stages use `asyncio.gather` for parallel asset generation where possible.
- Failed runs produce diagnostic artifacts uploaded to the Actions run.
- Secrets are never logged; only provider names and error categories appear in logs.

## Notes

- **FFmpeg Tuning**: All video encoding uses `threads=0` (all cores) and a fast
  preset (`veryfast` for libx264) to prevent GitHub runner timeouts on long-form content.
  Hardware acceleration (VideoToolbox on macOS, NVENC on NVIDIA) is auto-detected.
- **Model Caching**: Kokoro and Piper TTS model weights are cached via GitHub Actions
  cache, minimizing cold-start latency on every run.
- **Outputs**: Final video, metadata JSON, and thumbnail are uploaded as Action
  artifacts — no automated YouTube upload.
- **Costs**: All providers have free tiers; check rate limits if running on schedule.
