---
name: video-distillery
description: >-
  Use this skill when the user wants to: (1) analyze or replicate a reference video at ≥80% quality,
  (2) review today's distilled high-quality video digest or GitHub tool discoveries,
  (3) generate a director/screenwriter-level script, shot list, or storyboard,
  (4) get cinematic analysis of composition, color, pacing, or narrative structure.
  Activate for any request involving video creation, film craft, documentary storytelling,
  shot design, or replication of a reference clip's style and quality.
---

# 🎬 Video Distillery Skill

A comprehensive filmmaking intelligence system that:
1. **Daily auto-scans** the globe for high-quality videos → distills craft patterns into a knowledge base
2. **Daily scans GitHub** for open-source video tools → evaluates and integrates into the workflow
3. **Replicates reference videos** at ≥80% quality with structured production plans
4. **Applies director + screenwriter thinking** — narrative arc, shot language, pacing, emotion

---

## Directory Layout

```
~/.gemini/config/plugins/video-distillery/
├── plugin.json
├── skills/video-distillery/
│   ├── SKILL.md                    ← this file
│   ├── scripts/
│   │   ├── daily_video_scan.py     ← daily video distillation scan
│   │   ├── daily_github_scan.py    ← daily GitHub tool scan
│   │   └── replicate_reference.py ← reference video replication engine
│   └── references/
│       ├── cinematic_principles.md ← core film craft reference
│       ├── narrative_frameworks.md ← storytelling structures
│       └── tool_registry.md        ← discovered GitHub tools index
```

---

## Workflow A — Analyze & Replicate a Reference Video

When the user provides a reference video (URL, file, or description):

### Step 1: Deep Cinematic Deconstruction

Analyze the reference along these axes (read [cinematic_principles.md](./references/cinematic_principles.md)):

| Dimension | What to Extract |
|-----------|----------------|
| **Narrative Arc** | 3-act or non-linear? Inciting incident, climax, resolution |
| **Shot Language** | Shot sizes (ECU/CU/MS/WS/EWS), movements (dolly/pan/tilt/handheld/drone), angles |
| **Editing Rhythm** | Average shot length, cut types (hard/match/jump/dissolve), pacing curve |
| **Color & Tone** | Color temperature, grade style (teal-orange/muted/vivid), shadows vs highlights |
| **Sound Design** | Music genre/BPM, SFX layers, dialogue pacing, silence use |
| **Emotional Journey** | Per-scene emotion mapping, tension/release cycles |
| **Production Level** | Budget tier estimate, lighting setup, locations, crew size indicators |

### Step 2: Generate Replication Blueprint

Produce a **Production Bible** with:

```markdown
## [Project Name] — Replication Blueprint

### Core DNA (from reference)
- Genre/Style: [e.g., cinematic brand film / observational doc]
- Emotional target: [e.g., awe → intimacy → inspiration]
- Visual signature: [e.g., wide establishing + tight emotional close-ups, warm golden hour]

### Pre-Production Checklist
- [ ] Script/treatment (follows reference narrative arc)
- [ ] Shot list (mirrors reference shot language)
- [ ] Location scouting (matches reference aesthetic)
- [ ] Equipment list (achieves reference visual quality)
- [ ] Talent/casting brief

### Shot-by-Shot Replication Guide
[Scene 1]: [Shot type] + [Movement] + [Lens focal length estimate] + [Lighting note]
...

### Post-Production Recipe
- Color grade LUT style: [description]
- Edit pacing: [X sec avg shot length]
- Music: [tempo, genre, emotional arc]
- Sound design notes

### Quality Gate
≥80% replication is achieved when: [specific measurable criteria]
```

### Step 3: Director's Commentary

Add a director-level creative layer ON TOP of the reference:
- Identify what the reference does well and what it misses
- Propose 2–3 creative upgrades that elevate beyond the reference
- Write the narrative with a **screenwriter's eye**: subtext, visual metaphor, character arc

