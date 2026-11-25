#!/usr/bin/env python3
"""Check a director skeleton before anyone exports a replica."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import load_json

DIMENSIONS = ("hook", "structure", "shot_grammar", "sound", "graphics", "finish")
BANNED = (
    "同画面",
    "用原片",
    "原片画面",
    "直接用参考",
    "搬运原片",
    "把参考片放进去",
    "same frame",
    "same footage",
    "use the original",
)
PLACEHOLDER = ("待补", "之后再补", "tbd", "todo")
UPGRADE_WORDS = ("超过", "更好", "比参考", "better")


def validate(skeleton: Dict[str, Any], probe: Dict[str, Any], stage: str) -> List[str]:
    errors: List[str] = []
    upgrade = str(skeleton.get("upgrade") or "").strip()
    dimension = str(skeleton.get("upgrade_dimension") or "").strip()
    if len(upgrade) < 8 or not any(word in upgrade.lower() for word in UPGRADE_WORDS):
        errors.append("upgrade 要写明比参考片更好的一点，并包含「超过」「更好」或「比参考」。")
    if dimension not in DIMENSIONS:
        errors.append("upgrade_dimension 必须是 hook、structure、shot_grammar、sound、graphics、finish 之一。")
    slots = skeleton.get("slots") or []
    expected = probe.get("shot_durations") or []
    if len(slots) != len(expected):
        errors.append(f"槽位 {len(slots)} 个，参考片镜头 {len(expected)} 个。不能删镜头。")
    placeholder_hits = 0
    for slot, dur in zip(slots, expected):
        index = slot.get("index")
        if abs(float(slot.get("dur", -1)) - float(dur)) > 0.12 and not str(slot.get("deviation") or "").strip():
            errors.append(f"槽位 {index} 的时长改了，但没有 deviation。先按参考片节奏做。")
        picture = str(slot.get("picture") or "").strip()
        function = str(slot.get("function") or "").strip()
        sound = str(slot.get("sound") or "").strip()
        if len(function) < 8:
            errors.append(f"槽位 {index} 的 function 太短。写这个镜头要完成的事。")
        if len(picture) < 12:
            errors.append(f"槽位 {index} 的 picture 太短。写能拍到的动作和物件。")
        if len(sound) < 4:
            errors.append(f"槽位 {index} 的 sound 太短。写这一刀听见什么。")
        blob = f"{picture} {function}".lower()
        if any(term in blob for term in BANNED):
            errors.append(f"槽位 {index} 在复用参考片画面。换成新的物件和动作。")
        if any(term in picture.lower() for term in PLACEHOLDER):
            placeholder_hits += 1
        if stage == "assemble":
            source = str(slot.get("source") or "").strip()
            if not source or not Path(source).exists():
                errors.append(f"槽位 {index} 没有可用素材: {picture}")
            try:
                if float(slot.get("in", -1)) < 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(f"槽位 {index} 的 in 必须是大于等于 0 的秒数。")
    if slots and placeholder_hits / len(slots) > 0.2:
        errors.append("超过两成的槽位还在待补素材。先改剧本，让现有素材能演完。")
    cursor = 0.0
    for slot, dur in zip(slots, expected):
        try:
            start = float(slot.get("t"))
        except (TypeError, ValueError):
            errors.append(f"槽位 {slot.get('index')} 没有时间。")
            continue
        if abs(start - cursor) > 0.12:
            errors.append(f"槽位 {slot.get('index')} 的起点是 {start}，骨架上应该是 {cursor}。")
        step = float(slot.get("dur") or dur)
        cursor = round(cursor + step, 3)
    return errors


def _self_test() -> int:
    probe = {"shot_durations": [1.2, 1.8]}
    good = {
        "upgrade": "声音比参考更好：0:01 先听到瓶盖，参考片这里先出了音乐",
        "upgrade_dimension": "sound",
        "slots": [
            {
                "index": 0, "t": 0.0, "dur": 1.2,
                "function": "用一个失败的动作把人留住",
                "picture": "清晨有人第三次没拧开瓶盖，水槽是冷的",
                "sound": "只有齿音",
                "source": "", "in": 0,
            },
            {
                "index": 1, "t": 1.2, "dur": 1.8,
                "function": "让失败变成一个选择",
                "picture": "他把第二只杯子扣回沥水架",
                "sound": "杯子碰铁丝",
                "source": "", "in": 0,
            },
        ],
    }
    if validate(good, probe, "plan"):
        print("self-test failed: good plan was rejected", file=sys.stderr)
        print(validate(good, probe, "plan"), file=sys.stderr)
        return 1
    stolen = json.loads(json.dumps(good))
    stolen["slots"][0]["picture"] = "用原片这段城市航拍当作开场画面"
    if not any("复用参考片" in item for item in validate(stolen, probe, "plan")):
        print("self-test failed: stolen picture passed", file=sys.stderr)
        return 1
    print("check_plan self-test ok")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="检查导演骨架")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--skeleton")
    parser.add_argument("--probe")
    parser.add_argument("--stage", choices=("plan", "assemble"), default="plan")
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    if not args.skeleton or not args.probe:
        print("需要 --skeleton 和 --probe。", file=sys.stderr)
        return 1
    skeleton = load_json(Path(args.skeleton), {})
    probe = load_json(Path(args.probe), {})
    errors = validate(skeleton, probe, args.stage)
    if errors:
        print(f"{args.stage} 没过，还不能导出。")
        for error in errors:
            print(f"- {error}")
        return 2
    print(f"{args.stage} 通过。槽位 {len(skeleton.get('slots') or [])} 个。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
