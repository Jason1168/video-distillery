#!/usr/bin/env python3
"""
replicate_reference.py — Video Distillery: Reference Video Replication Engine

Given a reference video (URL or description), generates a full Production Bible
to replicate it at ≥80% quality with director-level creative upgrades.

Usage (called by the agent, not directly):
  The agent reads this file to understand the replication framework,
  then applies it step-by-step when the user provides a reference clip.
"""

import os
from datetime import datetime, timezone

DATA_DIR = os.path.expanduser("~/.gemini/config/plugins/video-distillery/data")
KB_PATH = os.path.join(DATA_DIR, "knowledge_base.json")

# ── Cinematic Deconstruction Framework ───────────────────────────────────────

DECONSTRUCTION_SCHEMA = {
    "metadata": {
        "title": str,
        "director": str,
        "year": int,
        "duration_seconds": int,
        "genre": str,           # brand_film / narrative_short / documentary / art_film / music_video
        "budget_tier": str,     # micro(<10k) / low(10k-100k) / mid(100k-1M) / high(>1M)
        "reference_url": str,
    },
    "narrative": {
        "structure_type": str,  # 3-act / in_media_res / poetic / episodic / problem-solution
        "logline": str,
        "act_breakdown": list,  # [{act, timecode_start, timecode_end, description}]
        "protagonist": str,
        "central_conflict": str,
        "resolution": str,
        "subtext": str,
        "visual_metaphors": list,
    },
    "shot_language": {
        "dominant_shot_sizes": list,  # e.g. ["CU", "MS", "WS"]
        "camera_movements": list,     # dolly / handheld / drone / static / slider
        "avg_shot_length_sec": float,
        "focal_length_range": str,    # e.g. "24mm-85mm"
        "depth_of_field": str,        # shallow / deep / mixed
        "frame_rate": str,            # 24fps / 60fps / slow-mo percentage
        "aspect_ratio": str,          # 2.39:1 / 16:9 / 4:3
        "shot_list_sample": list,     # first 10 shots deconstructed
    },
    "editing": {
        "avg_shot_length_sec": float,
        "cut_types": list,            # hard / match-cut / j-cut / l-cut / jump-cut / dissolve
        "pacing_curve": str,          # slow-build / constant / fast-opening-slow-middle / etc.
        "rhythm_sync": str,           # music-synced / dialogue-driven / visual-driven
        "transitions_style": str,
    },
    "color_grade": {
        "overall_tone": str,          # warm / cool / neutral / high-contrast / desaturated
        "primary_palette": list,      # e.g. ["#D4A574", "#8BBCB2", "#2D2D2D"]
        "grade_style": str,           # teal-orange / moody-dark / pastel / filmic / natural
        "shadow_detail": str,         # crushed / lifted / natural
        "highlight_rolloff": str,     # harsh / gentle / filmic
        "skin_tone_treatment": str,
        "lut_reference": str,         # closest known LUT style
    },
    "sound_design": {
        "music_genre": str,
        "music_bpm": int,
        "music_role": str,            # background / lead / reactive
        "sfx_density": str,           # sparse / medium / dense / hyper-real
        "dialogue_pacing": str,
        "silence_use": str,           # never / strategic / frequent
        "audio_mix_style": str,       # clean / immersive / lo-fi / cinematic
    },
    "emotional_map": [
        # [{timecode, scene_name, emotion, intensity_0_to_10, technique_used}]
    ],
    "production_notes": {
        "lighting_setup": str,        # natural / 3-point / high-key / low-key / mixed
        "location_count": int,
        "talent_type": str,           # professional-actor / real-person / vo-only / no-talent
        "equipment_tier": str,        # phone / prosumer / cinema-camera / full-cinema
        "estimated_crew_size": int,
    },
}

# ── 80% Replication Quality Gates ─────────────────────────────────────────────

