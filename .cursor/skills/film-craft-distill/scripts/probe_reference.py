#!/usr/bin/env python3
"""Measure a reference or a replica: cuts, loudness, black, silence, stills."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ffmpeg_bin, parse_media_info, run_cmd, save_json

SCENE_THRESHOLD = 12.0
_PTS = re.compile(r"pts_time:([0-9.]+)")
_DIFF = re.compile(r"signalstats\.(YDIF|UDIF|VDIF)=([0-9.]+)")
_BLACK = re.compile(r"black_start:([0-9.]+)\s+black_end:([0-9.]+)\s+black_duration:([0-9.]+)")
_SILENCE_START = re.compile(r"silence_start:\s*([0-9.]+)")
_SILENCE_END = re.compile(r"silence_end:\s*([0-9.]+)\s+\|\s+silence_duration:\s*([0-9.]+)")
_LOUD = re.compile(r"\{[^{}]*\"input_i\"[^{}]*\}", re.S)


def _fnum(value: Any) -> Optional[float]:
    if value in (None, "-inf", "inf", "nan"):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _cut_times(log: str) -> List[float]:
    pts: Optional[float] = None
    scores: Dict[str, float] = {}
    series: List[Tuple[float, float]] = []
    for line in log.splitlines():
        point = _PTS.search(line)
        if point and "frame:" in line:
            if pts is not None:
                series.append((pts, max(scores.values()) if scores else 0.0))
            scores = {}
            pts = float(point.group(1))
        for match in _DIFF.finditer(line):
            scores[match.group(1)] = float(match.group(2))
    if pts is not None:
        series.append((pts, max(scores.values()) if scores else 0.0))
    cuts: List[float] = []
    recent: List[float] = []
    for moment, score in series:
        baseline = (sum(recent[-5:]) / len(recent[-5:])) if recent else 0.0
        recent.append(score)
        if moment < 0.08 or score < SCENE_THRESHOLD:
            continue
        if score < baseline * 2 + 10:
            continue
        if cuts and moment - cuts[-1] < 0.2:
            continue
        cuts.append(round(moment, 3))
    return cuts


def _shots(duration: float, raw_times: List[float]) -> Tuple[List[float], List[float]]:
    points = [0.0]
    for raw in sorted(raw_times):
        if raw - points[-1] >= 0.08 and duration - raw >= 0.08:
            points.append(round(raw, 3))
    points.append(duration)
    durations = [round(b - a, 3) for a, b in zip(points, points[1:])]
    durations[-1] = round(durations[-1] + (duration - sum(durations)), 3)
    return durations, points[1:-1]


def _sample(times: List[float], limit: int) -> List[float]:
    if len(times) <= limit:
        return times
    if limit <= 1:
        return times[:1]
    last = len(times) - 1
    indexes = sorted({int(round(i * last / (limit - 1))) for i in range(limit)})
    return [times[index] for index in indexes]


def _export_sheets(ff: str, path: str, out: Path, duration: float) -> List[str]:
    sheets = out / "sheets"
    sheets.mkdir(parents=True, exist_ok=True)
    interval = 2.0 if duration <= 12 * 60 else max(2.0, duration / 48)
    rate = 1.0 / interval
    code, log = run_cmd(
        [
            ff, "-y", "-hide_banner", "-i", path,
            "-vf", f"fps={rate:.4f},scale=240:-2,tile=6x4",
            "-q:v", "4",
            str(sheets / "sheet_%02d.jpg"),
        ],
        timeout=max(180, int(duration * 2)),
    )
    files = sorted(sheets.glob("sheet_*.jpg"))
    if code != 0 or not files:
        (out / "sheet-error.log").write_text(log[-4000:], encoding="utf-8")
        return []
    return [str(item.relative_to(out)) for item in files]


def _export_stills(ff: str, path: str, out: Path, times: List[float]) -> List[str]:
    stills = out / "shots"
    stills.mkdir(parents=True, exist_ok=True)
    written: List[str] = []
    for index, moment in enumerate(times, start=1):
        target = stills / f"shot_{index:03d}.jpg"
        code, _log = run_cmd(
            [
                ff, "-y", "-hide_banner", "-ss", f"{max(0.0, moment):.3f}",
                "-i", path, "-frames:v", "1", "-vf", "scale=480:-2",
                str(target),
            ],
            timeout=60,
        )
        if code == 0 and target.exists():
            written.append(str(target.relative_to(out)))
    return written


def _loudness(ff: str, path: str, duration: float) -> Dict[str, Optional[float]]:
    _code, log = run_cmd(
        [
            ff, "-hide_banner", "-i", path,
            "-af", "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json",
            "-f", "null", "-",
        ],
        timeout=max(180, int(duration * 3)),
    )
    found = _LOUD.findall(log)
    if not found:
        return {"integrated_lufs": None, "true_peak_dbtp": None, "lra": None}
    payload = json.loads(found[-1])
    return {
        "integrated_lufs": _fnum(payload.get("input_i")),
        "true_peak_dbtp": _fnum(payload.get("input_tp")),
        "lra": _fnum(payload.get("input_lra")),
        "thresh": _fnum(payload.get("input_thresh")),
        "offset": _fnum(payload.get("target_offset")),
    }


def _black_and_silence(ff: str, path: str, duration: float) -> Tuple[float, float, List[str]]:
    _code, log = run_cmd(
        [
            ff, "-hide_banner", "-i", path,
            "-vf", "blackdetect=d=0.08:pic_th=0.98:pix_th=0.10",
            "-af", "silencedetect=n=-36dB:d=0.35",
            "-f", "null", "-",
        ],
        timeout=max(180, int(duration * 3)),
    )
    black = sum(float(item[2]) for item in _BLACK.findall(log))
    silence = sum(float(item[1]) for item in _SILENCE_END.findall(log))
    warnings = []
    if _SILENCE_START.findall(log) and not _SILENCE_END.findall(log):
        warnings.append("静音检测到开头但没有结束，静音时长可能偏低。")
    return round(black, 3), round(silence, 3), warnings


def _extract_reel(ff: str, path: Path, out: Path, reel: Tuple[float, float]) -> Path:
    target = out / "reel.mp4"
    code, log = run_cmd(
        [
            ff, "-y", "-hide_banner",
            "-ss", str(reel[0]), "-to", str(reel[1]),
            "-i", str(path),
            "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "192k",
            str(target),
        ],
        timeout=max(240, int((reel[1] - reel[0]) * 4) + 60),
    )
    if code != 0 or not target.exists():
        raise RuntimeError("这一盘切不出来。\n" + log[-1500:])
    return target


def measure(path: Path, out: Path, reel: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
    ff = ffmpeg_bin()
    out.mkdir(parents=True, exist_ok=True)
    source_label = str(path.resolve())
    if reel:
        path = _extract_reel(ff, path, out, reel)
    header_cmd = [ff, "-hide_banner", "-i", str(path)]
    _code, header_log = run_cmd(header_cmd, timeout=90)
    info = parse_media_info(header_log)
    warnings: List[str] = []
    if not info["duration"] or not info["width"] or not info["fps"]:
        warnings.append("文件头缺少时长、分辨率或帧率。")
    duration = float(info["duration"] or 0.0)
    scene_cmd = [
        ff, "-hide_banner", "-i", str(path),
        "-vf", "scale=32:18,format=yuv444p,signalstats,metadata=print",
        "-an", "-f", "null", "-",
    ]
    scene_code, scene_log = run_cmd(scene_cmd, timeout=max(240, int(duration * 4) + 60))
    if scene_code != 0:
        warnings.append("切点分析失败，节奏分不可用。")
        (out / "scene-error.log").write_text(scene_log[-4000:], encoding="utf-8")
        cut_times: List[float] = []
    else:
        cut_times = _cut_times(scene_log)
    shot_durations, cut_times = _shots(duration, cut_times) if duration else ([], [])
    loud = {"integrated_lufs": None, "true_peak_dbtp": None, "lra": None}
    black = silence = 0.0
    if info["has_audio"] and duration:
        loud = _loudness(ff, str(path), duration)
        if loud["integrated_lufs"] is None:
            warnings.append("有声音但没有测到综合响度。")
    if duration:
        black, silence, extra = _black_and_silence(ff, str(path), duration)
        warnings.extend(extra)
    sheets = _export_sheets(ff, str(path), out, duration) if duration else []
    if not sheets:
        warnings.append("没有接触表，不能给镜头语法打满。")
    still_times = cut_times or ([min(0.2, duration / 2)] if duration else [])
    sampled = duration > 12 * 60 or len(still_times) > 80
    exported_times = _sample(still_times, 80)
    stills = _export_stills(ff, str(path), out, exported_times) if duration else []
    if sampled:
        warnings.append("切点静帧是抽样。镜头语法最高 8 分。长片请按 8 到 12 分钟一盘重测。")
    elif len(stills) > 24:
        warnings.append("切点超过 24 个。镜头语法最高 9 分，除非你按盘重切到 24 个切点以内。")
    coverage = "full"
    if warnings and any("失败" in item or "缺少" in item or "没有接触表" in item for item in warnings):
        coverage = "partial"
    if not sheets or not stills or not duration:
        coverage = "partial"
    if info["has_audio"] and loud["integrated_lufs"] is None:
        coverage = "partial"
    probe: Dict[str, Any] = {
        "source": source_label,
        "coverage": coverage,
        "stills_sampled": sampled,
        "still_count": len(stills),
        "sheet_count": len(sheets),
        "has_audio": bool(info["has_audio"]),
        "duration": duration,
        "width": info["width"],
        "height": info["height"],
        "fps": info["fps"],
        "avg_shot_length": round(duration / len(shot_durations), 3) if shot_durations else None,
        "first_cut": cut_times[0] if cut_times else duration,
        "integrated_lufs": loud["integrated_lufs"],
        "true_peak_dbtp": loud["true_peak_dbtp"],
        "black_seconds": black,
        "silence_seconds": silence,
        "shot_count": len(shot_durations),
        "cut_times": cut_times,
        "shot_durations": shot_durations,
        "sheets": sheets,
        "stills": stills,
        "reel": list(reel) if reel else None,
        "scene_threshold": SCENE_THRESHOLD,
        "warnings": warnings,
    }
    save_json(out / "probe.json", probe)
    _write_skeleton(out / "skeleton.json", probe)
    return probe


def _write_skeleton(path: Path, probe: Dict[str, Any]) -> None:
    slots = []
    cursor = 0.0
    for index, dur in enumerate(probe["shot_durations"]):
        slots.append(
            {
                "index": index,
                "t": round(cursor, 3),
                "dur": dur,
                "function": "",
                "picture": "",
                "sound": "",
                "text": "",
                "text_pos": "bottom",
                "source": "",
                "in": 0,
                "must_fill": True,
            }
        )
        cursor = round(cursor + dur, 3)
    save_json(
        path,
        {
            "upgrade": "",
            "upgrade_dimension": "",
            "slots": slots,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="测量参考片或成片")
    parser.add_argument("video")
    parser.add_argument("--out", required=True)
    parser.add_argument("--reel", nargs=2, type=float, metavar=("START", "END"))
    args = parser.parse_args()
    source = Path(args.video)
    if not source.exists():
        print(f"找不到文件: {source}", file=sys.stderr)
        return 1
    try:
        probe = measure(source, Path(args.out), tuple(args.reel) if args.reel else None)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        f"coverage={probe['coverage']} duration={probe['duration']}s "
        f"shots={probe['shot_count']} lufs={probe['integrated_lufs']} "
        f"sheets={probe['sheet_count']} stills={probe['still_count']}"
    )
    print(Path(args.out) / "probe.json")
    return 0 if probe["coverage"] == "full" else 2


if __name__ == "__main__":
    raise SystemExit(main())
