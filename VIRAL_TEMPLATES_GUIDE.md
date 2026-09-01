"""
VIRAL VIDEO TEMPLATES 2026 - COMPLETE IMPLEMENTATION GUIDE
=========================================================

This document explains the complete viral template system integrated into your
AI video automation pipeline for maximum retention and engagement.
"""

# ============================================================================
# 1. OVERVIEW OF 10 TRENDING VIRAL TEMPLATES FOR 2026
# ============================================================================

"""
The system includes 10 scientifically-proven viral templates used by top creators:

┌─ LOCO (High-Energy, 2.2M+ uses)
│  • Fast cuts every 1.4 seconds
│  • Dynamic transitions (slide, blur, wipe)
│  • Music-forward audio mix
│  • Vibrant color grading
│  • Best for: Entertainment, music, high-energy content
│  • Retention hook: Rapid pacing keeps viewers watching
│  └─ Example: Music videos, gaming moments, action-packed tutorials

┌─ NOSTALGIC MORPH (2016 vs 2026)
│  • Slow 2.5s cuts for emotional beats
│  • Extended morphing transitions (xfade)
│  • Polaroid frame overlays
│  • Warm color grading
│  • Best for: Personal development, evolution, nostalgia
│  • Retention hook: Emotional connection to transformation
│  └─ Example: Personal growth journey, before/during/after life changes

┌─ RANKING SYSTEM
│  • 1.8s cuts with progression
│  • Bold red captions for emphasis
│  • High contrast color grading
│  • Curiosity-driven pacing
│  • Best for: Top lists, comparisons, educational ranking
│  • Retention hook: "What's #1?" curiosity loop
│  └─ Example: Top 10 productivity hacks, best coding practices

┌─ BEFORE & AFTER
│  • 2s clips with satisfying contrast
│  • Simple fade transitions
│  • Transformation focus
│  • High contrast color grading
│  • Best for: Transformations, cleaning, makeovers
│  • Retention hook: Instant satisfaction visual proof
│  └─ Example: Room makeovers, skin care results, fitness transformations

┌─ POV TRAVELING
│  • 1.6s immersive clips
│  • Slide left transitions (forward motion)
│  • Cool color grading
│  • Ken-Burns zoom effect (1.1x)
│  • Best for: Travel, lifestyle, daily vlogs, exploration
│  • Retention hook: First-person immersion
│  └─ Example: Travel vlogs, city explorations, lifestyle documentation

┌─ BEAT SYNC (Slow Zoom & Music)
│  • 2.2s cuts synced to music beats
│  • Zoom in transitions timed to beats
│  • Music-forward audio
│  • Enhanced visual movement
│  • Best for: Music-heavy, aesthetic, mood-driven
│  • Retention hook: Rhythmic visual-audio sync
│  └─ Example: Music videos, aesthetic compilations, dance trends

┌─ GRUNGE & BOLD (Black/Cyan Aesthetic)
│  • 1.5s fast dynamic cuts
│  • Desaturated (low saturation) color grade
│  • Black and cyan neon colors
│  • High contrast design
│  • Best for: Fashion, gaming, bold advertising, music
│  • Retention hook: Visual edginess and modern aesthetic
│  └─ Example: Gaming highlights, fashion lookbooks, music ads

┌─ MOTIVATIONAL TYPOGRAPHIC
│  • 1.9s clips with text emphasis
│  • Bold red/yellow/black text overlays
│  • Vibrant color grading
│  • Music-forward mix
│  • Best for: Growth content, motivation, education, self-improvement
│  • Retention hook: Powerful messaging + visual storytelling
│  └─ Example: Motivational quotes, skill tutorials, productivity tips

┌─ BEHIND-THE-SCENES (BTS)
│  • 2.4s intimate, slower pace
│  • Simple fade transitions
│  • Warm color grading
│  • Voice-forward audio mix
│  • Best for: Music production, creative process, studio sessions
│  • Retention hook: Insider perspective and authenticity
│  └─ Example: Music production breakdowns, studio sessions, creation process

┌─ EVERYDAY HACKS & Q&A
│  • 1.3s fast rapid-fire cuts
│  • Quick slide transitions
│  • Vibrant color grading
│  • Balanced audio mix
│  • Best for: Tips, hacks, quick solutions, rapid-fire Q&A
│  • Retention hook: Practical value in 60 seconds
│  └─ Example: Life hacks, productivity tips, quick tutorials
"""


