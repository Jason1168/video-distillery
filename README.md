# 🎬 Video Distillery

> An Antigravity plugin that **distills cinematic craft from the world's best videos daily** and replicates any reference video at ≥80% quality — with director-level storytelling and documentary-grade narrative structure.

---

## ✨ What It Does

| Capability | Description |
|------------|-------------|
| 🔍 **Daily Video Scan** | Every morning, automatically scans Vimeo Staff Picks, Short of the Week, Nowness, Cannes Lions winners, and more — distilling shot language, color, narrative patterns, and editing rhythms into a growing knowledge base |
| 🛠️ **Daily GitHub Scan** | Discovers and evaluates the best open-source video production tools on GitHub daily — integrating them into your workflow |
| 🎯 **Reference Replication** | Give it any reference video — it produces a full **Production Bible** to replicate it at ≥80% quality: shot list, lighting, color grade, edit structure, sound design |
| 🎬 **Director/Screenwriter Mode** | Applies professional film craft: 3-act structure, visual metaphor, emotional arc mapping, shot-by-shot director's notes — film and documentary quality output |

---

## 🚀 Installation

```bash
git clone https://github.com/YOUR_USERNAME/video-distillery \
  ~/.gemini/config/plugins/video-distillery
```

Then:
1. Open **Antigravity → Customizations** → find **Video Distillery** → enable it
2. Open **Automations Dashboard** → enable both daily automations:
   - **Video Distillery — Daily Video Scan** (runs at 7:00 AM)
   - **Video Distillery — Daily GitHub Scan** (runs at 7:30 AM)

---

## 💬 Usage

Just talk to Antigravity naturally:

```
分析这个参考片并复刻方案
[paste video URL]
```

```
今天发现了哪些顶级视频和开源工具？
```

```
用导演思维帮我写这个视频的分镜脚本
[describe your project]
```

```
帮我复刻这个视频风格：[URL]
```

---

## 📁 Plugin Structure

```
video-distillery/
├── plugin.json                          # Plugin manifest
└── skills/video-distillery/
    ├── SKILL.md                         # Core skill instructions
    ├── scripts/
    │   ├── daily_video_scan.py          # Daily video intelligence scanner
    │   ├── daily_github_scan.py         # Daily GitHub tools scanner
    │   └── replicate_reference.py       # Reference replication engine
    └── references/
        ├── cinematic_principles.md      # Shot language, editing, color, lighting
        ├── narrative_frameworks.md      # 11 storytelling structures
        └── tool_registry.md            # Open-source tool index
```

---

## 🎓 Knowledge Base

The plugin maintains a growing knowledge base at:
```
~/.gemini/config/plugins/video-distillery/data/
├── daily_digest.md      # Latest video scan results
├── github_tools.md      # Latest tool discoveries
└── knowledge_base.json  # Accumulated craft patterns
```

This database grows every day — the more it runs, the smarter it gets.

---

## 🔬 Reference Replication Workflow

When you give it a reference video, it:

1. **Deconstructs** — Shot language, edit rhythm, color grade, narrative arc, sound design, emotional map
2. **Blueprints** — Full Production Bible with measurable replication criteria
3. **Upgrades** — Director-level creative improvements on top of the reference
4. **Quality-gates** — Explicit ≥80% fidelity checklist across narrative, visual, and audio dimensions

---

## 📚 Built-in Film Craft Reference

- **11 narrative structures** (3-act, Hero's Journey, In Media Res, Poetic, Kishōtenketsu, etc.)
- **Complete shot language system** (sizes, movements, focal lengths, DOF, frame rates)
- **Professional color grading** (temperature, style taxonomy, color psychology)
- **Sound design hierarchy** (music, dialogue, SFX, silence)
- **Lighting setup library** (golden hour, Rembrandt, backlit, practical, etc.)
- **Editing principles** (Walter Murch's 6 rules, pacing curves, cut types)

---

## 🛠️ Requirements

- [Antigravity](https://antigravity.dev) AI assistant
- macOS (paths use `~/.gemini/config/`)
- Internet access for daily scans

---

## 📄 License

MIT License — see [LICENSE](./LICENSE)

---

## 🤝 Contributing

PRs welcome! Especially:
- New video source integrations
- Additional narrative frameworks
- More GitHub tool search queries
- Language support beyond Chinese/English
