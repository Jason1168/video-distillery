#!/usr/bin/env python3
"""Cut the user's own footage to a measured rhythm skeleton."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_plan import validate
from common import ffmpeg_bin, load_json, probe_header, run_cmd, save_json
from probe_reference import _loudness

IMAGES = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
FONTS = (
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/STHeiti Medium.ttc",
)


def _font() -> str:
    for candidate in FONTS:
        if Path(candidate).exists():
            return candidate
    return ""


def _escape(path: str) -> str:
    return path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _graph(
    slots: List[Dict[str, Any]],
    width: int,
    height: int,
    fps: float,
    work: Path,
    burn: bool,
) -> tuple:
    ff_inputs: List[str] = []
    chains: List[str] = []
    pairs: List[str] = []
    index = 0
    text_slots = []
    for slot in slots:
        dur = float(slot["dur"])
        inn = float(slot.get("in") or 0)
        source = str(slot["source"])
        image = Path(source).suffix.lower() in IMAGES
        has_audio = False
        if not image:
            info = probe_header(source)
            media_dur = float(info.get("duration") or 0)
            if media_dur + 0.05 < inn + dur:
                raise RuntimeError(
                    f"槽位 {slot.get('index')} 的素材只有 {media_dur:.2f}s，这一刀需要 {inn + dur:.2f}s。"
                )
            has_audio = bool(info.get("has_audio"))
            ff_inputs += ["-i", source]
        else:
            ff_inputs += ["-loop", "1", "-framerate", f"{fps:.3f}", "-t", f"{dur + 0.25:.3f}", "-i", source]
        video_index = index
        index += 1
        if image or not has_audio:
            ff_inputs += [
                "-f", "lavfi", "-t", f"{dur + 0.25:.3f}",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
            ]
            audio_index = index
            index += 1
            audio_in = 0.0
        else:
            audio_index = video_index
            audio_in = inn
        video_in = 0.0 if image else inn
        label = int(slot.get("index") or 0)
        chains.append(
            f"[{video_index}:v]trim=start={video_in:.3f}:duration={dur:.3f},setpts=PTS-STARTPTS,"
            f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
            f"fps={fps:.3f},format=yuv420p,setsar=1[v{label}]"
        )
        chains.append(
            f"[{audio_index}:a]atrim=start={audio_in:.3f}:duration={dur:.3f},asetpts=PTS-STARTPTS,"
            f"aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a{label}]"
        )
        pairs.append(f"[v{label}][a{label}]")
        if str(slot.get("text") or "").strip():
            text_slots.append(slot)
    graph = ";".join(chains)
    graph += f";{''.join(pairs)}concat=n={len(slots)}:v=1:a=1[v][a]"
    burned = False
    font = _font()
    if burn and text_slots and font:
        current = "[v]"
        for nth, slot in enumerate(text_slots):
            text_path = work / f"text_{nth}.txt"
            text_path.write_text(str(slot["text"]).strip() + "\n", encoding="utf-8")
            start = float(slot["t"])
            end = start + float(slot["dur"])
            pos = slot.get("text_pos") or "bottom"
            if pos == "top":
                y = "80"
            elif pos == "center":
                y = "(h-text_h)/2"
            else:
                y = "h-text_h-80"
            nxt = f"[vt{nth}]"
            size = max(28, height // 28)
            graph += (
                f";{current}drawtext=fontfile='{_escape(font)}':textfile='{_escape(str(text_path))}'"
                f":fontsize={size}:fontcolor=white:borderw=2:bordercolor=black"
                f":x=(w-text_w)/2:y={y}:enable='between(t\\,{start:.3f}\\,{end:.3f})'{nxt}"
            )
            current = nxt
        graph += f";{current}null[vout]"
        burned = True
    else:
        graph += ";[v]null[vout]"
    script = work / "graph.txt"
    script.write_text(graph, encoding="utf-8")
    return ff_inputs, script, len(text_slots), burned and bool(text_slots)


def _render(ff: str, inputs: List[str], script: Path, target: Path, duration: float, fps: float) -> tuple:
    return run_cmd(
        [
            ff, "-y", "-hide_banner", *inputs,
            "-filter_complex_script", str(script),
            "-map", "[vout]", "-map", "[a]",
            "-r", f"{fps:.3f}", "-fps_mode", "cfr", "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
            str(target),
        ],
        timeout=max(300, int(duration * 8) + 60),
    )


def _apply_loudness(ff: str, temp: Path, final: Path, target_lufs: float, duration: float) -> bool:
    measured = _loudness(ff, str(temp), duration)
    needed = ("integrated_lufs", "true_peak_dbtp", "lra", "thresh", "offset")
    if any(measured.get(key) is None for key in needed):
        return False
    audio = (
        f"loudnorm=I={target_lufs:.2f}:TP=-1.5:LRA=11:"
        f"measured_I={measured['integrated_lufs']:.2f}:"
        f"measured_TP={measured['true_peak_dbtp']:.2f}:"
        f"measured_LRA={measured['lra']:.2f}:"
        f"measured_thresh={measured['thresh']:.2f}:"
        f"offset={measured['offset']:.2f}:linear=true,aresample=48000"
    )
    code, log = run_cmd(
        [
            ff, "-y", "-hide_banner", "-i", str(temp),
            "-c:v", "copy", "-af", audio, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-t", f"{duration:.3f}",
            str(final),
        ],
        timeout=max(180, int(duration * 4) + 30),
    )
    if code != 0:
        (final.parent / "loudnorm-error.log").write_text(log[-2000:], encoding="utf-8")
        return False
    return True


def assemble(skeleton: Dict[str, Any], probe: Dict[str, Any], out: Path) -> Dict[str, Any]:
    errors = validate(skeleton, probe, "assemble")
    if errors:
        raise RuntimeError("导演本还没到能导出的程度。\n" + "\n".join(f"- {item}" for item in errors))
    if probe.get("coverage") != "full":
        raise RuntimeError("参考片测量不完整，不能按它锁节奏。")
    width = int(probe["width"]) // 2 * 2
    height = int(probe["height"]) // 2 * 2
    fps = float(probe["fps"])
    slots = sorted(skeleton["slots"], key=lambda slot: float(slot["t"]))
    duration = sum(float(slot["dur"]) for slot in slots)
    target_lufs = probe.get("integrated_lufs")
    if target_lufs is None:
        target_lufs = -14.0
    out.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="filmcraft-"))
    ff = ffmpeg_bin()
    temp = work / "cut.mp4"
    inputs, script, text_count, burned = _graph(slots, width, height, fps, work, burn=True)
    code, log = _render(ff, inputs, script, temp, duration, fps)
    if code != 0 and text_count:
        inputs, script, text_count, burned = _graph(slots, width, height, fps, work, burn=False)
        code, log = _render(ff, inputs, script, temp, duration, fps)
        burned = False
    if code != 0 or not temp.exists():
        raise RuntimeError(f"组装失败，滤镜留在 {script}。\n" + log[-2000:])
    applied = _apply_loudness(ff, temp, out, float(target_lufs), duration)
    if not applied:
        shutil.copy2(temp, out)
    notes = {
        "text_slots": text_count,
        "text_burned": bool(burned and text_count) or text_count == 0,
        "loudness_target": float(target_lufs),
        "loudness_applied": applied,
        "output": str(out.resolve()),
    }
    notes_path = out.with_suffix(".assemble-notes.json")
    save_json(notes_path, notes)
    shutil.rmtree(work, ignore_errors=True)
    return notes


def main() -> int:
    parser = argparse.ArgumentParser(description="按骨架把用户素材切成成片")
    parser.add_argument("--skeleton", required=True)
    parser.add_argument("--probe", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        notes = assemble(load_json(Path(args.skeleton), {}), load_json(Path(args.probe), {}), Path(args.out))
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(notes["output"])
    print(Path(args.out).with_suffix(".assemble-notes.json"))
    if not notes["loudness_applied"]:
        print("响度第二遍没有做成，成片还不能指望过响度分。")
    if notes["text_slots"] and not notes["text_burned"]:
        print("字没有烧进画面。graphics 过不了 8。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