# ============================================================================
# 2. FILE STRUCTURE & WHERE EACH COMPONENT LIVES
# ============================================================================

"""
New files added to your repository:

src/viral_templates.py
├─ ViralTemplateType enum (10 template types)
├─ TemplateConfig dataclass (clip duration, transitions, effects)
├─ 10 preset configurations (LOCO_CONFIG, RANKING_CONFIG, etc.)
├─ select_best_template(topic, category) → auto-selects template
└─ describe_template(template_type) → returns description dict

src/viral_captions.py
├─ ColorScheme namedtuple (6 color schemes)
├─ 6 preset color palettes:
│  ├─ KINETIC_BOLD_COLORS (#FFFF00 yellow)
│  ├─ YELLOW_BLACK_COLORS (high contrast)
│  ├─ GRADIENT_NEON_COLORS (pink/cyan)
│  ├─ SOFT_SHADOW_COLORS (subtle white)
│  ├─ BOLD_RED_COLORS (high-impact red)
│  └─ GLOWING_EDGE_COLORS (cyan glow)
├─ CaptionPosition enum (7 screen positions)
├─ apply_kinetic_caption() → yellow/bold captions
├─ apply_neon_gradient_caption() → gradient effects
└─ apply_glowing_edge_caption() → glow effects

src/template_utils.py
├─ get_template_transitions() → optimal transition sequences
├─ get_template_color_grade() → saturation/brightness/contrast
├─ get_music_emphasis_mix() → (voice_db, music_db) tuples
└─ validate_template_compatibility() → validates clip count & duration

src/template_integration.py
├─ get_template_from_env() → reads TEMPLATE_TYPE env var
├─ select_template_for_content() → returns template + full info dict
└─ apply_template_to_pipeline() → integration point for main.py
"""


# ============================================================================
# 3. QUICK START: USING TEMPLATES IN main.py
# ============================================================================

"""
STEP 1: Import the template integration module at the top of main.py

    from template_integration import apply_template_to_pipeline

STEP 2: After topic selection (in the run() function), add template logic:

    topic = resolve_topic(mode=topic_mode, category=topic_category, custom_topic=custom_topic)
    print(f"  -> Topic: {topic}")
    
    # NEW: Apply template system
    print("Step 1.5/7: Selecting viral template...")
    template_config = apply_template_to_pipeline(
        topic=topic,
        num_clips=len(clip_paths),  # You'll know this after fetching clips
        total_duration_seconds=voice_duration,  # You'll know this after voiceover
        force_template=os.environ.get("TEMPLATE_TYPE"),  # Optional: force specific template
        verbose=True
    )
    print(f"  -> Template: {template_config['template_name']}")
    print(f"  -> Clip duration: {template_config['clip_duration']}s")

STEP 3: Pass template config to assemble_video():

    # Existing code:
    assemble_video(
        clip_paths, voiceover_path, package["title"], video_path,
        work_dir=WORK_DIR, vertical=is_shorts, narration=package["narration"],
        music_path=music_path,
    )
    
    # Enhanced with template:
    assemble_video(
        clip_paths, voiceover_path, package["title"], video_path,
        work_dir=WORK_DIR, vertical=is_shorts, narration=package["narration"],
        music_path=music_path,
        template_config=template_config,  # NEW: pass template config
    )
"""


