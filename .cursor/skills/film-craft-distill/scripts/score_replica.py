#!/usr/bin/env python3
"""Score a replica against a reference. Exit 0 only at 95 or above."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import load_json

DIMENSIONS = ("hook", "structure", "shot_grammar", "sound", "graphics", "finish")
STAMP = __import__("re").compile(r"\d+:\d+|\d+\.\d+")
UPGRADE_WORDS = ("超过", "更好", "比参考", "better")


def _ratio_band(replica: float, reference: float, tight: Tuple[float, float], mid: Tuple[float, float], full: int, partial: int) -> int:
    if reference <= 0 or replica <= 0:
        return 0
    ratio = replica / reference
    if tight[0] <= ratio <= tight[1]:
        return full
    if mid[0] <= ratio <= mid[1]:
        return partial
    return 0


def technical(ref: Dict[str, Any], rep: Dict[str, Any], brief_duration: Optional[float]) -> Tuple[int, List[Tuple[str, int, int, str]]]:
    parts: List[Tuple[str, int, int, str]] = []
    target = brief_duration if brief_duration else float(ref.get("duration") or 0)
    duration_pts = _ratio_band(float(rep.get("duration") or 0), target, (0.92, 1.08), (0.85, 1.15), 6, 3)
    parts.append(("duration", duration_pts, 6, f"成片 {rep.get('duration')} / 目标 {target}"))
    asl_pts = _ratio_band(
        float(rep.get("avg_shot_length") or 0),
        float(ref.get("avg_shot_length") or 0),
        (0.90, 1.10),
        (0.80, 1.20),
        8,
        4,
    )
    parts.append(("avg_shot_length", asl_pts, 8, f"成片 {rep.get('avg_shot_length')} / 参考 {ref.get('avg_shot_length')}"))
    try:
        hook_gap = abs(float(rep.get("first_cut")) - float(ref.get("first_cut")))
    except (TypeError, ValueError):
        hook_gap = 99.0
    hook_pts = 4 if hook_gap <= 0.4 else 2 if hook_gap <= 1.0 else 0
    parts.append(("first_cut", hook_pts, 4, f"第一刀相差 {hook_gap:.2f}s"))

    ref_lufs = ref.get("integrated_lufs")
    rep_lufs = rep.get("integrated_lufs")
    if not ref.get("has_audio") and not rep.get("has_audio"):
        loud_pts, loud_note = 8, "两边都没有声音"
    elif ref_lufs is None or rep_lufs is None:
        loud_pts, loud_note = 0, "缺综合响度"
    else:
        diff = abs(float(rep_lufs) - float(ref_lufs))
        match = 5 if diff <= 1.0 else 3 if diff <= 2.0 else 0
        bonus = 0
        if -16 <= float(rep_lufs) <= -13 or (diff <= 1.0 and float(ref_lufs) < -18):
            bonus = 3
        loud_pts = min(8, match + bonus)
        loud_note = f"相差 {diff:.1f} LU"
    parts.append(("loudness", loud_pts, 8, loud_note))

    def aspect(probe: Dict[str, Any]) -> float:
        width = float(probe.get("width") or 0)
        height = float(probe.get("height") or 0)
        return width / height if width and height else 0.0

    ref_aspect = aspect(ref)
    rep_aspect = aspect(rep)
    if ref_aspect and rep_aspect:
        drift = abs(rep_aspect - ref_aspect) / ref_aspect
        aspect_pts = 4 if drift <= 0.04 else 2 if drift <= 0.08 else 0
    else:
        aspect_pts = 0
    ref_long = max(int(ref.get("width") or 0), int(ref.get("height") or 0))
    rep_long = max(int(rep.get("width") or 0), int(rep.get("height") or 0))
    long_pts = 2 if rep_long >= 1920 or (ref_long and abs(rep_long - ref_long) / ref_long <= 0.05) else 0
    try:
        fps_pts = 2 if abs(float(rep.get("fps")) - float(ref.get("fps"))) <= 1 else 0
    except (TypeError, ValueError):
        fps_pts = 0
    parts.append(("picture", aspect_pts + long_pts + fps_pts, 8, f"画幅 {rep.get('width')}x{rep.get('height')} @ {rep.get('fps')}"))

    black_pts = 2 if float(rep.get("black_seconds") or 0) <= float(ref.get("black_seconds") or 0) + 0.25 else 0
    peak = rep.get("true_peak_dbtp")
    peak_pts = 2 if peak is not None and float(peak) <= -1.0 else 0
    if not rep.get("has_audio") and not ref.get("has_audio"):
        peak_pts = 2
    silence_pts = 2 if float(rep.get("silence_seconds") or 0) <= float(ref.get("silence_seconds") or 0) + 1.0 else 0
    parts.append(("cleanliness", black_pts + peak_pts + silence_pts, 6, f"黑场 {black_pts}/2 峰值 {peak_pts}/2 静音 {silence_pts}/2"))
    return sum(item[1] for item in parts), parts


def grammar_cap(ref: Dict[str, Any], rep: Dict[str, Any]) -> int:
    cap = 10
    for probe in (ref, rep):
        if probe.get("stills_sampled"):
            cap = min(cap, 8)
        elif int(probe.get("still_count") or 0) > 24:
            cap = min(cap, 9)
    return cap


def graphics_cap(notes: Optional[Dict[str, Any]], seen: Optional[Dict[str, Any]]) -> int:
    if notes:
        if int(notes.get("text_slots") or 0) == 0 or notes.get("text_burned"):
            return 10
        return 8
    evidence = str((seen or {}).get("evidence") or "")
    if seen and seen.get("inspected") and STAMP.search(evidence):
        return 10
    return 8


def evaluate(
    ref: Dict[str, Any],
    rep: Dict[str, Any],
    craft: Dict[str, Any],
    notes: Optional[Dict[str, Any]] = None,
    seen: Optional[Dict[str, Any]] = None,
    skeleton: Optional[Dict[str, Any]] = None,
    brief_duration: Optional[float] = None,
) -> Dict[str, Any]:
    messages: List[str] = []
    tech, parts = technical(ref, rep, brief_duration)
    scores: Dict[str, int] = {}
    evidence = craft.get("evidence") or {}
    for name in DIMENSIONS:
        try:
            scores[name] = int(craft[name])
        except (KeyError, TypeError, ValueError):
            messages.append(f"缺少 {name} 的整数分。")
            scores[name] = 0
        if not 0 <= scores[name] <= 10:
            messages.append(f"{name} 必须在 0 到 10。")
            scores[name] = max(0, min(10, scores[name]))
        proof = str(evidence.get(name) or "")
        if len(proof) < 8 or not STAMP.search(proof):
            messages.append(f"{name} 的 evidence 需要时间码和一句画面证据。")
    gcap = grammar_cap(ref, rep)
    if scores["shot_grammar"] > gcap:
        messages.append(f"shot_grammar {scores['shot_grammar']} 被压到 {gcap}。接触表没有覆盖每一刀。")
        scores["shot_grammar"] = gcap
    xcap = graphics_cap(notes, seen)
    if scores["graphics"] > xcap:
        messages.append(f"graphics {scores['graphics']} 被压到 {xcap}。字幕或图形没有被确认在画面里。")
        scores["graphics"] = xcap
    upgrade = str(craft.get("upgrade") or "")
    dimension = str(craft.get("upgrade_dimension") or "")
    if dimension not in DIMENSIONS:
        messages.append("upgrade_dimension 不在六个维度里。")
    elif scores[dimension] < 9:
        messages.append(f"要超过参考片的 {dimension} 只有 {scores[dimension]}，至少要 9。")
    if not any(word in upgrade.lower() for word in UPGRADE_WORDS):
        messages.append("upgrade 要写明哪里比参考更好。")
    if skeleton and str(skeleton.get("upgrade_dimension") or "") != dimension:
        messages.append("导演骨架和分数卡的超过维度不一致。")
    if ref.get("reel") != rep.get("reel"):
        messages.append("参考和成片不是同一盘。长片要一对一按盘打分。")
    coverage_ok = ref.get("coverage") == "full" and rep.get("coverage") == "full"
    if not coverage_ok:
        messages.append("测量不完整。这版没有成片分。")
    craft_total = sum(scores.values())
    total = tech + craft_total
    floors = all(scores[name] >= 8 for name in DIMENSIONS)
    passed = bool(coverage_ok and tech >= 36 and floors and total >= 95 and not messages)
    if total < 80:
        verdict = "废片。推倒重做：先检查类型判断和节奏骨架，不要在这版上补字幕。"
    elif not passed:
        verdict = "半成品。只改最低的两项，重新导出后再打分。这版不能交付。"
    elif any(value == 8 for value in scores.values()):
        verdict = "过线。还有一项是 8，再针对性改一轮，然后停。这句话只执行一次。"
    else:
        verdict = "过线。可以交付。"
    gaps = []
    for name, pts, full, _note in parts:
        gaps.append((full - pts, f"技术:{name}", pts, full))
    for name, pts in scores.items():
        gaps.append((10 - pts, f"工艺:{name}", pts, 10))
    gaps.sort(key=lambda item: (-item[0], item[1]))
    return {
        "technical": tech,
        "craft": craft_total,
        "total": total,
        "scores": scores,
        "parts": parts,
        "passed": passed,
        "verdict": verdict,
        "messages": messages,
        "gaps": [item for item in gaps if item[0] > 0][:2],
    }


def render(result: Dict[str, Any]) -> str:
    lines = [
        f"技术 {result['technical']}/40",
        f"工艺 {result['craft']}/60",
        f"总分 {result['total']}/100",
        result["verdict"],
        "",
    ]
    for name, pts, full, note in result["parts"]:
        lines.append(f"- {name}: {pts}/{full} {note}")
    lines.append("")
    for name, pts in result["scores"].items():
        lines.append(f"- {name}: {pts}/10")
    if result["gaps"] and not result["passed"]:
        lines.append("")
        lines.append("先改这两项:")
        for _deficit, name, pts, full in result["gaps"]:
            lines.append(f"- {name} {pts}/{full}")
    if result["messages"]:
        lines.append("")
        for message in result["messages"]:
            lines.append(f"- {message}")
    return "\n".join(lines)


def _probe(duration: float = 30.0, lufs: float = -14.0, sampled: bool = False, stills: int = 12) -> Dict[str, Any]:
    return {
        "coverage": "full",
        "stills_sampled": sampled,
        "still_count": stills,
        "has_audio": True,
        "duration": duration,
        "width": 1920,
        "height": 1080,
        "fps": 24,
        "avg_shot_length": 2.5,
        "first_cut": 1.2,
        "integrated_lufs": lufs,
        "true_peak_dbtp": -1.5,
        "black_seconds": 0,
        "silence_seconds": 0.4,
        "reel": None,
    }


def _craft(scores: Dict[str, int], dimension: str = "sound") -> Dict[str, Any]:
    return {
        **scores,
        "upgrade": "声音比参考更好：0:04 房间声一直在，参考片用音乐盖住了口型",
        "upgrade_dimension": dimension,
        "evidence": {name: f"0:{index:02d} 这一刀能在画面里指出来" for index, name in enumerate(DIMENSIONS, start=1)},
    }


def _self_test() -> int:
    ref = _probe()
    rep = _probe()
    notes = {"text_slots": 1, "text_burned": True}
    almost = evaluate(ref, rep, _craft({name: 9 for name in DIMENSIONS}), notes)
    if almost["total"] != 94 or almost["passed"]:
        print(f"self-test failed: all nines should be 94 unfinished, got {almost['total']} {almost['passed']}", file=sys.stderr)
        return 1
    scores = {name: 9 for name in DIMENSIONS}
    scores["sound"] = 10
    passed = evaluate(ref, rep, _craft(scores), notes)
    if passed["total"] != 95 or not passed["passed"]:
        print(f"self-test failed: 95 should pass, got {passed['total']} {passed['passed']} {passed['messages']}", file=sys.stderr)
        return 1
    scores["hook"] = 7
    low = evaluate(ref, rep, _craft(scores, "sound"), notes)
    if low["passed"] or "废片" in low["verdict"]:
        print("self-test failed: a 7 should be unfinished, not scrap or pass", file=sys.stderr)
        return 1
    scrap = evaluate(ref, _probe(duration=12, lufs=-28), _craft({name: 6 for name in DIMENSIONS}), notes)
    if "废片" not in scrap["verdict"]:
        print(f"self-test failed: expected scrap, got {scrap['total']} {scrap['verdict']}", file=sys.stderr)
        return 1
    bare = evaluate(ref, rep, _craft({name: 10 for name in DIMENSIONS}))
    if bare["scores"]["graphics"] != 8 or bare["passed"]:
        print("self-test failed: missing graphics proof should clamp and fail", file=sys.stderr)
        return 1
    print("score_replica self-test ok")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="给复刻成片打分")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--reference")
    parser.add_argument("--replica")
    parser.add_argument("--craft")
    parser.add_argument("--notes")
    parser.add_argument("--graphics-seen")
    parser.add_argument("--skeleton")
    parser.add_argument("--brief-duration", type=float)
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    if not args.reference or not args.replica or not args.craft:
        print("需要 --reference --replica --craft。", file=sys.stderr)
        return 1
    result = evaluate(
        load_json(Path(args.reference), {}),
        load_json(Path(args.replica), {}),
        load_json(Path(args.craft), {}),
        load_json(Path(args.notes), {}) if args.notes else None,
        load_json(Path(args.graphics_seen), {}) if args.graphics_seen else None,
        load_json(Path(args.skeleton), {}) if args.skeleton else None,
        args.brief_duration,
    )
    print(render(result))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
