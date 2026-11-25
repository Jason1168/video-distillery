#!/usr/bin/env python3
"""
daily_video_scan.py — Video Distillery: Daily Global Video Intelligence Scanner

Scans curated high-quality video sources, distills craft patterns,
and writes a digest to the plugin data directory.

Run: python3 daily_video_scan.py
Output: ~/.gemini/config/plugins/video-distillery/data/daily_digest.md
"""

import json
import os
import sys
from datetime import datetime, timezone

DATA_DIR = os.path.expanduser("~/.gemini/config/plugins/video-distillery/data")
DIGEST_PATH = os.path.join(DATA_DIR, "daily_digest.md")
KNOWLEDGE_BASE_PATH = os.path.join(DATA_DIR, "knowledge_base.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ── Video Source Catalog ──────────────────────────────────────────────────────
VIDEO_SOURCES = {
    "vimeo_staff_picks": {
        "url": "https://vimeo.com/channels/staffpicks",
        "api": "https://api.vimeo.com/channels/staffpicks/videos?per_page=10&sort=date",
        "category": "cinematic_shorts",
        "quality_tier": "A",
    },
    "short_of_the_week": {
        "url": "https://www.shortoftheweek.com",
        "rss": "https://www.shortoftheweek.com/feed/",
        "category": "narrative_short_film",
        "quality_tier": "A",
    },
    "vimeo_documentary": {
        "url": "https://vimeo.com/categories/documentary",
        "category": "documentary",
        "quality_tier": "A",
    },
    "youtube_cinema_channels": {
        "channels": [
            "UCi7GJNg51C3jgmYTUwqoUXA",  # Every Frame a Painting
            "UCKpH0CKltc73e4wh0_pgL3g",  # Lessons from the Screenplay
            "UCErSSa3CaP_GJxmFpdjG9Jw",  # Filmmaker IQ
        ],
        "category": "craft_analysis",
        "quality_tier": "B",
    },
    "ads_of_the_world": {
        "url": "https://www.adsoftheworld.com",
        "category": "brand_film",
        "quality_tier": "A",
    },
    "nowness": {
        "url": "https://www.nowness.com",
        "category": "art_film",
        "quality_tier": "A+",
    },
}

# ── Cinematic Craft Distillation Schema ────────────────────────────────────────
CRAFT_DIMENSIONS = [
    "shot_language",        # ECU/CU/MS/WS/EWS + movements
    "editing_rhythm",       # avg shot length, cut types, pacing
    "color_grade",          # temperature, style, mood
    "narrative_structure",  # 3-act, in media res, poetic, etc.
    "sound_design",         # music genre/BPM, SFX, silence
    "emotional_journey",    # tension/release map
    "production_level",     # budget tier, crew, locations
    "director_signature",   # unique stylistic choices
]

# ── Quality Scoring Rubric ────────────────────────────────────────────────────
QUALITY_RUBRIC = {
    "narrative_clarity":    20,  # max 20 pts
    "visual_craft":         25,  # max 25 pts
    "emotional_impact":     20,  # max 20 pts
    "technical_execution":  20,  # max 20 pts
    "originality":          15,  # max 15 pts
    # Total: 100 pts. Threshold for inclusion: ≥75
}

INCLUSION_THRESHOLD = 75  # minimum quality score for digest

def build_agent_scan_prompt():
    """
    Returns a prompt the agent should use to perform the actual web scan.
    This is called by the daily automation sidecar.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""
# Daily Video Intelligence Scan — {today}

You are running the Video Distillery daily scan. Your goal: find, analyze,
and distill the highest-quality videos published or featured today/this week.

## Sources to Check (use search_web for each):

1. **Vimeo Staff Picks** — search: `site:vimeo.com staff picks {today[:7]}`
2. **Short of the Week** — search: `site:shortoftheweek.com featured {today[:7]}`
3. **Nowness** — search: `site:nowness.com new {today[:7]}`
4. **Ads of the World** — search: `site:adsoftheworld.com best {today[:7]}`
5. **YouTube Documentary** — search: `best documentary short film {today[:7]} youtube`
6. **Film Festival Online** — search: `sundance tiff tribeca online screening {today[:7]}`

## For Each Video Found, Extract:

```json
{{
  "title": "",
  "url": "",
  "director": "",
  "duration_seconds": 0,
  "quality_score": 0,
  "craft_analysis": {{
    "shot_language": "",
    "editing_rhythm": "",
    "color_grade": "",
    "narrative_structure": "",
    "sound_design": "",
    "emotional_journey": "",
    "production_level": "",
    "director_signature": ""
  }},
  "replication_difficulty": "low|medium|high",
  "key_techniques": [],
  "director_notes": ""
}}
```

## Quality Threshold: Only include videos scoring ≥75/100.

## Output Format:

Write the complete digest to:
`~/.gemini/config/plugins/video-distillery/data/daily_digest.md`

Using the template in `scripts/daily_video_scan.py` → `DIGEST_TEMPLATE`.

Also update the knowledge base:
`~/.gemini/config/plugins/video-distillery/data/knowledge_base.json`
with new craft patterns discovered today.
"""

DIGEST_TEMPLATE = """# 🎬 Video Distillery — Daily Digest
**Date**: {date}
**Videos Scanned**: {scanned_count}
**High-Quality Included**: {included_count}
**New Craft Patterns**: {pattern_count}

---

## 🏆 Top Videos Today

{video_entries}

---

## 🔬 Craft Patterns Distilled Today

### Shot Language Trends
{shot_trends}

### Narrative Structure Patterns
{narrative_trends}

### Color & Grade Trends
{color_trends}

### Sound Design Trends
{sound_trends}

---

## 📚 Knowledge Base Updates

New techniques added to the replication engine:
{kb_updates}

---

## 💡 Director's Synthesis

{directors_synthesis}

---
*Next scan scheduled: tomorrow same time*
*Knowledge base entries: {total_kb_entries}*
"""

VIDEO_ENTRY_TEMPLATE = """
### {rank}. {title}
- **Director**: {director}
- **URL**: {url}
- **Quality Score**: {quality_score}/100
- **Duration**: {duration}
- **Category**: {category}

**Craft Analysis**:
| Dimension | Analysis |
|-----------|----------|
| Shot Language | {shot_language} |
| Edit Rhythm | {editing_rhythm} |
| Color Grade | {color_grade} |
| Narrative | {narrative_structure} |
| Sound | {sound_design} |
| Emotional Arc | {emotional_journey} |

**Key Techniques to Steal**: {key_techniques}

**Director's Note**: {director_notes}

**Replication Difficulty**: {replication_difficulty}
"""

if __name__ == "__main__":
    prompt = build_agent_scan_prompt()
    print(prompt)
    print(f"\n[INFO] Digest will be written to: {DIGEST_PATH}")
    print(f"[INFO] Knowledge base: {KNOWLEDGE_BASE_PATH}")