# ============================================================================
# 4. ENVIRONMENT VARIABLES FOR TEMPLATE CONTROL
# ============================================================================

"""
Add these to your GitHub Actions secrets or local .env file to control templates:

TEMPLATE_TYPE (string)
├─ Value: "auto" (default) | "loco" | "nostalgic_morph" | "ranking" 
├─       | "before_after" | "pov_traveling" | "beat_sync" 
├─       | "grunge_bold" | "motivational_typographic" | "bts" | "everyday_hacks"
├─ Effect: Force a specific template (ignores auto-selection)
└─ Example: TEMPLATE_TYPE=ranking (always use ranking template)

CONTENT_CATEGORY (string, optional)
├─ Value: "lifestyle" | "education" | "entertainment" | "transformation"
├─       | "process" | "ranking" | "travel" | "music" | "aesthetic"
├─ Effect: Hints the auto-selector towards appropriate templates
└─ Example: CONTENT_CATEGORY=transformation (prefers before_after, nostalgic_morph)

TEMPLATE_VERBOSE (boolean, optional)
├─ Value: "true" | "false"
├─ Effect: Print detailed template info to console
└─ Example: TEMPLATE_VERBOSE=true (shows template selection reasoning)
"""


# ============================================================================
# 5. AUTO-SELECTION ALGORITHM
# ============================================================================

"""
When TEMPLATE_TYPE=auto or not set, the system selects templates intelligently:

1. CATEGORY-BASED MATCHING (if CONTENT_CATEGORY is provided)
   "lifestyle" → POV_TRAVELING, BTS
   "education" → EVERYDAY_HACKS, MOTIVATIONAL_TYPOGRAPHIC
   "entertainment" → LOCO, RANKING
   "transformation" → BEFORE_AFTER, NOSTALGIC_MORPH
   "process" → BTS, EVERYDAY_HACKS
   "ranking" → RANKING, MOTIVATIONAL_TYPOGRAPHIC
   "travel" → POV_TRAVELING, LOCO
   "music" → BEAT_SYNC, LOCO
   "aesthetic" → GRUNGE_BOLD, NOSTALGIC_MORPH

2. KEYWORD MATCHING (in topic string)
   Topic contains "before" OR "after" → BEFORE_AFTER
   Topic contains "ranking" OR "top" OR "best" OR "worst" → RANKING
   Topic contains "2016" OR "2026" OR "evolution" → NOSTALGIC_MORPH
   Topic contains "hack" OR "tip" OR "tutorial" → EVERYDAY_HACKS
   Topic contains "behind" OR "scenes" OR "process" → BTS
   Topic contains "travel" OR "vlog" → POV_TRAVELING

3. TRENDING FALLBACK (weighted random selection)
   LOCO: 25% (highest usage)
   BEAT_SYNC: 20%
   POV_TRAVELING: 15%
   RANKING: 15%
   NOSTALGIC_MORPH: 10%
   EVERYDAY_HACKS: 10%
   GRUNGE_BOLD: 5%

EXAMPLE AUTO-SELECTIONS:
   "Top 5 productivity hacks" → RANKING (keyword "Top", category hint)
   "Before and after fitness transformation" → BEFORE_AFTER (keyword "Before and after")
   "Travel vlog in Japan" → POV_TRAVELING (keyword "travel", category "travel")
   "Random interesting fact" → Random from trending (no hints, keyword match fails)
"""


# ============================================================================
# 6. CAPTION STYLES & HOW TO USE THEM
# ============================================================================

