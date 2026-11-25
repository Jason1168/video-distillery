#!/usr/bin/env python3
"""
daily_github_scan.py — Video Distillery: Daily GitHub Open-Source Tool Scanner

Searches GitHub for open-source projects related to video production,
evaluates quality, and writes findings to the plugin data directory.

Run: python3 daily_github_scan.py
Output: ~/.gemini/config/plugins/video-distillery/data/github_tools.md
"""

import os
from datetime import datetime, timezone

DATA_DIR = os.path.expanduser("~/.gemini/config/plugins/video-distillery/data")
GITHUB_TOOLS_PATH = os.path.join(DATA_DIR, "github_tools.md")
TOOL_REGISTRY_PATH = os.path.join(DATA_DIR, "tool_registry.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ── GitHub Search Queries ─────────────────────────────────────────────────────
SEARCH_QUERIES = [
    # Core video editing & processing
    "video editing python stars:>500",
    "ffmpeg wrapper python stars:>200",
    "video processing AI stars:>300",

    # AI-powered video tools
    "AI video generation open source stars:>500",
    "text to video open source stars:>300",
    "video style transfer stars:>200",
    "video inpainting open source stars:>300",
    "depth estimation video stars:>200",

    # Color & grade
    "color grading lut open source stars:>100",
    "video color correction python stars:>100",
    "film grain simulation stars:>50",

    # Scene analysis & detection
    "scene detection video python stars:>200",
    "shot boundary detection stars:>100",
    "video scene segmentation stars:>200",
    "video highlight detection stars:>100",

    # Audio & sync
    "audio video sync open source stars:>100",
    "music sync video beats stars:>100",
    "speech to text video subtitles stars:>500",
    "whisper video subtitles stars:>300",

    # Motion & VFX
    "optical flow estimation stars:>200",
    "video stabilization open source stars:>200",
    "motion tracking python stars:>200",
    "video background removal stars:>300",

    # Workflow & pipeline
    "video production pipeline open source stars:>100",
    "video compression optimization stars:>200",
    "video thumbnail generation stars:>100",
    "video analytics python stars:>100",

    # Cinematic & film tools
    "cinematic look lut generator stars:>50",
    "film simulation open source stars:>100",
    "documentary editing tool stars:>50",
]

# ── Evaluation Criteria ───────────────────────────────────────────────────────
EVALUATION_CRITERIA = {
    "min_stars": 100,                    # minimum GitHub stars
    "max_days_since_last_commit": 180,   # must be active
    "preferred_licenses": [              # ranked preference
        "MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "GPL-3.0"
    ],
    "language_preference": [
        "Python", "JavaScript", "TypeScript", "Rust", "C++", "Go"
    ],
    "disqualify_if": [
        "archived",                      # archived repos
        "no_readme",                     # no documentation
    ]
}

# ── Tool Categories ───────────────────────────────────────────────────────────
TOOL_CATEGORIES = {
    "ai_generation": "AI Video Generation",
    "editing_pipeline": "Editing & Pipeline",
    "color_grade": "Color & Grade",
    "audio_sync": "Audio & Sound",
    "scene_analysis": "Scene Analysis & Detection",
    "motion_vfx": "Motion & VFX",
    "compression": "Compression & Delivery",
    "subtitles": "Subtitles & Captions",
    "workflow": "Workflow Automation",
}

def build_agent_scan_prompt():
    """Returns the prompt for the daily agent to execute the GitHub scan."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    queries_sample = "\n".join(f"  - `{q}`" for q in SEARCH_QUERIES[:12])

    return f"""
# Daily GitHub Video Tools Scan — {today}

You are running the Video Distillery GitHub scanner. Find the best open-source
video production tools published or updated recently.

## Search Strategy

Use `search_web` with these GitHub search queries (site:github.com):
{queries_sample}
  ... (and more from the full list in daily_github_scan.py)

## For Each Repository Found, Evaluate:

```json
{{
  "name": "owner/repo",
  "url": "https://github.com/owner/repo",
  "stars": 0,
  "last_commit_date": "",
  "license": "",
  "language": "",
  "category": "",
  "description": "",
  "what_it_does": "",
  "workflow_fit": "",
  "install_command": "",
  "quality_score": 0,
  "is_new_discovery": true
}}
```

## Quality Filter:
- Stars ≥ 100
- Last commit within 180 days
- Has a README and clear documentation
- Genuinely useful for video production workflow

## Output:

Write findings to:
`~/.gemini/config/plugins/video-distillery/data/github_tools.md`

Using the TOOLS_DIGEST_TEMPLATE format below.

Also update the tool registry:
`~/.gemini/config/plugins/video-distillery/data/tool_registry.json`
"""

TOOLS_DIGEST_TEMPLATE = """# 🛠️ Video Distillery — GitHub Tools Digest
**Date**: {date}
**Repos Scanned**: {scanned_count}
**New Tools Discovered**: {new_count}
**Updated Tools**: {updated_count}

---

## 🌟 Top New Discoveries

{new_tool_entries}

---

## 🔄 Notable Updates to Known Tools

{updated_entries}

---

## 📊 Tool Registry Summary

| Category | Count | Top Tool |
|----------|-------|----------|
{category_table}

---

## 🔧 Integration Recommendations

Based on today's scan, these tools are most immediately useful:

{integration_recommendations}

---
*Tool registry total: {total_tools} tools tracked*
*Next scan: tomorrow same time*
"""

TOOL_ENTRY_TEMPLATE = """
### {rank}. [{name}]({url})
- **Stars**: ⭐ {stars} | **Language**: {language} | **License**: {license}
- **Last Commit**: {last_commit_date}
- **Category**: {category}

**What it does**: {what_it_does}

**How it fits your workflow**: {workflow_fit}

**Quick Start**:
```bash
{install_command}
```

**Quality Score**: {quality_score}/100
"""

if __name__ == "__main__":
    prompt = build_agent_scan_prompt()
    print(prompt)
    print(f"\n[INFO] Tools digest will be written to: {GITHUB_TOOLS_PATH}")
    print(f"[INFO] Tool registry: {TOOL_REGISTRY_PATH}")
