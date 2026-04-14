#!/usr/bin/env python3
"""Generate usable SVG draft pages from task markdown files.

This is a deterministic draft renderer for the WorkBuddy ppt-master wrapper.
It turns per-slide task files into structured SVG pages using a few stable layouts.
The output is not intended to be final design polish; it is a production-friendly
starting point that can later be refined by an agent or designer.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

VIEWBOXES = {
    "ppt169": (1280, 720),
    "ppt43": (1024, 768),
    "xhs": (1242, 1660),
    "square": (1080, 1080),
    "story": (1080, 1920),
    "wechat-cover": (900, 383),
    "a4": (1240, 1754),
}

PALETTES = {
    "default": {
        "bg": "#F7F8FA",
        "panel": "#FFFFFF",
        "text": "#0F172A",
        "muted": "#475569",
        "accent": "#2563EB",
        "accent_soft": "#DBEAFE",
        "line": "#E2E8F0",
    },
    "dark": {
        "bg": "#0F172A",
        "panel": "#111827",
        "text": "#F8FAFC",
        "muted": "#CBD5E1",
        "accent": "#38BDF8",
        "accent_soft": "#082F49",
        "line": "#334155",
    },
    "tech-blue": {
        "bg": "#F4F8FF",
        "panel": "#FFFFFF",
        "text": "#0B1F3A",
        "muted": "#4A5D7A",
        "accent": "#2563EB",
        "accent_soft": "#DCEAFE",
        "line": "#C7D7F2",
    },
    "business-dark": {
        "bg": "#0B1020",
        "panel": "#121A2B",
        "text": "#F3F6FB",
        "muted": "#B8C2D8",
        "accent": "#60A5FA",
        "accent_soft": "#172554",
        "line": "#2A3753",
    },
    "brand-light": {
        "bg": "#FFF9F5",
        "panel": "#FFFFFF",
        "text": "#3A2230",
        "muted": "#7A5C68",
        "accent": "#EC4899",
        "accent_soft": "#FCE7F3",
        "line": "#F3D4E4",
    },
    "consulting": {
        "bg": "#F7F6F2",
        "panel": "#FFFEFC",
        "text": "#172033",
        "muted": "#5B6472",
        "accent": "#0F766E",
        "accent_soft": "#DFF5F2",
        "line": "#D6D9DE",
    },
}



def resolve_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def read_text(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"文件不存在: {path}")
    return path.read_text(encoding="utf-8")


def parse_viewbox(value: str) -> Tuple[int, int]:
    parts = [p for p in value.strip().split() if p]
    if len(parts) != 4:
        raise SystemExit(f"非法 viewBox: {value}")
    try:
        return int(float(parts[2])), int(float(parts[3]))
    except ValueError as exc:
        raise SystemExit(f"无法解析 viewBox: {value}") from exc


def detect_dimensions(project_path: Path, explicit_format: str | None, explicit_viewbox: str | None) -> Tuple[str, int, int]:
    if explicit_viewbox:
        width, height = parse_viewbox(explicit_viewbox)
        return explicit_format or "custom", width, height
    if explicit_format and explicit_format in VIEWBOXES:
        width, height = VIEWBOXES[explicit_format]
        return explicit_format, width, height

    spec_path = project_path / "design_spec.md"
    if spec_path.exists():
        content = spec_path.read_text(encoding="utf-8")
        fmt_match = re.search(r"-\s*Format:\s*([A-Za-z0-9\-]+)", content)
        vb_match = re.search(r"-\s*ViewBox:\s*([0-9\.\s]+)", content)
        if vb_match:
            width, height = parse_viewbox(vb_match.group(1))
            return fmt_match.group(1) if fmt_match else "custom", width, height
        if fmt_match and fmt_match.group(1) in VIEWBOXES:
            width, height = VIEWBOXES[fmt_match.group(1)]
            return fmt_match.group(1), width, height

    width, height = VIEWBOXES["ppt169"]
    return explicit_format or "ppt169", width, height


def extract_heading_value(content: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(content)
    if not match:
        return "待补充"
    start = match.end()
    next_heading = re.search(r"^##\s+", content[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(content)
    value = content[start:end].strip()
    return value or "待补充"


def infer_layout(layout_text: str, visual_text: str, title: str, objective: str = "", message: str = "", support: str = "") -> str:
    text = f"{layout_text} {visual_text} {title} {objective} {message} {support}".lower()
    message_lines = split_lines(message)
    support_lines = split_lines(support)
    total_lines = len(message_lines) + len(support_lines)

    if any(key in text for key in ["cover", "封面", "开场", "title slide"]):
        return "cover"
    if any(key in text for key in ["section", "divider", "章节页", "分隔页"]):
        return "section-divider"
    if any(key in text for key in ["quote", "引言", "引用", "金句"]):
        return "quote"
    if any(key in text for key in ["kpi", "dashboard", "scorecard", "指标卡", "数据卡"]):
        return "kpi-grid"
    if any(key in text for key in ["process", "workflow", "步骤", "流程"]):
        return "process"
    if any(key in text for key in ["matrix", "2x2", "象限", "矩阵"]):
        return "matrix"
    if any(key in text for key in ["table", "tabular", "表格"]):
        return "table-lite"
    if any(key in text for key in ["timeline", "时间线", "里程碑"]):
        return "timeline"
    if any(key in text for key in ["compare", "comparison", "对比", "before / after", "before-after"]):
        return "comparison"
    if any(key in text for key in ["data", "metric", "数字", "指标", "图表", "chart"]):
        return "data-highlight"
    if any(key in text for key in ["hero", "主视觉"]):
        return "hero"
    if any(key in text for key in ["two-column", "双栏", "左右"]):
        return "two-column"
    if any(key in text for key in ["对比优势", "核心差异", "before", "after"]) and total_lines >= 4:
        return "comparison"
    if any(key in text for key in ["增长", "收入", "roi", "%", "亿元", "万", "同比"]) and total_lines <= 5:
        return "data-highlight"
    if total_lines >= 7:
        return "two-column"
    if len(message_lines) <= 1 and len((message or title).strip()) <= 36:
        return "hero"
    return "title-bullets"



def compress_text(text: str, max_chars: int = 84) -> str:
    cleaned = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    cleaned = re.sub(r"^[\-•\*\d\.\)\(\s]+", "", cleaned)
    if len(cleaned) <= max_chars:
        return cleaned
    chunks = [chunk.strip() for chunk in re.split(r"[；;，,。.!！?？:：]", cleaned) if chunk.strip()]
    if not chunks:
        return cleaned[: max_chars - 1].rstrip() + "…"
    compact = chunks[0]
    for chunk in chunks[1:]:
        candidate = f"{compact}，{chunk}"
        if len(candidate) > max_chars:
            break
        compact = candidate
    if len(compact) < len(cleaned):
        compact = compact.rstrip("，,;；") + "…"
    return compact


def rewrite_title(text: str, max_chars: int = 24) -> str:
    title = compress_text(text or "未命名页面", max_chars + 12)
    title = re.sub(r"^(关于|围绕|针对|基于)", "", title).strip()
    title = re.sub(r"(的情况|的分析|的说明|的介绍)$", "", title).strip()
    if len(title) <= max_chars:
        return title
    parts = [part.strip() for part in re.split(r"[：:，,。；;|-]", title) if part.strip()]
    if parts:
        best = max(parts, key=len)
        return compress_text(best, max_chars)
    return compress_text(title, max_chars)


def rewrite_bullet(text: str, max_chars: int = 26) -> str:
    sentence = compress_text(text, max_chars + 20)
    sentence = re.sub(r"^(我们|需要|可以|应该|当前|通过)", "", sentence).strip()
    sentence = re.sub(r"(这一点|这一页|这个部分)", "", sentence).strip()
    return compress_text(sentence, max_chars)


def extract_takeaway(title: str, objective: str, message: str, support: str) -> str:
    candidates = split_lines("\n".join([objective, message, support]), max_items=6, item_chars=40)
    if candidates:
        lead = candidates[0]
        if len(lead) < 10 and len(candidates) > 1:
            lead = f"{lead}：{candidates[1]}"
        return compress_text(lead, 28)
    return compress_text(objective or title, 28)


def rewrite_objective(text: str, max_chars: int = 34) -> str:
    objective = compress_text(text, max_chars + 18)
    objective = re.sub(r"^(本页目标|目标|这一页要说明|本页说明)[:：\s]*", "", objective).strip()
    objective = re.sub(r"(即可|为主|展开说明)$", "", objective).strip()
    return compress_text(objective, max_chars)


def build_subtitle(title: str, objective: str, message: str) -> str:
    objective_line = rewrite_objective(objective, 30)
    if objective_line and objective_line != "待补充":
        return objective_line
    message_lines = split_lines(message, max_items=3, item_chars=28)
    if message_lines:
        return compress_text(message_lines[0], 30)
    return compress_text(title, 30)


def build_supporting_bullets(layout: str, objective: str, message: str, support: str, notes: str = "", max_items: int = 4) -> List[str]:
    preferred: List[str] = []
    evidence: List[str] = []
    seen = set()
    for source in [message, support, objective, notes]:
        for line in split_lines(source, max_items=10, item_chars=48):
            bullet = rewrite_bullet(line, 28)
            if not bullet or bullet in seen:
                continue
            seen.add(bullet)
            if re.search(r"\d|%|同比|增长|下降|提升|减少|ROI|留存|转化|亿元|万|mau|dau|arpu|gmv", bullet, re.IGNORECASE):
                preferred.append(bullet)
            else:
                evidence.append(bullet)

    merged = preferred + evidence
    if layout == "comparison":
        left = [item for item in merged if re.search(r"before|旧|传统|方案a|a端|现状|问题|劣势", item, re.IGNORECASE)]
        right = [item for item in merged if re.search(r"after|新|优化|方案b|b端|目标|优势|改进", item, re.IGNORECASE)]
        rest = [item for item in merged if item not in left and item not in right]
        merged = (left[:2] + right[:2] + rest)[:max_items]
    elif layout == "timeline":
        staged = []
        for idx, item in enumerate(merged[:max_items], start=1):
            if re.search(r"^(q\d|第.?阶段|阶段|step|milestone|里程碑|m\d)", item, re.IGNORECASE):
                staged.append(item)
            else:
                staged.append(f"阶段{idx}：{compress_text(item, 22)}")
        merged = staged[:max_items]
    elif layout == "process":
        process_items = []
        for idx, item in enumerate(merged[:max_items], start=1):
            short = compress_text(item, 20)
            if re.search(r"^(step|步骤|阶段)\s*\d+", short, re.IGNORECASE):
                process_items.append(short)
            else:
                process_items.append(f"步骤{idx}：{short}")
        merged = process_items[:max_items]
    elif layout == "kpi-grid":
        metrics = []
        for item in merged:
            match = re.search(r"([A-Za-z]{2,8}|\d+(?:\.\d+)?%|\d+(?:\.\d+)?[亿万元]*)", item)
            if match:
                metrics.append(compress_text(item, 18))
        merged = (metrics or merged)[:max_items]
    elif layout == "matrix":
        quadrants = ["高影响高可行", "高影响低可行", "低影响高可行", "低影响低可行"]
        matrix_items = []
        for idx, item in enumerate(merged[:4]):
            if re.search(r"高|低|象限|quadrant", item, re.IGNORECASE):
                matrix_items.append(compress_text(item, 18))
            else:
                matrix_items.append(f"{quadrants[idx]}：{compress_text(item, 12)}")
        merged = matrix_items[:max_items]
    elif layout == "table-lite":
        rows = []
        for item in merged[:max_items]:
            if "|" in item:
                rows.append(item)
            else:
                parts = re.split(r"[:：,，]\s*", item, maxsplit=2)
                if len(parts) >= 3:
                    rows.append(" | ".join(part.strip() or "待补充" for part in parts[:3]))
                elif len(parts) == 2:
                    rows.append(f"{parts[0].strip()} | {parts[1].strip()} | 待补充")
                else:
                    rows.append(f"{compress_text(item, 10)} | 结果待补充 | 备注待补充")
        merged = rows[:max_items]
    return merged[:max_items]


def build_layout_payload(layout: str, message_lines: List[str], support_lines: List[str]) -> Dict[str, object]:
    payload: Dict[str, object] = {}
    if layout == "comparison":
        combined = message_lines + support_lines
        left = [item for item in combined if re.search(r"before|旧|传统|方案a|a端|现状|问题|劣势", item, re.IGNORECASE)]
        right = [item for item in combined if re.search(r"after|新|优化|方案b|b端|目标|优势|改进", item, re.IGNORECASE)]
        rest = [item for item in combined if item not in left and item not in right]
        while len(left) < 2 and rest:
            left.append(rest.pop(0))
        while len(right) < 2 and rest:
            right.append(rest.pop(0))
        payload["left_title"] = "现状 / Before" if left else "维度 A"
        payload["right_title"] = "目标 / After" if right else "维度 B"
        payload["left_items"] = left[:3] or message_lines[:2]
        payload["right_items"] = right[:3] or support_lines[:2] or rest[:2]
    elif layout == "timeline":
        payload["stages"] = (message_lines or support_lines)[:5]
    elif layout == "process":
        payload["steps"] = (message_lines or support_lines)[:5]
    elif layout == "kpi-grid":
        kpis = []
        for item in (message_lines + support_lines)[:6]:
            metric_match = re.search(r"(\d+(?:\.\d+)?%|\d+(?:\.\d+)?[亿万元]?)", item)
            label = item
            value = metric_match.group(1) if metric_match else f"KPI {len(kpis) + 1:02d}"
            if metric_match:
                label = compress_text(item.replace(metric_match.group(1), "").strip("：:，, ") or item, 16)
            kpis.append({"label": label or f"KPI {len(kpis) + 1:02d}", "value": value, "note": compress_text(item, 22)})
        payload["kpis"] = kpis[:4]
    elif layout == "matrix":
        quadrants = ["高影响高可行", "高影响低可行", "低影响高可行", "低影响低可行"]
        items = []
        for idx, item in enumerate((message_lines or support_lines)[:4]):
            label = quadrants[idx]
            detail = item
            if "：" in item or ":" in item:
                parts = re.split(r"[:：]", item, maxsplit=1)
                label = compress_text(parts[0], 12)
                detail = parts[1].strip() if len(parts) > 1 else item
            items.append({"quadrant": label, "detail": compress_text(detail, 14)})
        payload["quadrants"] = items
    elif layout == "table-lite":
        rows = []
        for item in (message_lines or support_lines)[:5]:
            cells = [cell.strip() for cell in item.split("|")]
            while len(cells) < 3:
                cells.append("待补充")
            rows.append(cells[:3])
        payload["rows"] = rows
    return payload


def split_lines(text: str, max_items: int = 8, item_chars: int = 84) -> List[str]:




    lines: List[str] = []
    for raw in text.splitlines():
        stripped = raw.strip().lstrip("-*0123456789. )(").strip()
        if stripped:
            lines.append(compress_text(stripped, item_chars))
    if not lines and text.strip():
        chunks = [chunk.strip() for chunk in re.split(r"[；;。\n]", text) if chunk.strip()]
        lines.extend(compress_text(chunk, item_chars) for chunk in chunks)
    deduped: List[str] = []
    for line in lines:
        if line and line not in deduped:
            deduped.append(line)
    return deduped[:max_items]


def wrap_text(text: str, max_chars: int, max_lines: int = 8) -> List[str]:
    source = compress_text(text, max(max_chars * max_lines, max_chars)).strip()
    if not source:
        return []
    parts = re.split(r"(?<=[，。；：,.;:!?])", source)
    lines: List[str] = []
    current = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        candidate = f"{current}{part}"
        if current and len(candidate) > max_chars:
            lines.append(current.strip())
            current = part
        elif not current and len(part) > max_chars:
            for i in range(0, len(part), max_chars):
                lines.append(part[i : i + max_chars])
            current = ""
        else:
            current = candidate
    if current.strip():
        lines.append(current.strip())
    return lines[:max_lines]



def esc(text: str) -> str:
    return html.escape(text, quote=True)


def text_block(x: int, y: int, lines: List[str], size: int, fill: str, weight: int = 400, line_gap: int | None = None) -> str:
    if not lines:
        return ""
    gap = line_gap or int(size * 1.45)
    tspans = []
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else gap
        tspans.append(f'<tspan x="{x}" dy="{dy}">{esc(line)}</tspan>')
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" font-family="Arial, PingFang SC, Microsoft YaHei, sans-serif">{"".join(tspans)}</text>'


def bullet_list(x: int, y: int, items: List[str], size: int, fill: str, bullet_fill: str, width: int) -> str:
    if not items:
        return ""
    parts: List[str] = []
    cursor_y = y
    for item in items[:5]:
        wrapped = wrap_text(item, max(16, width // max(size, 1) // 2))
        if not wrapped:
            continue
        parts.append(f'<circle cx="{x}" cy="{cursor_y - 7}" r="5" fill="{bullet_fill}"/>')
        parts.append(text_block(x + 18, cursor_y, wrapped, size, fill, 400, int(size * 1.5)))
        cursor_y += max(44, int(size * 1.6) * len(wrapped) + 14)
    return "".join(parts)


def card(x: int, y: int, width: int, height: int, radius: int, fill: str, stroke: str) -> str:
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def render_title_bullets(meta: Dict[str, str], width: int, height: int, palette: Dict[str, str]) -> str:
    margin = 64
    title = text_block(margin, 110, wrap_text(meta["title"], 18), 34, palette["text"], 700, 42)
    subtitle = text_block(margin, 180, wrap_text(meta["objective"], 34), 18, palette["muted"], 400, 28)
    body_card_y = 230
    body_height = height - body_card_y - 60
    left_w = int(width * 0.58)
    right_x = margin + left_w + 28
    right_w = width - right_x - margin
    bullets = bullet_list(margin + 28, body_card_y + 56, split_lines(meta["message"]), 22, palette["text"], palette["accent"], left_w - 60)
    support = text_block(right_x + 24, body_card_y + 60, ["Supporting Material"] + wrap_text(meta["support"], 18), 18, palette["text"], 600, 28)
    visual = text_block(right_x + 24, body_card_y + 200, ["Visual Guidance"] + wrap_text(meta["visual"], 18), 18, palette["text"], 600, 28)
    notes = text_block(right_x + 24, body_card_y + 340, ["Speaker Seed"] + wrap_text(meta["notes"], 18), 16, palette["muted"], 500, 24)
    return "".join([
        title,
        subtitle,
        card(margin, body_card_y, left_w, body_height, 24, palette["panel"], palette["line"]),
        card(right_x, body_card_y, right_w, body_height, 24, palette["panel"], palette["line"]),
        bullets,
        support,
        visual,
        notes,
    ])


def render_two_column(meta: Dict[str, str], width: int, height: int, palette: Dict[str, str]) -> str:
    margin = 60
    col_gap = 28
    col_w = (width - margin * 2 - col_gap) // 2
    top = 86
    left_x = margin
    right_x = margin + col_w + col_gap
    title = text_block(margin, top, wrap_text(meta["title"], 18), 34, palette["text"], 700, 42)
    left_y = 170
    left_card_h = height - left_y - 60
    right_card_h = left_card_h
    left_inner = bullet_list(left_x + 28, left_y + 70, split_lines(meta["message"]), 21, palette["text"], palette["accent"], col_w - 56)
    right_top = text_block(right_x + 24, left_y + 62, ["Support"] + wrap_text(meta["support"], 18), 18, palette["text"], 600, 28)
    right_mid = text_block(right_x + 24, left_y + 230, ["Layout"] + wrap_text(meta["layout"], 18), 18, palette["text"], 600, 28)
    right_bottom = text_block(right_x + 24, left_y + 390, ["Visual"] + wrap_text(meta["visual"], 18), 16, palette["muted"], 500, 24)
    return "".join([
        title,
        card(left_x, left_y, col_w, left_card_h, 24, palette["panel"], palette["line"]),
        card(right_x, left_y, col_w, right_card_h, 24, palette["panel"], palette["line"]),
        text_block(left_x + 28, left_y + 34, ["Core Message"], 18, palette["text"], 600, 24),
        left_inner,
        right_top,
        right_mid,
        right_bottom,
    ])


def render_hero(meta: Dict[str, str], width: int, height: int, palette: Dict[str, str]) -> str:
    style = get_theme_style(palette)
    margin = 64
    hero_h = int(height * 0.55)
    title = text_block(margin, 150, wrap_text(meta["title"], 16), 46, palette["text"], 700, 56)
    objective = text_block(margin, 290, wrap_text(meta["objective"], 30), 22, palette["muted"], 400, 32)
    message_card = card(margin, 360, width - margin * 2, 108, 26, str(style["hero_message_fill"]), str(style["hero_message_stroke"]))
    message_lines = wrap_text(meta["message"], 42)[:3]
    message = text_block(margin + 28, 408, message_lines, 24, palette["text"], 600, 34)
    footer_y = hero_h + 40
    card_w = (width - margin * 2 - 24) // 2
    support_card = card(margin, footer_y, card_w, height - footer_y - 48, 24, str(style["hero_support_fill"]), palette["line"])
    visual_card = card(margin + card_w + 24, footer_y, card_w, height - footer_y - 48, 24, str(style["hero_visual_fill"]), str(style["hero_visual_stroke"]))
    support = text_block(margin + 24, footer_y + 48, ["Support"] + wrap_text(meta["support"], 20), 18, palette["text"], 600, 28)
    visual = text_block(margin + card_w + 48, footer_y + 48, ["Visual Cue"] + wrap_text(meta["visual"], 20), 18, palette["text"], 600, 28)
    kicker = text_block(margin, 108, [resolve_theme_variant(palette).replace("-", " ").title()], 15, str(style["hero_kicker"]), 700, 18)
    accent_panel = f'<rect x="0" y="0" width="{width}" height="{hero_h}" fill="{style["hero_band_fill"]}" opacity="{style["hero_band_opacity"]}"/>'
    return "".join([accent_panel, kicker, title, objective, message_card, message, support_card, visual_card, support, visual])



def render_data_highlight(meta: Dict[str, str], width: int, height: int, palette: Dict[str, str]) -> str:
    style = get_theme_style(palette)
    margin = 60
    title = text_block(margin, 96, wrap_text(meta["title"], 18), 34, palette["text"], 700, 42)
    objective = text_block(margin, 154, wrap_text(meta["objective"], 34), 18, palette["muted"], 400, 28)
    metric_card = card(margin, 220, int(width * 0.36), int(height * 0.42), 28, str(style["data_metric_fill"]), str(style["data_metric_stroke"]))
    bullets_card = card(int(width * 0.42), 220, width - int(width * 0.42) - margin, int(height * 0.42), 28, palette["panel"], palette["line"])
    metric_lines = split_lines(meta["message"])
    hero_metric = metric_lines[0] if metric_lines else meta["message"]
    metric_label = text_block(margin + 32, 276, [resolve_theme_variant(palette).replace("-", " ").title()], 16, str(style["data_metric_label"]), 700, 20)
    metric = text_block(margin + 32, 348, wrap_text(hero_metric, 10), 54, str(style["data_metric_value"]), 700, 58)
    support = bullet_list(int(width * 0.42) + 28, 286, split_lines(meta["support"] + "\n" + meta["message"]), 21, palette["text"], palette["accent"], width - int(width * 0.42) - margin - 56)
    bottom_card = card(margin, int(height * 0.7), width - margin * 2, height - int(height * 0.7) - 42, 24, str(style["data_bottom_fill"]), str(style["data_bottom_stroke"]))
    layout_text = text_block(margin + 24, int(height * 0.7) + 44, ["Layout + Visual Guidance"] + wrap_text(meta["layout"] + "；" + meta["visual"], 48), 18, palette["text"], 600, 28)
    return "".join([title, objective, metric_card, bullets_card, metric_label, metric, support, bottom_card, layout_text])



def render_timeline(meta: Dict[str, str], width: int, height: int, palette: Dict[str, str]) -> str:
    margin = 60
    title = text_block(margin, 92, wrap_text(meta["title"], 18), 34, palette["text"], 700, 42)
    objective = text_block(margin, 148, wrap_text(meta["objective"], 36), 18, palette["muted"], 400, 28)
    items = list(meta.get("stages", [])) or split_lines(meta["message"] or meta["support"])
    if len(items) < 3:
        items.extend(split_lines(meta["support"]))
    items = items[:5] or ["阶段一", "阶段二", "阶段三"]

    y_line = int(height * 0.45)
    usable_w = width - margin * 2
    step = usable_w // max(1, len(items) - 1) if len(items) > 1 else usable_w
    line = f'<line x1="{margin}" y1="{y_line}" x2="{width - margin}" y2="{y_line}" stroke="{palette["line"]}" stroke-width="8" stroke-linecap="round"/>'
    progress = f'<line x1="{margin}" y1="{y_line}" x2="{width - margin - max(0, step // 3)}" y2="{y_line}" stroke="{palette["accent"]}" stroke-width="4" stroke-linecap="round" opacity="0.45"/>'
    nodes: List[str] = [render_chip_row(["Timeline", "Milestone", "Roadmap"], margin, 196, palette, 3), line, progress]
    for idx, item in enumerate(items):
        x = margin + step * idx if len(items) > 1 else width // 2
        label_y = y_line - 110 if idx % 2 == 0 else y_line + 98
        nodes.append(f'<line x1="{x}" y1="{y_line}" x2="{x}" y2="{label_y + 18}" stroke="{palette["line"]}" stroke-width="2" stroke-dasharray="6 6"/>')
        nodes.append(f'<circle cx="{x}" cy="{y_line}" r="24" fill="{palette["panel"]}" stroke="{palette["accent"]}" stroke-width="4"/>')
        nodes.append(f'<circle cx="{x}" cy="{y_line}" r="10" fill="{palette["accent"]}"/>')
        nodes.append(f'<rect x="{x - 34}" y="{label_y - 16}" width="68" height="28" rx="14" fill="{palette["accent_soft"]}"/>')
        nodes.append(text_block(x - 20, label_y + 4, [f"{idx + 1:02d}"], 14, palette["accent"], 700, 18))
        nodes.append(text_block(x - 86, label_y + 28, wrap_text(item, 10), 17, palette["text"], 600, 22))
    footer = card(margin, int(height * 0.68), width - margin * 2, height - int(height * 0.68) - 42, 24, palette["panel"], palette["line"])
    footer_title = text_block(margin + 24, int(height * 0.68) + 36, ["Visual / Notes"], 16, palette["accent"], 700, 20)
    footer_text = text_block(margin + 24, int(height * 0.68) + 66, wrap_text(meta["visual"] + "；" + meta["notes"], 52), 18, palette["text"], 600, 28)
    return "".join([title, objective, *nodes, footer, footer_title, footer_text])



def render_comparison(meta: Dict[str, str], width: int, height: int, palette: Dict[str, str]) -> str:
    style = get_theme_style(palette)
    margin = 60
    title = text_block(margin, 92, wrap_text(meta["title"], 18), 34, palette["text"], 700, 42)
    objective = text_block(margin, 148, wrap_text(meta["objective"], 36), 18, palette["muted"], 400, 28)
    top = 210
    col_gap = 28
    col_w = (width - margin * 2 - col_gap) // 2
    body_h = height - top - 54
    left_x = margin
    right_x = margin + col_w + col_gap
    left_card = card(left_x, top, col_w, body_h, 24, palette["panel"], palette["line"])
    right_card = card(right_x, top, col_w, body_h, 24, str(style["comparison_right_fill"]), str(style["comparison_right_stroke"]))
    left_items = list(meta.get("left_items", [])) or split_lines(meta["message"])
    right_items = list(meta.get("right_items", [])) or split_lines(meta["support"])
    if not right_items:
        midpoint = max(1, math.ceil(len(left_items) / 2))
        right_items = left_items[midpoint:]
        left_items = left_items[:midpoint]
    left_bar = f'<rect x="{left_x}" y="{top}" width="{col_w}" height="56" rx="24" fill="{palette["accent_soft"]}"/>'
    right_bar = f'<rect x="{right_x}" y="{top}" width="{col_w}" height="56" rx="24" fill="{style["comparison_right_fill"]}" stroke="{style["comparison_right_stroke"]}" stroke-width="2"/>'
    left_label = text_block(left_x + 28, top + 34, [str(meta.get("left_title", "Column A"))], 18, palette["accent"], 700, 24)
    right_label = text_block(right_x + 28, top + 34, [str(meta.get("right_title", "Column B"))], 18, palette["text"], 700, 24)
    left = bullet_list(left_x + 28, top + 94, left_items or [meta["message"]], 20, palette["text"], palette["accent"], col_w - 56)
    right = bullet_list(right_x + 28, top + 94, right_items or [meta["support"]], 20, palette["text"], palette["accent"], col_w - 56)
    delta_chip = render_chip_row(list(style["comparison_chip_labels"]), margin, top - 26, palette, 3)
    return "".join([title, objective, delta_chip, left_card, right_card, left_bar, right_bar, left_label, right_label, left, right])





def render_cover(meta: Dict[str, str], width: int, height: int, palette: Dict[str, str]) -> str:
    style = get_theme_style(palette)
    margin = 72
    bg_band = f'<rect x="0" y="0" width="{width}" height="{int(height * 0.62)}" fill="{style["hero_band_fill"]}" opacity="{style["cover_band_opacity"]}"/>'
    title = text_block(margin, int(height * 0.28), wrap_text(meta["title"], 14), 52, palette["text"], 700, 62)
    objective = text_block(margin, int(height * 0.48), wrap_text(meta["objective"], 28), 24, palette["muted"], 400, 34)
    kicker = text_block(margin, int(height * 0.16), ["Presentation Cover"], 16, str(style["cover_kicker_fill"]), 700, 20)
    footer_card = card(margin, int(height * 0.72), width - margin * 2, int(height * 0.16), 24, str(style["cover_footer_fill"]), str(style["cover_footer_stroke"]))
    footer = text_block(margin + 28, int(height * 0.72) + 46, wrap_text(meta["support"] or meta["visual"], 52), 18, palette["text"], 500, 28)
    return "".join([bg_band, kicker, title, objective, footer_card, footer])




def render_section_divider(meta: Dict[str, str], width: int, height: int, palette: Dict[str, str]) -> str:
    style = get_theme_style(palette)
    margin = 88
    line_y = int(height * 0.55)
    panel = card(margin, int(height * 0.18), width - margin * 2, int(height * 0.58), 28, str(style["section_panel_fill"]), str(style["section_panel_stroke"]))
    accent = f'<rect x="{margin + 28}" y="{line_y}" width="{width - margin * 2 - 56}" height="8" rx="4" fill="{style["section_line_fill"]}"/>'
    title = text_block(margin + 28, int(height * 0.42), wrap_text(meta["title"], 16), 48, palette["text"], 700, 58)
    objective = text_block(margin + 28, int(height * 0.66), wrap_text(meta["objective"], 34), 20, palette["muted"], 400, 30)
    tag = text_block(margin + 28, int(height * 0.26), ["Section Divider"], 16, str(style["section_tag_fill"]), 700, 20)
    return "".join([panel, tag, title, accent, objective])



def render_quote(meta: Dict[str, str], width: int, height: int, palette: Dict[str, str]) -> str:
    margin = 90
    quote_mark = text_block(margin, 140, ["“"], 88, palette["accent"], 700, 96)
    quote_text = text_block(margin + 40, 210, wrap_text(meta["message"] or meta["title"], 20), 34, palette["text"], 600, 44)
    source_card = card(margin, int(height * 0.72), width - margin * 2, 100, 20, palette["panel"], palette["line"])
    source = text_block(margin + 28, int(height * 0.72) + 42, [meta["title"]] + wrap_text(meta["support"] or meta["objective"], 40), 18, palette["muted"], 500, 26)
    return "".join([quote_mark, quote_text, source_card, source])


def render_kpi_grid(meta: Dict[str, str], width: int, height: int, palette: Dict[str, str]) -> str:
    style = get_theme_style(palette)
    margin = 56
    title = text_block(margin, 92, wrap_text(meta["title"], 18), 34, palette["text"], 700, 42)
    objective = text_block(margin, 148, wrap_text(meta["objective"], 34), 18, palette["muted"], 400, 28)
    kpis = list(meta.get("kpis", []))
    while len(kpis) < 4:
        idx = len(kpis) + 1
        kpis.append({"label": f"KPI {idx:02d}", "value": f"KPI {idx:02d}", "note": compress_text(meta["visual"], 22)})
    gap = 24
    card_w = (width - margin * 2 - gap) // 2
    card_h = int((height - 250 - gap - 56) / 2)
    parts = [title, objective, render_chip_row(["Dashboard", "KPI", "Snapshot"], margin, 196, palette, 3)]
    for idx, item in enumerate(kpis[:4]):
        row = idx // 2
        col = idx % 2
        x = margin + col * (card_w + gap)
        y = 220 + row * (card_h + gap)
        parts.append(card(x, y, card_w, card_h, 24, str(style["kpi_card_fill"]), str(style["kpi_card_stroke"])))
        parts.append(f'<rect x="{x}" y="{y}" width="{card_w}" height="10" rx="10" fill="{style["kpi_bar_fill"]}"/>')
        parts.append(f'<rect x="{x + 24}" y="{y + 26}" width="110" height="28" rx="14" fill="{style["kpi_tag_fill"]}"/>')
        parts.append(text_block(x + 40, y + 46, [str(item.get("label", f"KPI {idx + 1:02d}"))], 14, str(style["kpi_tag_text"]), 700, 18))
        parts.append(text_block(x + 24, y + 122, wrap_text(str(item.get("value", "--")), 10), 42, str(style["kpi_value_fill"]), 700, 46))
        parts.append(f'<line x1="{x + 24}" y1="{y + card_h - 56}" x2="{x + card_w - 24}" y2="{y + card_h - 56}" stroke="{palette["line"]}" stroke-width="1"/>')
        parts.append(text_block(x + 24, y + card_h - 24, wrap_text(str(item.get("note", meta["visual"])), 24)[:2], 14, str(style["kpi_note_fill"]), 500, 20))
    return "".join(parts)





def render_process(meta: Dict[str, str], width: int, height: int, palette: Dict[str, str]) -> str:
    margin = 60
    title = text_block(margin, 92, wrap_text(meta["title"], 18), 34, palette["text"], 700, 42)
    objective = text_block(margin, 148, wrap_text(meta["objective"], 34), 18, palette["muted"], 400, 28)
    items = list(meta.get("steps", [])) or split_lines(meta["message"] or meta["support"])[:4]
    while len(items) < 3:
        items.append(f"步骤 {len(items) + 1}")

    gap = 20
    step_w = (width - margin * 2 - gap * (len(items) - 1)) // len(items)
    y = int(height * 0.42)
    parts = [title, objective, render_chip_row(["Process", "Workflow", "Execution"], margin, 196, palette, 3)]
    for idx, item in enumerate(items):
        x = margin + idx * (step_w + gap)
        parts.append(card(x, y, step_w, 196, 24, palette["panel"], palette["line"]))
        parts.append(f'<rect x="{x}" y="{y}" width="{step_w}" height="12" rx="12" fill="{palette["accent"]}" opacity="0.9"/>')
        parts.append(f'<circle cx="{x + 34}" cy="{y + 44}" r="18" fill="{palette["accent_soft"]}" stroke="{palette["accent"]}" stroke-width="2"/>')
        parts.append(text_block(x + 24, y + 50, [f"{idx + 1:02d}"], 14, palette["accent"], 700, 18))
        parts.append(text_block(x + 66, y + 46, [f"STEP {idx + 1:02d}"], 14, palette["accent"], 700, 18))
        parts.append(text_block(x + 22, y + 104, wrap_text(item, 10), 22, palette["text"], 600, 28))
        parts.append(text_block(x + 22, y + 164, ["Owner / Output"], 13, palette["muted"], 600, 18))
        parts.append(text_block(x + 22, y + 188, wrap_text(meta["support"] or meta["visual"], 14, 2), 13, palette["muted"], 500, 18))
        if idx < len(items) - 1:
            arrow_x = x + step_w + 4
            parts.append(f'<line x1="{arrow_x}" y1="{y + 98}" x2="{arrow_x + gap - 8}" y2="{y + 98}" stroke="{palette["accent"]}" stroke-width="4" stroke-linecap="round"/>')
            parts.append(f'<polygon points="{arrow_x + gap - 8},{y + 98} {arrow_x + gap - 18},{y + 92} {arrow_x + gap - 18},{y + 104}" fill="{palette["accent"]}"/>')
    footer = card(margin, y + 238, width - margin * 2, 74, 20, palette["panel"], palette["line"])
    footer_text = text_block(margin + 24, y + 282, wrap_text(meta["support"] or meta["visual"], 60), 16, palette["muted"], 500, 24)
    parts.extend([footer, footer_text])
    return "".join(parts)



def render_matrix(meta: Dict[str, str], width: int, height: int, palette: Dict[str, str]) -> str:
    margin = 72
    title = text_block(margin, 92, wrap_text(meta["title"], 18), 34, palette["text"], 700, 42)
    objective = text_block(margin, 148, wrap_text(meta["objective"], 34), 18, palette["muted"], 400, 28)
    box_x = margin + 90
    box_y = 230
    box_w = width - box_x - margin
    box_h = height - box_y - 80
    quad_w = box_w // 2
    quad_h = box_h // 2
    quad_fills = [palette["accent_soft"], palette["panel"], palette["panel"], "#F8FAFC" if palette is PALETTES["default"] else "#172033"]
    parts = [title, objective]
    for idx, (qx, qy) in enumerate([(box_x, box_y), (box_x + quad_w, box_y), (box_x, box_y + quad_h), (box_x + quad_w, box_y + quad_h)]):
        parts.append(f'<rect x="{qx}" y="{qy}" width="{quad_w}" height="{quad_h}" fill="{quad_fills[idx]}" stroke="{palette["line"]}"/>')
    vertical = f'<line x1="{box_x + quad_w}" y1="{box_y}" x2="{box_x + quad_w}" y2="{box_y + box_h}" stroke="{palette["line"]}" stroke-width="3"/>'
    horizontal = f'<line x1="{box_x}" y1="{box_y + quad_h}" x2="{box_x + box_w}" y2="{box_y + quad_h}" stroke="{palette["line"]}" stroke-width="3"/>'
    outer = card(box_x, box_y, box_w, box_h, 0, "none", palette["line"])
    axis_y = text_block(margin, box_y + box_h // 2 + 8, ["Impact"], 16, palette["muted"], 600, 20)
    axis_x = text_block(box_x + box_w // 2 - 20, box_y + box_h + 42, ["Feasibility"], 16, palette["muted"], 600, 20)
    items = list(meta.get("quadrants", []))
    positions = [(0.22, 0.22), (0.72, 0.22), (0.22, 0.7), (0.72, 0.7)]
    parts.extend([outer, vertical, horizontal, axis_y, axis_x])
    for idx, item in enumerate(items[:4]):
        px, py = positions[idx]
        cx = int(box_x + box_w * px)
        cy = int(box_y + box_h * py)
        label = str(item.get("quadrant", f"Q{idx + 1}"))
        detail = str(item.get("detail", "待补充"))
        parts.append(text_block(cx - 10, cy - 22, wrap_text(label, 10), 14, palette["accent"], 700, 18))
        parts.append(f'<circle cx="{cx}" cy="{cy + 26}" r="12" fill="{palette["accent"]}" opacity="0.85"/>')
        parts.append(text_block(cx + 26, cy + 34, wrap_text(detail, 10), 16, palette["text"], 600, 22))
    return "".join(parts)




def render_table_lite(meta: Dict[str, str], width: int, height: int, palette: Dict[str, str]) -> str:
    margin = 56
    title = text_block(margin, 92, wrap_text(meta["title"], 18), 34, palette["text"], 700, 42)
    objective = text_block(margin, 148, wrap_text(meta["objective"], 34), 18, palette["muted"], 400, 28)
    rows = list(meta.get("rows", []))
    if not rows:
        rows = [["项目 A", "结果", "说明"], ["项目 B", "结果", "说明"], ["项目 C", "结果", "说明"]]
    table_x = margin
    table_y = 220
    table_w = width - margin * 2
    row_h = 64
    table_h = row_h * (len(rows) + 1)
    parts = [title, objective, render_chip_row(["Table", "Snapshot", "Structured"], margin, 196, palette, 3), card(table_x, table_y, table_w, table_h, 16, palette["panel"], palette["line"]) ]
    parts.append(f'<rect x="{table_x}" y="{table_y}" width="{table_w}" height="{row_h}" rx="16" fill="{palette["accent_soft"]}"/>')
    headers = ["项目", "结果", "备注"]
    col_w = table_w // 3
    for idx, header in enumerate(headers):
        parts.append(text_block(table_x + 20 + idx * col_w, table_y + 40, [header], 18, palette["text"], 700, 24))
    for row_idx, row in enumerate(rows, start=1):
        y = table_y + row_h * row_idx
        fill = palette["panel"] if row_idx % 2 else palette["accent_soft"]
        parts.append(f'<rect x="{table_x}" y="{y}" width="{table_w}" height="{row_h}" fill="{fill}" opacity="0.45"/>')
        if row_idx < len(rows) + 1:
            parts.append(f'<line x1="{table_x}" y1="{y}" x2="{table_x + table_w}" y2="{y}" stroke="{palette["line"]}" stroke-width="1"/>')
        cells = list(row)
        while len(cells) < 3:
            cells.append("待补充")
        parts.append(f'<rect x="{table_x + 16}" y="{y + 16}" width="6" height="{row_h - 32}" rx="3" fill="{palette["accent"]}" opacity="0.7"/>')
        for idx, cell in enumerate(cells[:3]):
            color = palette["accent"] if idx == 1 else palette["text"]
            weight = 700 if idx == 1 else 500
            parts.append(text_block(table_x + 28 + idx * col_w, y + 40, wrap_text(str(cell), 12), 16, color, weight, 22))
    return "".join(parts)




def resolve_theme_name(meta: Dict[str, str], explicit_theme: str | None = None) -> str:
    aliases = {
        "default": "default",
        "dark": "dark",
        "tech": "tech-blue",
        "tech-blue": "tech-blue",
        "科技蓝": "tech-blue",
        "business-dark": "business-dark",
        "深色商务": "business-dark",
        "brand": "brand-light",
        "brand-light": "brand-light",
        "轻品牌": "brand-light",
        "consulting": "consulting",
        "顾问": "consulting",
        "顾问报告": "consulting",
    }
    if explicit_theme:
        theme_key = explicit_theme.strip().lower()
        resolved = aliases.get(theme_key, theme_key)
        if resolved in PALETTES:
            return resolved

    style_text = f"{meta['layout']} {meta['visual']} {meta['title']}".lower()
    if any(key in style_text for key in ["consulting", "顾问", "报告风", "咨询"]):
        return "consulting"
    if any(key in style_text for key in ["brand", "品牌", "营销", "pink", "粉"]):
        return "brand-light"
    if any(key in style_text for key in ["tech", "科技", "blue", "蓝"]):
        return "tech-blue"
    if any(key in style_text for key in ["business", "商务", "董事会", "深色商务"]):
        return "business-dark"
    if any(key in style_text for key in ["dark", "黑", "夜", "深色"]):
        return "dark"
    return "default"


def choose_palette(meta: Dict[str, str], explicit_theme: str | None = None) -> Dict[str, str]:
    return PALETTES[resolve_theme_name(meta, explicit_theme)]


def resolve_theme_variant(palette: Dict[str, str]) -> str:
    for name, candidate in PALETTES.items():
        if candidate is palette:
            return name
    return "default"


def get_theme_style(palette: Dict[str, str]) -> Dict[str, str | int | float]:
    theme = resolve_theme_variant(palette)
    base = {
        "chip_fill": palette["accent_soft"],
        "chip_stroke": palette["line"],
        "chip_text": palette["accent"],
        "chip_weight": 700,
        "callout_fill": palette["accent_soft"],
        "callout_stroke": palette["line"],
        "callout_text": palette["text"],
        "callout_radius": 18,
        "cover_band_opacity": 1.0,
        "cover_footer_fill": palette["panel"],
        "comparison_right_fill": palette["panel"],
        "comparison_right_stroke": palette["accent"],
        "comparison_chip_labels": ["Gap", "Trade-off", "Decision"],
        "hero_band_fill": palette["accent_soft"],
        "hero_band_opacity": 1.0,
        "hero_support_fill": palette["panel"],
        "hero_visual_fill": palette["panel"],
        "hero_visual_stroke": palette["line"],
        "hero_kicker": palette["accent"],
        "hero_message_fill": palette["accent_soft"],
        "hero_message_stroke": palette["line"],
        "kpi_card_fill": palette["panel"],
        "kpi_card_stroke": palette["line"],
        "kpi_bar_fill": palette["accent"],
        "kpi_value_fill": palette["text"],
        "kpi_note_fill": palette["muted"],
        "kpi_tag_fill": palette["accent_soft"],
        "kpi_tag_text": palette["accent"],
        "cover_kicker_fill": palette["accent"],
        "cover_footer_stroke": palette["line"],
        "section_tag_fill": palette["accent"],
        "section_line_fill": palette["accent"],
        "section_panel_fill": palette["panel"],
        "section_panel_stroke": palette["line"],
        "data_metric_fill": palette["accent_soft"],
        "data_metric_stroke": palette["line"],
        "data_metric_value": palette["accent"],
        "data_metric_label": palette["accent"],
        "data_bottom_fill": palette["panel"],
        "data_bottom_stroke": palette["line"],
    }

    overrides = {
        "dark": {
            "chip_fill": palette["panel"],
            "chip_stroke": palette["accent"],
            "callout_fill": palette["panel"],
            "callout_stroke": palette["accent"],
            "cover_band_opacity": 0.92,
            "hero_band_fill": "#111827",
            "hero_band_opacity": 1.0,
            "hero_support_fill": "#111827",
            "hero_visual_fill": "#0B1220",
            "hero_visual_stroke": palette["accent"],
            "hero_message_fill": "#111827",
            "hero_message_stroke": palette["accent"],
            "kpi_card_fill": "#111827",
            "kpi_card_stroke": palette["accent"],
            "kpi_note_fill": "#CBD5E1",
        },
        "tech-blue": {
            "chip_fill": "#E0ECFF",
            "chip_stroke": "#9DBCF7",
            "callout_fill": "#EAF2FF",
            "comparison_chip_labels": ["System", "Signal", "Decision"],
            "hero_band_fill": "#DCEAFE",
            "hero_support_fill": "#FFFFFF",
            "hero_visual_fill": "#EEF4FF",
            "hero_visual_stroke": "#9DBCF7",
            "hero_message_fill": "#E8F0FF",
            "hero_message_stroke": "#9DBCF7",
            "kpi_card_fill": "#F8FBFF",
            "kpi_card_stroke": "#C7D7F2",
            "kpi_tag_fill": "#E8F0FF",
            "kpi_tag_text": "#1D4ED8",
            "cover_kicker_fill": "#1D4ED8",
            "cover_footer_stroke": "#9DBCF7",
            "section_tag_fill": "#1D4ED8",
            "section_line_fill": "#2563EB",
            "section_panel_fill": "#EEF4FF",
            "section_panel_stroke": "#9DBCF7",
            "data_metric_fill": "#E8F0FF",
            "data_metric_stroke": "#9DBCF7",
            "data_metric_value": "#1D4ED8",
            "data_metric_label": "#1D4ED8",
            "data_bottom_fill": "#F8FBFF",
            "data_bottom_stroke": "#C7D7F2",
        },

        "business-dark": {
            "chip_fill": "#162033",
            "chip_stroke": "#60A5FA",
            "callout_fill": "#162033",
            "callout_stroke": "#3B82F6",
            "cover_band_opacity": 0.88,
            "comparison_right_fill": "#162033",
            "comparison_chip_labels": ["Risk", "Trade-off", "Decision"],
            "hero_band_fill": "#111827",
            "hero_band_opacity": 0.94,
            "hero_support_fill": "#121A2B",
            "hero_visual_fill": "#162033",
            "hero_visual_stroke": "#3B82F6",
            "hero_message_fill": "#162033",
            "hero_message_stroke": "#60A5FA",
            "kpi_card_fill": "#121A2B",
            "kpi_card_stroke": "#2F4B76",
            "kpi_value_fill": "#F8FAFC",
            "kpi_note_fill": "#CBD5E1",
            "cover_kicker_fill": "#93C5FD",
            "cover_footer_stroke": "#2F4B76",
            "section_tag_fill": "#93C5FD",
            "section_line_fill": "#60A5FA",
            "section_panel_fill": "#121A2B",
            "section_panel_stroke": "#2F4B76",
            "data_metric_fill": "#162033",
            "data_metric_stroke": "#3B82F6",
            "data_metric_value": "#93C5FD",
            "data_metric_label": "#93C5FD",
            "data_bottom_fill": "#121A2B",
            "data_bottom_stroke": "#2F4B76",
        },

        "brand-light": {
            "chip_fill": "#FDECF5",
            "chip_stroke": "#F9A8D4",
            "chip_text": "#DB2777",
            "callout_fill": "#FFF1F7",
            "callout_stroke": "#FBCFE8",
            "callout_radius": 22,
            "comparison_chip_labels": ["Brand", "Contrast", "Choice"],
            "hero_band_fill": "#FCE7F3",
            "hero_support_fill": "#FFFFFF",
            "hero_visual_fill": "#FFF1F7",
            "hero_visual_stroke": "#F9A8D4",
            "hero_kicker": "#DB2777",
            "hero_message_fill": "#FFF1F7",
            "hero_message_stroke": "#FBCFE8",
            "kpi_card_fill": "#FFFCFE",
            "kpi_card_stroke": "#F3D4E4",
            "kpi_bar_fill": "#EC4899",
            "kpi_value_fill": "#BE185D",
            "kpi_tag_fill": "#FFF1F7",
            "kpi_tag_text": "#DB2777",
            "cover_kicker_fill": "#DB2777",
            "cover_footer_stroke": "#F3D4E4",
            "section_tag_fill": "#DB2777",
            "section_line_fill": "#EC4899",
            "section_panel_fill": "#FFF6FB",
            "section_panel_stroke": "#F9A8D4",
            "data_metric_fill": "#FFF1F7",
            "data_metric_stroke": "#F9A8D4",
            "data_metric_value": "#DB2777",
            "data_metric_label": "#DB2777",
            "data_bottom_fill": "#FFF8FC",
            "data_bottom_stroke": "#F3D4E4",
        },

        "consulting": {
            "chip_fill": "#ECF7F5",
            "chip_stroke": "#9FD5CE",
            "chip_text": "#0F766E",
            "callout_fill": "#F6FBFA",
            "callout_stroke": "#B9D9D3",
            "comparison_chip_labels": ["Gap", "Evidence", "Recommendation"],
            "hero_band_fill": "#E8F3F1",
            "hero_support_fill": "#FFFEFC",
            "hero_visual_fill": "#F3F7F6",
            "hero_visual_stroke": "#B9D9D3",
            "hero_kicker": "#0F766E",
            "hero_message_fill": "#F0F7F6",
            "hero_message_stroke": "#C7D9D5",
            "kpi_card_fill": "#FFFEFC",
            "kpi_card_stroke": "#D6D9DE",
            "kpi_bar_fill": "#0F766E",
            "kpi_value_fill": "#0F172A",
            "kpi_tag_fill": "#F1F8F7",
            "kpi_tag_text": "#0F766E",
        },
    }
    if theme in overrides:
        base.update(overrides[theme])
    return base



def render_chip_row(chips: List[str], x: int, y: int, palette: Dict[str, str], max_chips: int = 4) -> str:
    if not chips:
        return ""
    style = get_theme_style(palette)
    parts: List[str] = []
    cursor_x = x
    for chip in chips[:max_chips]:
        label = compress_text(chip, 14)
        chip_w = max(84, min(180, 24 + len(label) * 14))
        parts.append(f'<rect x="{cursor_x}" y="{y - 22}" width="{chip_w}" height="34" rx="17" fill="{style["chip_fill"]}" stroke="{style["chip_stroke"]}"/>')
        parts.append(text_block(cursor_x + 16, y, [label], 14, str(style["chip_text"]), int(style["chip_weight"]), 18))
        cursor_x += chip_w + 10
    return "".join(parts)




def render_callout(x: int, y: int, width: int, text: str, palette: Dict[str, str]) -> str:
    lines = wrap_text(text, 24, 3)
    if not lines:
        return ""
    style = get_theme_style(palette)
    height = 28 + len(lines) * 22
    return "".join([
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{style["callout_radius"]}" fill="{style["callout_fill"]}" stroke="{style["callout_stroke"]}"/>',
        text_block(x + 18, y + 26, lines, 15, str(style["callout_text"]), 600, 20),
    ])




def render_svg(meta: Dict[str, str], width: int, height: int, layout: str, theme: str | None = None) -> str:
    palette = choose_palette(meta, theme)

    rewritten = dict(meta)
    rewritten["title"] = rewrite_title(meta.get("title", ""))
    rewritten["objective"] = rewrite_objective(meta.get("objective", ""), 40)
    rewritten["subtitle"] = build_subtitle(meta.get("title", ""), meta.get("objective", ""), meta.get("message", ""))
    message_bullets = build_supporting_bullets(layout, meta.get("objective", ""), meta.get("message", ""), meta.get("support", ""), meta.get("notes", ""), max_items=5)
    support_bullets = build_supporting_bullets(layout, meta.get("message", ""), meta.get("support", ""), meta.get("notes", ""), meta.get("objective", ""), max_items=4)
    rewritten["message"] = "\n".join(message_bullets)
    rewritten["support"] = "\n".join(support_bullets)
    rewritten.update(build_layout_payload(layout, message_bullets, support_bullets))

    rewritten["notes"] = "\n".join(split_lines(meta.get("notes", ""), max_items=3, item_chars=30))
    rewritten["takeaway"] = extract_takeaway(meta.get("title", ""), meta.get("objective", ""), rewritten["message"], rewritten["support"])


    bg = f'<rect width="100%" height="100%" fill="{palette["bg"]}"/>'
    renderers = {
        "title-bullets": render_title_bullets,
        "two-column": render_two_column,
        "hero": render_hero,
        "data-highlight": render_data_highlight,
        "timeline": render_timeline,
        "comparison": render_comparison,
        "cover": render_cover,
        "section-divider": render_section_divider,
        "quote": render_quote,
        "kpi-grid": render_kpi_grid,
        "process": render_process,
        "matrix": render_matrix,
        "table-lite": render_table_lite,
    }

    body = renderers.get(layout, render_title_bullets)(rewritten, width, height, palette)
    chips = render_chip_row(split_lines(rewritten["layout"] + "\n" + rewritten["visual"], max_items=4, item_chars=16), 44, 42, palette, 4)
    callout = render_callout(width - 324, 28, 280, f"Objective：{rewritten['objective']}", palette)
    takeaway = render_callout(44, height - 104, 340, f"Takeaway：{rewritten['takeaway']}", palette)
    subtitle = text_block(392, height - 46, [f"Subtitle: {rewritten['subtitle']}"], 12, palette["muted"], 500, 16)
    footer = text_block(392, height - 24, [f"Layout: {layout}"], 12, palette["muted"], 500, 16)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">{bg}{chips}{callout}{body}{takeaway}{subtitle}{footer}</svg>\n'





def parse_task_file(path: Path) -> Dict[str, str]:
    content = read_text(path)
    meta = {
        "title": extract_heading_value(content, "Metadata"),
        "objective": extract_heading_value(content, "Objective"),
        "message": extract_heading_value(content, "Core Message"),
        "support": extract_heading_value(content, "Supporting Material"),
        "layout": extract_heading_value(content, "Layout Guidance"),
        "visual": extract_heading_value(content, "Visual Guidance"),
        "notes": extract_heading_value(content, "Speaker Notes Seed"),
    }
    title_match = re.search(r"-\s*Title:\s*(.+)", content)
    if title_match:
        meta["title"] = title_match.group(1).strip()
    return meta


def write_if_needed(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        print(f"跳过已存在文件: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"已写入: {path}")


def resolve_task_files(project_path: Path, tasks_dir: Path | None) -> List[Path]:
    target_dir = tasks_dir or (project_path / "tasks")
    if not target_dir.exists():
        raise SystemExit(f"任务目录不存在: {target_dir}")
    task_files = sorted(target_dir.glob("slide-*.md"))
    if not task_files:
        raise SystemExit(f"未在任务目录找到 slide-*.md: {target_dir}")
    return task_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SVG draft pages from task markdown files")
    parser.add_argument("--project-path", required=True, help="项目目录")
    parser.add_argument("--tasks-dir", help="任务目录，默认 <project>/tasks")
    parser.add_argument("--output-dir", help="SVG 输出目录，默认 <project>/svg_output")
    parser.add_argument("--manifest", help="可选 manifest 输出路径，默认 <project>/svg_page_drafts.json")
    parser.add_argument("--format", help="显式指定画布格式")
    parser.add_argument("--viewbox", help="显式指定 viewBox")
    parser.add_argument("--theme", help="显式指定主题：default、dark、tech-blue、business-dark、brand-light、consulting")
    parser.add_argument("--force", action="store_true", help="覆盖已有 SVG 草稿")

    args = parser.parse_args()

    project_path = resolve_path(args.project_path)
    tasks_dir = resolve_path(args.tasks_dir) if args.tasks_dir else None
    output_dir = resolve_path(args.output_dir) if args.output_dir else project_path / "svg_output"
    manifest_path = resolve_path(args.manifest) if args.manifest else project_path / "svg_page_drafts.json"

    fmt, width, height = detect_dimensions(project_path, args.format, args.viewbox)
    task_files = resolve_task_files(project_path, tasks_dir)
    manifest = {
        "project_path": str(project_path),
        "format": fmt,
        "viewbox": f"0 0 {width} {height}",
        "slides": [],
    }

    for task_file in task_files:
        meta = parse_task_file(task_file)
        slide_match = re.search(r"slide-(\d+)\.md$", task_file.name)
        slide_no = slide_match.group(1) if slide_match else "00"
        layout = infer_layout(meta["layout"], meta["visual"], meta["title"])
        svg_path = output_dir / f"slide-{slide_no}.svg"
        svg = render_svg(meta, width, height, layout, args.theme)

        write_if_needed(svg_path, svg, args.force)
        manifest["slides"].append(
            {
                "slide_no": int(slide_no),
                "task_file": str(task_file),
                "svg_file": str(svg_path),
                "layout": layout,
                "theme": resolve_theme_name(meta, args.theme),

                "title": meta["title"],
            }
        )


    write_if_needed(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", True)
    print(f"已生成 {len(task_files)} 页 SVG 草稿。")


if __name__ == "__main__":
    main()