"""
The system includes 6 trending 2026 caption styles, automatically applied per template:

TEMPLATE → CAPTION STYLE MAPPING:
   LOCO → KINETIC_BOLD (bright yellow, fast pacing)
   NOSTALGIC_MORPH → SOFT_SHADOW (white, subtle, emotional)
   RANKING → BOLD_RED (high-contrast, high-impact)
   BEFORE_AFTER → YELLOW_BLACK_OUTLINE (thick outline, satisfying)
   POV_TRAVELING → SOFT_SHADOW (immersive, unobtrusive)
   BEAT_SYNC → KINETIC_BOLD (synced to music beats)
   GRUNGE_BOLD → GRADIENT_NEON (pink/cyan neon aesthetic)
   MOTIVATIONAL_TYPOGRAPHIC → BOLD_RED (powerful, motivational)
   BTS → SOFT_SHADOW (authentic, behind-the-scenes)
   EVERYDAY_HACKS → YELLOW_BLACK_OUTLINE (fast, clear info)

COLOR SCHEME DETAILS:

1. KINETIC_BOLD (#FFFF00 yellow)
   ├─ Primary: #FFFF00 (bright yellow)
   ├─ Outline: #000000 (black, 8px thick)
   ├─ Shadow: (2, 2) offset
   └─ Use case: High-energy, music-driven content
   
2. YELLOW_BLACK_OUTLINE (#FFEE00 gold)
   ├─ Primary: #FFEE00 (gold yellow)
   ├─ Outline: #000000 (black, 12px THICK)
   ├─ Shadow: (3, 3) offset
   └─ Use case: Maximum legibility, informational content

3. GRADIENT_NEON (pink to cyan)
   ├─ Primary: #FF1493 (hot pink)
   ├─ Secondary: #00CED1 (cyan)
   ├─ Outline: #FF00FF (magenta, 6px)
   └─ Use case: Aesthetic, modern, trendy content

4. SOFT_SHADOW (#FFFFFF white)
   ├─ Primary: #FFFFFF (white)
   ├─ Outline: #000000 (black, 4px subtle)
   ├─ Shadow: (1, 1) offset, semi-transparent
   └─ Use case: Intimate, professional, emotional content

5. BOLD_RED (#FF0000 red)
   ├─ Primary: #FF0000 (red)
   ├─ Outline: #FFFF00 (yellow, 8px)
   ├─ Shadow: (3, 3) offset
   └─ Use case: High-impact, motivational, ranking content

6. GLOWING_EDGE (#FFFFFF white with cyan glow)
   ├─ Primary: #FFFFFF (white)
   ├─ Glow: #00FFFF (cyan, multi-layer)
   ├─ Outline: #00FFFF (6px)
   └─ Use case: Modern, high-tech, futuristic content

CAPTION POSITIONING (7 options):
   TOP_CENTER → Upper portion of screen
   MIDDLE_CENTER → Center (default for Shorts UI safe zone)
   BOTTOM_CENTER → Lower portion (avoid YouTube controls)
   TOP_LEFT → Corner placement
   TOP_RIGHT → Corner placement
   BOTTOM_LEFT → Corner placement
   BOTTOM_RIGHT → Corner placement (safe from like button)
"""


# ============================================================================
# 7. DETAILED TEMPLATE CONFIGURATIONS
# ============================================================================