---

## Workflow B — Daily Video Intelligence Digest

> **This workflow runs automatically via the daily automation sidecar.**
> The agent reads the latest digest from `~/.gemini/config/plugins/video-distillery/data/daily_digest.md`.

### What Gets Scanned Daily

**Video Sources** (run `scripts/daily_video_scan.py`):
- Vimeo Staff Picks (cinematic shorts, docs, brand films)
- YouTube curated channels: cinema, documentary, advertising
- Film festival online showcases (Sundance, TIFF, Tribeca online)
- TED/FORA.tv for high-production talks
- Brand film award winners (Cannes Lions, D&AD)
- Short film platforms (Short of the Week)

**What Gets Distilled**:
- Shot pattern library update (new techniques observed)
- Color/grade trends
- Narrative structure patterns
- Production technique innovations

### Reading the Daily Digest

When the user asks "今天发现了什么" or "每日摘要":
1. Read `~/.gemini/config/plugins/video-distillery/data/daily_digest.md`
2. Read `~/.gemini/config/plugins/video-distillery/data/github_tools.md`
3. Present: Top 3 videos, key craft lessons, top 3 GitHub tools, integration suggestions

---

## Workflow C — Director/Screenwriter Script Generation

When the user wants a script or treatment:

### Narrative Frameworks (read [narrative_frameworks.md](./references/narrative_frameworks.md))

Apply the most fitting structure:
- **3-Act** (brand films, shorts): Setup → Confrontation → Resolution
- **In Media Res** (action, thriller): Drop into peak moment, flashback, return
- **Character Journey** (documentary): Follow a person's transformation
- **Poetic/Essayistic** (art film): Associative logic, visual poetry
- **Problem → Solution** (corporate): Pain point → insight → transformation

### Output Format

Always produce:
1. **Logline** (1–2 sentences, the whole story)
2. **Emotional Map** (scene-by-scene emotional journey)
3. **Full Script/Treatment** with scene headings, action lines, dialogue
4. **Director's Notes** per scene (shot language, mood, music cue)
5. **Shot List** (numbered, with equipment notes)

---

## Workflow D — GitHub Tool Integration

When the user asks about video tools or the daily scan discovers relevant repos:

**Evaluation Criteria** (run `scripts/daily_github_scan.py`):
- Stars ≥ 500 AND active commits in last 90 days
- Categories: video editing, color grading, motion tracking, AI video generation, ffmpeg wrappers, subtitle/caption tools, scene detection, audio sync
- License: permissive (MIT/Apache/BSD preferred)

**Integration Output**:
```markdown
## Discovered Tool: [repo-name]
- **Repo**: github.com/[owner]/[repo]
- **Stars**: [n] | **Last commit**: [date]
- **What it does**: [1-line]
- **How it fits your workflow**: [specific use case]
- **Quick start**: `[install command]`
```

---

## Quality Standards

Every output must meet **film-quality benchmarks**:

| Standard | Requirement |
|----------|-------------|
| Narrative | Clear 3-act or intentional non-linear structure |
| Visuals | Shot list with specific lens, movement, lighting for every scene |
| Pacing | Edit rhythm mapped to music/emotion curve |
| Sound | Full sound design brief (music + SFX + dialogue) |
| Color | Grade style with reference images or descriptors |
| Replication | Measurable ≥80% fidelity criteria stated explicitly |

---

## Quick Reference Commands

| User Says | Action |
|-----------|--------|
| 分析这个参考片 | Run Workflow A — full deconstruction |
| 帮我复刻这个视频 | Run Workflow A → produce Production Bible |
| 今天发现了什么 | Read daily digest → present summary |
| 写分镜/脚本 | Run Workflow C — script generation |
| 有什么新工具 | Read github_tools.md → present top finds |
| 导演视角建议 | Apply director upgrade layer to any project |
