#!/usr/bin/env python3
"""Collect recent high-craft films and craft articles from public feeds."""

from __future__ import annotations

import email.utils
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import http_get, is_fresh, library, load_json, strip_html

ATOM = "http://www.w3.org/2005/Atom"
MEDIA = "http://search.yahoo.com/mrss/"
DROP_TITLE = re.compile(
    r"new look|we'?re hiring|now hiring|box office|net worth|celebrity|gossip|"
    r"official trailer|teaser trailer|reaction video|dating rumor|body-only|firmware update|pre-order|preorder",
    re.I,
)
BOOSTS = (
    "documentary",
    "cinematograph",
    "short film",
    "editing",
    "screenwrit",
    "lighting",
    "sound design",
    "director",
    "纪录",
    "摄影",
    "剪辑",
)
DROPS = ("trailer", "box office", "celebrity", "gossip", "reaction", "net worth", "teaser", "quote")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_date(raw: str) -> Optional[datetime]:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(raw)
        if parsed is not None:
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _rss_items(root: ET.Element, source: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = []
    for node in root.iter():
        if _local(node.tag) != "item":
            continue
        title = ""
        link = ""
        summary = ""
        published = None
        for child in list(node):
            name = _local(child.tag)
            if name == "title":
                title = strip_html("".join(child.itertext()))
            elif name == "link":
                link = (child.text or "").strip()
            elif name in ("description", "summary"):
                summary = strip_html("".join(child.itertext()))
            elif name in ("pubDate", "published", "updated", "date"):
                published = _parse_date("".join(child.itertext()))
        if title and link:
            items.append(_item(source, title, link, summary, published))
    return items


def _atom_items(root: ET.Element, source: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = []
    ns = {"a": ATOM, "m": MEDIA}
    for entry in root.findall("a:entry", ns):
        title = strip_html(" ".join((entry.findtext("a:title", default="", namespaces=ns) or "").split()))
        link = ""
        for node in entry.findall("a:link", ns):
            rel = node.attrib.get("rel", "alternate")
            if rel == "alternate":
                link = node.attrib.get("href", "")
                break
        summary = ""
        media = entry.find("m:group/m:description", ns)
        if media is None:
            media = entry.find("a:summary", ns)
        if media is not None:
            summary = strip_html("".join(media.itertext()))
        published = _parse_date(entry.findtext("a:published", default="", namespaces=ns) or "")
        if not published:
            published = _parse_date(entry.findtext("a:updated", default="", namespaces=ns) or "")
        if title and link:
            items.append(_item(source, title, link, summary, published))
    return items


def _item(source: Dict[str, Any], title: str, link: str, summary: str, published: Optional[datetime]) -> Dict[str, Any]:
    return {
        "source": source["name"],
        "tier": source["tier"],
        "title": title,
        "url": link,
        "summary": summary[:360],
        "published": published,
        "link_contains": source.get("link_contains") or "",
        "undated_keep": int(source.get("undated_keep") or 3),
    }


def fetch_feed(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    payload = http_get(source["url"])
    root = ET.fromstring(payload)
    kind = _local(root.tag)
    if kind == "feed":
        return _atom_items(root, source)
    return _rss_items(root, source)


def _in_window(item: Dict[str, Any], now: datetime, window_days: int) -> Optional[bool]:
    published = item["published"]
    if published is None:
        return None
    age = now - published
    if age < timedelta(days=-1) or age > timedelta(days=window_days):
        return False
    return True


def _score(item: Dict[str, Any], now: datetime) -> int:
    text = f"{item['title']} {item['summary']}".lower()
    score = {"film": 60, "essay": 48, "craft-article": 36}[item["tier"]]
    for word in BOOSTS:
        if word in text:
            score += 6
    for word in DROPS:
        if word in text:
            score -= 30
    if item["published"] is not None:
        age_days = max(0.0, (now - item["published"]).total_seconds() / 86400)
        score += max(0, int(8 - age_days))
    return score


def _line(item: Dict[str, Any]) -> str:
    when = item["published"].date().isoformat() if item["published"] else "日期不详"
    summary = item["summary"] or "（源里没有简介）"
    return (
        f"1. **{item['title']}**（{item['source']}，优先级 {item['score']}）\n"
        f"   - 日期: {when}\n"
        f"   - 链接: {item['url']}\n"
        f"   - 简介: {summary}\n"
        f"   - 状态: 待蒸馏\n"
    )


def collect(seen: Dict[str, Any], day: Any, force: bool = False) -> Tuple[str, List[str]]:
    config = load_json(library() / "sources.json", {})
    window_days = int(config.get("window_days") or 10)
    caps = config.get("caps") or {"film": 8, "essay": 4, "craft-article": 3}
    now = datetime.now(timezone.utc)
    errors: List[str] = []
    seen_urls = set()
    picked: Dict[str, List[Dict[str, Any]]] = {"film": [], "essay": [], "craft-article": []}
    overflow: List[Dict[str, Any]] = []
    keys: List[str] = []

    for source in config.get("feeds") or []:
        try:
            items = fetch_feed(source)
        except (RuntimeError, ET.ParseError, OSError) as exc:
            errors.append(f"- {source.get('name', '未命名源')}: {exc}")
            continue
        undated_kept = 0
        for item in items:
            if DROP_TITLE.search(item["title"]) or "/shorts/" in item["url"]:
                keys.append(item["url"])
                continue
            if item["link_contains"] and item["link_contains"] not in item["url"]:
                continue
            inside = _in_window(item, now, window_days)
            if inside is False:
                continue
            if inside is None:
                if undated_kept >= item["undated_keep"]:
                    keys.append(item["url"])
                    continue
                undated_kept += 1
            if item["url"] in seen_urls or not is_fresh(seen, "videos", item["url"], day, force):
                continue
            seen_urls.add(item["url"])
            item["score"] = _score(item, now)
            if item["score"] < 20:
                keys.append(item["url"])
                continue
            picked[item["tier"]].append(item)

    shown: List[Dict[str, Any]] = []
    for tier, rows in picked.items():
        rows.sort(key=lambda row: row["score"], reverse=True)
        cap = int(caps.get(tier) or 0)
        shown.extend(rows[:cap])
        overflow.extend(rows[cap:])

    def section(title: str, tier: str) -> str:
        rows = [row for row in shown if row["tier"] == tier]
        if not rows:
            return f"## {title}\n\n今天没有新的条目。\n"
        lines = [f"## {title}\n"]
        for index, row in enumerate(rows, start=1):
            lines.append(_line(row).replace("1. ", f"{index}. ", 1))
            keys.append(row["url"])
        return "\n".join(lines)

    for row in overflow:
        keys.append(row["url"])

    parts = [
        section("影片", "film"),
        section("视频论文", "essay"),
        section("工艺文章", "craft-article"),
    ]
    if overflow:
        extra = "\n".join(f"- {row['title']} · {row['url']}" for row in overflow[:12])
        parts.append(f"## 窗口内未展开\n\n{extra}\n")
    if errors:
        parts.append("## 源失败\n\n" + "\n".join(errors) + "\n")
    parts.append(
        "这些是公开页面上的候选。没有本地文件和接触表之前，不能写景别、切点数或调色，也不能当作复刻依据。\n"
    )
    return "\n".join(parts), keys