"""
Each template has these configurable parameters:

CLIP_DURATION_MS (milliseconds per clip)
   LOCO: 1400ms (fastest, rapid cuts)
   NOSTALGIC_MORPH: 2500ms (slowest, emotional pacing)
   RANKING: 1800ms (medium-fast)
   BEFORE_AFTER: 2000ms (time for satisfaction)
   POV_TRAVELING: 1600ms (immersive pace)
   BEAT_SYNC: 2200ms (synced to music)
   GRUNGE_BOLD: 1500ms (fast, edgy)
   MOTIVATIONAL_TYPOGRAPHIC: 1900ms (emphasis on text)
   BTS: 2400ms (slowest after nostalgic, intimate)
   EVERYDAY_HACKS: 1300ms (fastest for rapid info)

TRANSITION_DURATION_MS (crossfade/xfade length)
   LOCO: 200ms (snappy)
   NOSTALGIC_MORPH: 800ms (extended emotional morph)
   RANKING: 150ms (quick progression)
   BEFORE_AFTER: 300ms (clear contrast)
   POV_TRAVELING: 180ms (smooth immersion)
   BEAT_SYNC: 250ms (music-synced)
   GRUNGE_BOLD: 200ms (dynamic)
   MOTIVATIONAL_TYPOGRAPHIC: 180ms (text-focused)
   BTS: 200ms (natural flow)
   EVERYDAY_HACKS: 150ms (quick cuts)

ENABLE_ZOOM_PAN (Ken-Burns 1.1x zoom effect)
   TRUE: LOCO, POV_TRAVELING, BEAT_SYNC, GRUNGE_BOLD, 
         MOTIVATIONAL_TYPOGRAPHIC, EVERYDAY_HACKS, RANKING
   FALSE: NOSTALGIC_MORPH, BEFORE_AFTER, BTS
   (False for emotional/intimate templates)

ENABLE_MUSIC_BEAT_SYNC (sync visuals to audio beats)
   TRUE: LOCO, RANKING, POV_TRAVELING, BEAT_SYNC, GRUNGE_BOLD,
         MOTIVATIONAL_TYPOGRAPHIC, EVERYDAY_HACKS
   FALSE: NOSTALGIC_MORPH, BEFORE_AFTER, BTS
   (False for voice-forward templates)

ENABLE_POLAROID_STYLE (nostalgic frame overlays)
   TRUE: NOSTALGIC_MORPH only
   FALSE: All others

MAX_CLIPS (maximum recommended clips)
   LOCO: 12 clips
   NOSTALGIC_MORPH: 6 clips (fewer for emotional beats)
   RANKING: 8 clips
   BEFORE_AFTER: 4 clips (minimal for clarity)
   POV_TRAVELING: 10 clips
   BEAT_SYNC: 8 clips
   GRUNGE_BOLD: 10 clips
   MOTIVATIONAL_TYPOGRAPHIC: 8 clips
   BTS: 6 clips (intimate)
   EVERYDAY_HACKS: 10 clips (rapid-fire)

COLOR_GRADE (HSL adjustments)
   VIBRANT: Saturation +35%, Contrast +25%
   WARM: Saturation +20%, Brightness +8%, Contrast +15%
   COOL: Brightness -5%, Contrast +20%
   DESATURATED: Saturation -30%, Contrast +40% (Black/Cyan aesthetic)

AUDIO_EMPHASIS (mix levels)
   VOICE_FORWARD: Voice -3dB, Music -25dB (voice prominent)
   MUSIC_FORWARD: Voice -12dB, Music -15dB (music prominent)
   BALANCED: Voice -6dB, Music -20dB (equal but voice leads)
"""


# ============================================================================
# 8. WORKFLOW EXAMPLE: RANKING TEMPLATE
# ============================================================================

