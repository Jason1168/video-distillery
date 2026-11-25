#!/usr/bin/env python3
"""Collect today's film candidates and GitHub video tools."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import library, load_seen, mark, save_seen, today
from scan_github import collect as collect_github
from scan_videos import collect as collect_videos


def _digest_ok(path: Path) -> bool:
    if not path.exists():
        return False
    return "<!-- status: ok -->" in path.read_text(encoding="utf-8")


def run(force: bool = False) -> int:
    day = today()
    path = library() / "digests" / f"{day.isoformat()}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if _digest_ok(path) and not force:
        print(path)
        return 0
    seen = load_seen()
    video_error = github_error = ""
    video_keys: list = []
    github_keys: list = []
    try:
        video_md, video_keys = collect_videos(seen, day, force)
    except Exception as exc:  # noqa: BLE001 - one bad source set should not hide the other
        video_error = str(exc)
        video_md = f"## 视频扫描失败\n\n{exc}\n"
    try:
        github_md, github_keys = collect_github(seen, day, force)
    except Exception as exc:  # noqa: BLE001
        github_error = str(exc)
        github_md = f"## GitHub 扫描失败\n\n{exc}\n"
    status = "ok" if not video_error and not github_error else "partial"
    body = (
        f"<!-- status: {status} -->\n"
        f"# {day.isoformat()} 候选\n\n"
        "定时收集只到名单。导演卡片和工具去留在对话里做。\n"
        "成片完成线是 95 分。这份名单不是镜头表。\n\n"
        f"{video_md}\n"
        f"{github_md}\n"
    )
    path.write_text(body, encoding="utf-8")
    if not video_error:
        for key in video_keys:
            mark(seen, "videos", key, day)
    if not github_error:
        for key in github_keys:
            mark(seen, "github", key, day)
    if not video_error or not github_error:
        save_seen(seen)
    print(path)
    return 0 if status == "ok" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="收集今天的影片和视频工具")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    return run(force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
