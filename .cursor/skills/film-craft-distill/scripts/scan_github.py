#!/usr/bin/env python3
"""Scan GitHub for video-production tools worth adopting."""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import http_get, is_fresh

REJECT = re.compile(
    r"face\s*swap|faceswap|deepfake|deep-fake|insightface|\broop\b|nudif|undress|"
    r"onlyfans|swap the face|换脸|deepface|face recognition|人脸识别",
    re.I,
)
HOLD = re.compile(
    r"clone any|clone viral|viral video|remake any|一键生成|one[- ]click|"
    r"from a topic|viral short|100M views|money printer",
    re.I,
)
INFRA = re.compile(r"(^|/)(FFmpeg|obs-studio|mpv|scrcpy|vlc|kodi|yt-dlp|youtube-dl)$", re.I)
PHOTO = re.compile(r"RAW image|photo editor|image editor", re.I)
RECORDER = re.compile(r"\b(recorder|screen recording|live streaming)\b", re.I)
SKIP = re.compile(r"youtube-dl|yt-dlp|watermark remover|video downloader|去水印", re.I)
SLOTS = (
    ("caption", re.compile(r"caption|subtitle|whisper|srt", re.I)),
    ("grade", re.compile(r"color|grade|lut", re.I)),
    ("scene", re.compile(r"scene|shot detect|transcrib", re.I)),
    ("motion", re.compile(r"motion|remotion|lottie|after effects", re.I)),
    ("audio", re.compile(r"audio|loudness|mix|music|ffmpeg", re.I)),
    ("edit", re.compile(r"editor|timeline|nle|cut|video", re.I)),
)


def _queries(day: Any) -> List[str]:
    start = (day - timedelta(days=14)).isoformat()
    return [
        f"topic:video-editing pushed:>={start} stars:15..3000 fork:false",
        f"topic:remotion pushed:>={start} stars:10..3000 fork:false",
        f"topic:color-grading pushed:>={start} fork:false",
        f"topic:subtitles pushed:>={start} stars:15..2000 fork:false",
    ]


def _search(query: str) -> Dict[str, Any]:
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
        {"q": query, "sort": "stars", "order": "desc", "per_page": "15"}
    )
    raw = http_get(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    return json.loads(raw.decode("utf-8"))


def _slot(text: str) -> str:
    for name, pattern in SLOTS:
        if pattern.search(text):
            return name
    return "edit"


def _keep(repo: Dict[str, Any], now: datetime) -> bool:
    if repo.get("archived") or repo.get("disabled") or repo.get("fork"):
        return False
    stars = int(repo.get("stargazers_count") or 0)
    created = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
    fresh = (now - created) <= timedelta(days=21)
    return stars >= 10 or (fresh and stars >= 3)


def _entry(repo: Dict[str, Any], reason: str) -> str:
    license_info = repo.get("license") or {}
    spdx = license_info.get("spdx_id") or "未标许可证"
    text = f"{repo.get('full_name', '')} {repo.get('description') or ''}"
    description = (repo.get("description") or "（没有简介）").replace("\n", " ")[:180]
    return (
        f"- **{repo['full_name']}** ★{repo.get('stargazers_count', 0)} · {_slot(text)} · {spdx}\n"
        f"  - {reason}\n"
        f"  - {description}\n"
        f"  - https://github.com/{repo['full_name']}\n"
    )


def collect(seen: Dict[str, Any], day: Any, force: bool = False) -> Tuple[str, List[str]]:
    now = datetime.now(timezone.utc)
    errors: List[str] = []
    found: Dict[str, Dict[str, Any]] = {}
    for query in _queries(day):
        try:
            payload = _search(query)
        except (RuntimeError, json.JSONDecodeError, KeyError) as exc:
            errors.append(f"- `{query}`: {exc}")
            continue
        if payload.get("message"):
            errors.append(f"- `{query}`: {payload.get('message')}")
            continue
        for repo in payload.get("items") or []:
            if not _keep(repo, now):
                continue
            found.setdefault(repo["full_name"], repo)

    candidates: List[Dict[str, Any]] = []
    holds: List[Tuple[Dict[str, Any], str]] = []
    rejects: List[Tuple[Dict[str, Any], str]] = []
    infra: List[Dict[str, Any]] = []
    keys: List[str] = []
    for repo in sorted(found.values(), key=lambda row: int(row.get("stargazers_count") or 0), reverse=True):
        name = repo["full_name"]
        if not is_fresh(seen, "github", name, day, force):
            continue
        text = f"{name} {repo.get('description') or ''}"
        if REJECT.search(text):
            rejects.append((repo, "拒绝：换脸、deepfake 或色情换装，不安装。"))
        elif SKIP.search(text):
            rejects.append((repo, "不接入：下载器或去水印，不是成片工艺。"))
        elif INFRA.search(name):
            infra.append(repo)
        elif PHOTO.search(text) and not re.search(r"\bvideo\b", text, re.I):
            keys.append(name)
            continue
        elif RECORDER.search(text) and not re.search(r"editor|timeline|caption|grade|remotion", text, re.I):
            keys.append(name)
            continue
        elif not ((repo.get("license") or {}).get("spdx_id") or "") or (repo.get("license") or {}).get("spdx_id") in {"NOASSERTION", "NONE"}:
            holds.append((repo, "观望：许可证不清楚。"))
        elif HOLD.search(text):
            holds.append((repo, "先不要接入。一键成片或「重做任何视频」不是这条工艺。README 若证明它只剪用户自己的素材，才可以改判。"))
        else:
            candidates.append(repo)

    lines = ["## 可以评估\n"]
    if candidates:
        for repo in candidates[:8]:
            lines.append(_entry(repo, "状态: 待评估"))
            keys.append(repo["full_name"])
    else:
        lines.append("今天没有新的可评估项目。\n")
    if infra:
        lines.append("\n## 已知底座\n\n播放器、录屏或 FFmpeg 本体。已经在用，不重复接入。\n")
        for repo in infra[:4]:
            lines.append(_entry(repo, "状态: 已知"))
            keys.append(repo["full_name"])
    lines.append("\n## 先不要接入\n")
    if holds:
        for repo, reason in holds[:5]:
            lines.append(_entry(repo, reason))
            keys.append(repo["full_name"])
    else:
        lines.append("无。\n")
    lines.append("\n## 拒绝\n")
    if rejects:
        for repo, reason in rejects[:5]:
            lines.append(_entry(repo, reason))
            keys.append(repo["full_name"])
    else:
        lines.append("无。\n")
    if errors:
        lines.append("\n## 查询失败\n\n" + "\n".join(errors) + "\n")
    lines.append(
        "\n未标许可证的只能观望。接入前要在样片上跑通一条命令，并写进 library/toolchain.md。拒绝类不要打开安装。\n"
    )
    return "\n".join(lines), keys