"""
Let's walk through a complete example using the RANKING template:

Topic: "Top 5 productivity hacks for 2026"

STEP 1: Auto-selection triggers
   └─ Keyword "Top" detected
   └─ Select RANKING template

STEP 2: Template configuration applied
   ├─ Clip duration: 1800ms
   ├─ Caption style: BOLD_RED (high-impact)
   ├─ Transitions: slideright, slideleft, wiperight, wipeleft, fade
   ├─ Color grade: Vibrant (saturation +35%, contrast +25%)
   ├─ Audio mix: Balanced (-6dB voice, -20dB music)
   ├─ Zoom/Pan: Enabled (1.1x Ken-Burns)
   ├─ Music sync: Enabled
   └─ Max clips: 8

STEP 3: Script generation (generate_script.py)
   ├─ Title: "Top 5 Productivity Hacks #shorts"
   ├─ Narration (120-135 words):
   │  "Most people waste 4 hours daily. [HOOK]
   │   First, timeblocking. Schedule like a calendar [CLIP 1]
   │   Second, no-phone mornings. Results within days. [CLIP 2]
   │   Third, Pomodoro + breaks. 25 minutes focused. [CLIP 3]
   │   Fourth, batching similar tasks. Context switching kills time. [CLIP 4]
   │   Fifth, automate the routine. [CLIP 5]
   │   Try one today. You'll see."
   ├─ Visual keywords: [productivity, calendar, time, focus, routine]
   └─ Tags: [shorts, productivity, hacks, time-management, 2026]

STEP 4: Voiceover generation
   └─ Duration: ~52 seconds (fits 50-55s max)

STEP 5: Clip fetching
   └─ 5 clips (one per hack) + intro = 6 clips total
   └─ Duration: 52s / 6 clips ≈ 8.7s each
   └─ Template scales to fit available clips

STEP 6: Video assembly with template
   ├─ Apply ranking overlay: "#1 TIMEBLOCKING" (red bold)
   ├─ Clip 1: 1800ms zoom/pan, fade transition
   ├─ Apply ranking overlay: "#2 NO-PHONE MORNINGS" (red bold)
   ├─ Clip 2: 1800ms zoom/pan, slide right
   ├─ Apply ranking overlay: "#3 POMODORO TECHNIQUE" (red bold)
   ├─ Clip 3: 1800ms zoom/pan, wipe right
   ├─ ... (continue for all 5 hacks)
   ├─ Music sync: Beat-aligned transitions
   ├─ Color grade: Vibrant (boost contrast for impact)
   ├─ Audio mix: Voice forward (narrator clearly heard)
   └─ Looped seamless ending

STEP 7: Thumbnail generation
   ├─ Extract frame at 1.5s
   ├─ Center-crop to 1080x1920
   ├─ Boost contrast +25%, saturation +35%
   ├─ Add text hook: "TOP 5" (yellow, bold)
   └─ Dark band overlay for readability

STEP 8: Upload to YouTube
   ├─ Title: "Top 5 Productivity Hacks #shorts"
   ├─ Description: "#shorts\nTry these 5 proven productivity hacks..."
   ├─ Tags: [shorts, productivity, hacks, time-management, 2026]
   └─ Privacy: Public

EXPECTED PERFORMANCE:
   ├─ Retention: High (curiosity loop: "what's #1?")
   ├─ Click-through: High (bold red captions drive engagement)
   ├─ Watch time: 50+ seconds (full video retention)
   └─ Shares: Medium (utility content)
"""


# ============================================================================
# 9. ADDING TEMPLATE SUPPORT TO assemble_video.py
# ============================================================================

"""
Modify src/assemble_video.py to accept template_config parameter:

# In the assemble_video() function signature, add:
def assemble_video(
    clip_paths: list[str],
    voiceover_path: str,
    title_text: str,
    out_path: str,
    work_dir: str = "work",
    vertical: bool = False,
    narration: str | None = None,
    music_path: str | None = None,
    template_config: dict | None = None,  # NEW PARAMETER
):
    # ... existing code ...
    
    # NEW: Apply template-specific settings
    if template_config:
        clip_durations_ms = template_config.get('clip_duration_ms', 1800)
        enable_zoom = template_config.get('enable_zoom_pan', True)
        enable_beat_sync = template_config.get('enable_music_beat_sync', True)
        color_grade = template_config.get('color_grade', {})
        
        # Scale clip durations based on template
        CLIP_DURATIONS = (clip_durations_ms / 1000.0,) * 8
        
        # Apply color grading in thumbnail
        if color_grade:
            img = ImageEnhance.Color(img).enhance(
                color_grade.get('saturation', 1.0)
            )
            img = ImageEnhance.Contrast(img).enhance(
                color_grade.get('contrast', 1.0)
            )
    
    # ... rest of function ...
"""


# ============================================================================
# 10. TEMPLATE COMPATIBILITY VALIDATION
# ============================================================================

