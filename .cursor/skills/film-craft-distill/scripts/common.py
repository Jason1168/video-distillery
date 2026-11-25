#!/usr/bin/env python3
"""Shared paths, HTTP, and media parsing for film-craft-distill."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from html import unescape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

UA = "film-craft-distill"
ROOT = Path(__file__).resolve().parents[1]


def library() -> Path:
    path = ROOT / "library"
    path.mkdir(parents=True, exist_ok=True)
    return path


def today() -> date:
    return date.today()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_seen() -> Dict[str, Dict[str, str]]:
    data = load_json(library() / "seen.json", {"videos": {}, "github": {}})
    data.setdefault("videos", {})
    data.setdefault("github", {})
    return data


def save_seen(seen: Dict[str, Dict[str, str]]) -> None:
    cutoff = today() - timedelta(days=180)
    for bucket in list(seen.values()):
        for key, raw in list(bucket.items()):
            try:
                stamped = date.fromisoformat(raw)
            except ValueError:
                stamped = None
            if stamped is None or stamped < cutoff:
                del bucket[key]
    save_json(library() / "seen.json", seen)


def mark(seen: Dict[str, Dict[str, str]], bucket: str, key: str, day: date) -> None:
    seen.setdefault(bucket, {})[key] = day.isoformat()


def is_fresh(seen: Dict[str, Dict[str, str]], bucket: str, key: str, day: date, force: bool) -> bool:
    prev = seen.get(bucket, {}).get(key)
    if prev is None:
        return True
    return bool(force and prev == day.isoformat())


def strip_html(raw: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", " ", raw or ""))
    return re.sub(r"\s+", " ", text).strip()


def http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 25) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"HTTP {exc.code} {url} {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"网络失败 {url}: {exc.reason}") from exc


def ffmpeg_bin() -> str:
    env = os.environ.get("FFMPEG_BIN", "").strip()
    if env and Path(env).exists():
        return env
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise RuntimeError("找不到 ffmpeg。安装 ffmpeg，或设置 FFMPEG_BIN。")


def run_cmd(args: List[str], timeout: int = 120) -> Tuple[int, str]:
    proc = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    err = proc.stderr.decode("utf-8", "replace")
    out = proc.stdout.decode("utf-8", "replace")
    return proc.returncode, out + err


_DURATION = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
_VIDEO = re.compile(
    r"Video:\s*([^,\n]+).*?(\d{2,5})x(\d{2,5}).*?(?:([\d.]+)\s*fps|([\d.]+)\s*tbr)",
    re.S,
)
_AUDIO = re.compile(r"Audio:\s*([^,\n]+),\s*(\d+)\s*Hz,\s*([^,\n]+)")


def _seconds(hours: str, minutes: str, seconds: str) -> float:
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def parse_media_info(log: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "duration": None,
        "width": None,
        "height": None,
        "fps": None,
        "video_codec": None,
        "has_audio": False,
        "sample_rate": None,
        "channels": None,
        "audio_codec": None,
    }
    duration = _DURATION.search(log)
    if duration:
        info["duration"] = round(_seconds(*duration.groups()), 3)
    video = _VIDEO.search(log)
    if video:
        codec, width, height, fps, tbr = video.groups()
        info["video_codec"] = codec.strip()
        info["width"] = int(width)
        info["height"] = int(height)
        info["fps"] = float(fps or tbr)
    audio = _AUDIO.search(log)
    if audio:
        info["has_audio"] = True
        info["audio_codec"] = audio.group(1).strip()
        info["sample_rate"] = int(audio.group(2))
        info["channels"] = audio.group(3).strip()
    return info


def probe_header(path: str, timeout: int = 60) -> Dict[str, Any]:
    code, log = run_cmd([ffmpeg_bin(), "-hide_banner", "-i", path], timeout=timeout)
    info = parse_media_info(log)
    info["header_code"] = code
    info["header_log"] = log
    return info