QUALITY_GATES = {
    "narrative": [
        "Same structure type implemented",
        "Emotional arc hits same beats at similar timecodes",
        "Central conflict and resolution present",
        "Visual metaphors translated or improved",
    ],
    "visual": [
        "Shot size distribution matches within ±15%",
        "Camera movement style matched",
        "Average shot length within ±20%",
        "Color grade matches overall tone and palette",
        "Depth of field treatment matches",
    ],
    "audio": [
        "Music genre and tempo within ±20 BPM",
        "SFX density level matched",
        "Silence/pause moments matched",
        "Audio mix style matched",
    ],
    "production": [
        "Lighting style matched",
        "Location aesthetic matched",
        "Talent direction matches reference energy",
    ],
}

# ── Production Bible Template ─────────────────────────────────────────────────

PRODUCTION_BIBLE_TEMPLATE = """
# 🎬 Production Bible: {project_name}
**Reference**: [{reference_title}]({reference_url})
**Director**: {director}
**Created**: {date}
**Replication Target**: ≥80% quality fidelity + creative upgrades

---

## 1. CREATIVE FOUNDATION

### Logline
{logline}

### Core DNA (extracted from reference)
- **Genre/Style**: {genre}
- **Emotional Target**: {emotional_target}
- **Visual Signature**: {visual_signature}
- **Sound Identity**: {sound_identity}

### Narrative Arc
{narrative_arc}

---

## 2. PRE-PRODUCTION CHECKLIST

### Script/Treatment
{script_treatment}

### Shot List (reference-matched)
{shot_list}

### Equipment List
{equipment_list}

### Location Brief
{location_brief}

### Casting/Talent Brief
{casting_brief}

### Music Brief
{music_brief}

---

## 3. PRODUCTION GUIDE

### Lighting Setup
{lighting_setup}

### Camera Settings
{camera_settings}

### Director's On-Set Notes
{directors_notes}

---

## 4. POST-PRODUCTION RECIPE

### Edit Structure
{edit_structure}

### Color Grade
{color_grade}

### Sound Design
{sound_design}

---

## 5. QUALITY GATES (≥80% Replication Checklist)

### Narrative Gates
{narrative_gates}

### Visual Gates
{visual_gates}

### Audio Gates
{audio_gates}

---

## 6. DIRECTOR'S CREATIVE UPGRADES

*Going beyond the reference — where we improve:*

{creative_upgrades}

---

## 7. APPENDIX: Reference Analysis

### Full Shot Breakdown
{shot_breakdown}

### Emotional Journey Map
{emotional_map}

### Color Palette
{color_palette}
"""

# ── Director Thinking Frameworks ──────────────────────────────────────────────

DIRECTOR_QUESTIONS = [
    "What is the single most important emotion the audience should feel at the end?",
    "What visual metaphor best represents the core theme?",
    "Where is the emotional peak, and what camera choice amplifies it most?",
    "What would be gained or lost by cutting 20% of the runtime?",
    "If there were no dialogue/narration, would the story still be clear?",
    "What is the first and last image — are they in conversation with each other?",
    "Where should the camera be absolutely still, and where should it move?",
    "What does the music tell us that the visuals don't?",
]

SCREENWRITER_PRINCIPLES = {
    "show_dont_tell": "Every expository line should be replaced with a visual action",
    "subtext": "Characters never say exactly what they mean when emotion is high",
    "visual_metaphor": "The physical world mirrors the internal world",
    "economy": "Every scene must serve at least two functions simultaneously",
    "escalation": "Each scene should raise the stakes or deepen our understanding",
    "contrast": "Juxtapose opposites: fast/slow, tight/wide, loud/silent",
}

if __name__ == "__main__":
    print("Video Distillery — Replication Engine")
    print("This module is used by the agent. See SKILL.md for usage.")
    print(f"\nKnowledge base path: {KB_PATH}")
    print("\nDirector Questions (apply to every project):")
    for i, q in enumerate(DIRECTOR_QUESTIONS, 1):
        print(f"  {i}. {q}")