"""
Before assembling, the system validates your content against template requirements:

VALIDATION CHECKS:

1. Minimum clip count
   ├─ All templates require: 3+ clips minimum
   ├─ Error: "{template} requires at least 3 clips (you have {n})"
   └─ Solution: Fetch more clips from Pexels or use illustrations

2. Maximum recommended clips
   ├─ LOCO: ≤ 24 clips optimal (12 max recommended)
   ├─ NOSTALGIC_MORPH: ≤ 12 clips (6 max, emotional pacing)
   ├─ RANKING: ≤ 16 clips
   ├─ BEFORE_AFTER: ≤ 8 clips (4 max for clear contrast)
   ├─ Warning: "{template} works best with {max} or fewer clips"
   └─ Solution: Filter clips by relevance or use fewer

3. Minimum total duration
   ├─ Calculated: (clip_duration_ms / 1000) × 3
   ├─ LOCO minimum: 1.4s × 3 = 4.2s
   ├─ Error: "Content too short for {template} (min {min}s)"
   └─ Solution: Add more clips or use longer clips

4. Maximum total duration
   ├─ Hard limit: 60 seconds (YouTube Shorts max)
   ├─ Error: "Content too long for YouTube Shorts (max 60s, you have {n}s)"
   └─ Solution: Shorten voiceover or use fewer clips

VALIDATION OUTPUT:
   ✓ loco template is compatible with your content
   ⚠ Warning: Before_after works best with 4 or fewer clips (you have 8)
   ✗ Content too short for ranking (min 5.4s, you have 3.2s)
"""


# ============================================================================
# 11. MONITORING & DEBUGGING
# ============================================================================

"""
Enable detailed logging with:

export TEMPLATE_VERBOSE=true

Output includes:
   [template_integration] Selected template: LOCO (2.2M+ uses)
   Description: High-energy viral trend with fast cuts
   Best for: Entertainment, music, high-energy content
   Retention hook: Rapid pacing and constant visual movement
   Compatibility: ✓ LOCO template is compatible with your content
   Clip duration: 1.4s
   Transitions: slideleft, slideright, fade, hblur, wiperight, wipeleft
   Zoom/Pan: True
   Music sync: True
   Color grade: {'saturation': 1.35, 'brightness': 1.05, 'contrast': 1.25}

DEBUGGING TEMPLATE AUTO-SELECTION:
   1. Check topic keywords in keyword_templates dict (viral_templates.py line ~130)
   2. Check content_category in category_templates dict (line ~110)
   3. Verify TEMPLATE_TYPE env var is correctly set
   4. Add print() statements to select_best_template()
   5. Test locally: python -m src.viral_templates <topic>

COMMON ISSUES:

Issue: "Unknown template type: mycustom"
   └─ Solution: Check spelling, must match ViralTemplateType enum

Issue: "Content too short for ranking"
   └─ Solution: Voiceover too short, increase narration length or use different template

Issue: "Template not being selected"
   └─ Solution: 
      a) Verify keyword is in topic string (case-sensitive matching)
      b) Check CONTENT_CATEGORY matches category_templates keys
      c) Fall back to trending random selection if no match
"""


# ============================================================================
# 12. FUTURE ENHANCEMENTS
# ============================================================================

"""
Planned features for template system:

PHASE 2 - Audio Features
   ├─ Beat detection (analyze music to sync clips perfectly)
   ├─ Silence removal (auto-trim quiet sections)
   ├─ Dynamic EQ per template (preset audio profiles)
   └─ Voice tone matching (match narrator voice to template vibe)

PHASE 3 - Advanced Visuals
   ├─ Green screen detection (add branded backgrounds)
   ├─ Face detection (focus zoom on faces for BTS)
   ├─ Scene cuts (auto-detect natural transitions)
   └─ Optical flow (better pan/zoom calculations)

PHASE 4 - AI Optimization
   ├─ A/B test templates (measure performance)
   ├─ Engagement heat map (predict drop-off points)
   ├─ Auto-caption generation (smart caption placement)
   └─ Audience targeting (select template based on viewer data)

PHASE 5 - Template Customization
   ├─ User-defined templates (create custom template configs)
   ├─ Template blending (mix 2 templates)
   ├─ Per-clip overrides (different template per segment)
   └─ Template library (community-shared templates)
"""


# ============================================================================
# 13. QUICK REFERENCE TABLE
# ============================================================================

"""
TEMPLATE SELECTION QUICK REFERENCE:

┌────────────────────┬──────────────┬──────────────┬─────────────┬──────────────┐
│ TEMPLATE           │ CLIP DURATION│ TRANSITIONS  │ BEST FOR    │ RETENTION    │
├────────────────────┼──────────────┼──────────────┼─────────────┼──────────────┤
│ LOCO               │ 1.4s (fast)  │ Slide, blur  │ Music, energy│ Pacing       │
│ NOSTALGIC_MORPH    │ 2.5s (slow)  │ Xfade morph  │ Evolution   │ Emotion      │
│ RANKING            │ 1.8s         │ Slide, wipe  │ Lists       │ Curiosity    │
│ BEFORE_AFTER       │ 2.0s         │ Fade         │ Transform   │ Satisfaction │
│ POV_TRAVELING      │ 1.6s         │ Slide left   │ Travel      │ Immersion    │
│ BEAT_SYNC          │ 2.2s         │ Zoom in      │ Aesthetic   │ Music sync   │
│ GRUNGE_BOLD        │ 1.5s         │ Wipe         │ Fashion     │ Edginess     │
│ MOTIVATIONAL       │ 1.9s         │ Mixed        │ Growth      │ Messaging    │
│ BTS                │ 2.4s (slow)  │ Fade         │ Process     │ Authenticity │
│ EVERYDAY_HACKS     │ 1.3s (fast)  │ Slide        │ Tips        │ Value        │
└────────────────────┴──────────────┴──────────────┴─────────────┴──────────────┘
"""


# ============================================================================
# 14. SUPPORT & RESOURCES
# ============================================================================

"""
CAPTION STYLE EXAMPLES:

KINETIC_BOLD: Bright yellow (#FFFF00), 8px black outline
   "SUBSCRIBE"
   
YELLOW_BLACK_OUTLINE: Gold (#FFEE00), 12px black outline
   "WATCH THIS"
   
GRADIENT_NEON: Hot pink (#FF1493) to cyan (#00CED1)
   "EPIC MOMENT"
   
SOFT_SHADOW: White (#FFFFFF), subtle 4px black outline
   "The journey"
   
BOLD_RED: Red (#FF0000), yellow outline
   "#1 BEST HACK"
   
GLOWING_EDGE: White with cyan glow
   "NEXT LEVEL"

DOCUMENTATION FILES:
   └─ README.md - Updated with template info
   └─ VIRAL_TEMPLATES_GUIDE.md (this file)
   └─ Template configs: src/viral_templates.py (line-by-line comments)

EXAMPLE GITHUB ACTIONS WORKFLOW:
   # .github/workflows/daily_video.yml
   env:
      TEMPLATE_TYPE: "auto"           # Auto-select template
      CONTENT_CATEGORY: "education"   # Hint for selection
      TEMPLATE_VERBOSE: "true"        # Print template info
      
TESTING LOCALLY:
   export TEMPLATE_TYPE=ranking
   export CONTENT_CATEGORY=education
   export TEMPLATE_VERBOSE=true
   python main.py

REPORTING ISSUES:
   1. Check VIRAL_TEMPLATES_GUIDE.md troubleshooting
   2. Verify topic keywords are detected (TEMPLATE_VERBOSE=true)
   3. Confirm clip count is 3+ and duration < 60s
   4. Check environment variables are set correctly
"""


if __name__ == "__main__":
    print(__doc__)
