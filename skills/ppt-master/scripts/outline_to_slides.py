#!/usr/bin/env python3
"""Expand outline.md into a slide-by-slide planning document.

This helper creates a stable intermediate file for WorkBuddy's ppt-master flow.
It does not generate SVG. It turns high-level sections into explicit slide blocks
that agents or downstream generators can refine.
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from typing import List


SECTION_RE = re.compile(r"^##\s+Section\s+(\d+):\s*(.+?)\s*$")
BULLET_PREFIXES = ("- ", "* ")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def detect_slide_count(spec_text: str) -> int | None:
    match = re.search(r"目标页数：\s*(\d+)", spec_text)
    if match:
        return int(match.group(1))
    match = re.search(r"Slide Count.*?(\d+)", spec_text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return int(match.group(1))
    return None


def parse_outline(outline_text: str) -> List[dict]:
    sections: List[dict] = []
    current: dict | None = None
    for raw_line in outline_text.splitlines():
        line = raw_line.rstrip()
        section_match = SECTION_RE.match(line)
        if section_match:
            if current:
                sections.append(current)
            current = {
                "title": section_match.group(2).strip(),
                "goal": "待补充",
                "arguments": [],
                "evidence": [],
            }
            continue
        if not current:
            continue
        if line.startswith("- 目标："):
            current["goal"] = line.split("：", 1)[1].strip() or "待补充"
        elif line.startswith("- 关键论点："):
            value = line.split("：", 1)[1].strip()
            if value and value != "待补充":
                current["arguments"] = [item.strip() for item in re.split(r"[；;]", value) if item.strip()]
        elif line.startswith("- 需要的数据/案例："):
            value = line.split("：", 1)[1].strip()
            if value and value != "待补充":
                current["evidence"] = [item.strip() for item in re.split(r"[；;]", value) if item.strip()]
        elif line.startswith(BULLET_PREFIXES):
            payload = line[2:].strip()
            if payload:
                current.setdefault("arguments", []).append(payload)
    if current:
        sections.append(current)
    return sections


def expand_sections_to_slides(sections: List[dict], requested_slide_count: int | None) -> List[dict]:
    if not sections:
        return []
    target = requested_slide_count or len(sections)
    target = max(target, len(sections))
    extra = target - len(sections)
    distribution = [1] * len(sections)
    idx = 0
    while extra > 0:
        distribution[idx % len(distribution)] += 1
        idx += 1
        extra -= 1

    slides: List[dict] = []
    for section, copies in zip(sections, distribution):
        arguments = section.get("arguments") or ["待补充"]
        evidence = section.get("evidence") or ["待补充"]
        for copy_idx in range(copies):
            title = section["title"] if copies == 1 else f"{section['title']}（{copy_idx + 1}/{copies}）"
            arg = arguments[min(copy_idx, len(arguments) - 1)]
            evd = evidence[min(copy_idx, len(evidence) - 1)]
            slides.append(
                {
                    "title": title,
                    "goal": section.get("goal", "待补充"),
                    "message": arg,
                    "evidence": evd,
                    "layout": infer_layout(title, copy_idx, copies),
                }
            )
    return slides


def infer_layout(title: str, copy_idx: int, copies: int) -> str:
    lower = title.lower()
    if copy_idx == 0 and ("封面" in title or "cover" in lower):
        return "大标题 + 副标题 + 视觉主图"
    if any(token in title for token in ["数据", "证据", "指标", "图表"]):
        return "图表主导 + 关键结论标注"
    if any(token in title for token in ["案例", "演示", "示例"]):
        return "左右分栏 / 步骤拆解"
    if copies > 1:
        return "同章节连续展开页，保持统一栅格"
    return "标题 + 3 要点 + 支撑视觉"


def build_slides_markdown(project_name: str, slides: List[dict]) -> str:
    lines = ["# Slide Plan", "", f"- 项目名称：{project_name}", f"- 目标页数：{len(slides)}", ""]
    for idx, slide in enumerate(slides, start=1):
        lines.extend(
            [
                f"## Slide {idx}: {slide['title']}",
                f"- 页面目标：{slide['goal']}",
                f"- 核心信息：{slide['message']}",
                f"- 支撑数据/案例：{slide['evidence']}",
                f"- 建议版式：{slide['layout']}",
                "- 视觉提示：待补充",
                "- 备注：待补充",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand outline.md into slide-by-slide planning markdown")
    parser.add_argument("--project-path", required=True, help="项目目录")
    parser.add_argument("--outline", help="自定义 outline.md 路径")
    parser.add_argument("--output", help="输出 slide plan 路径，默认 notes/slides.md")
    parser.add_argument("--force", action="store_true", help="覆盖已有输出文件")
    args = parser.parse_args()

    project_path = Path(args.project_path).expanduser().resolve()
    outline_path = Path(args.outline).expanduser().resolve() if args.outline else project_path / "notes" / "outline.md"
    output_path = Path(args.output).expanduser().resolve() if args.output else project_path / "notes" / "slides.md"
    spec_path = project_path / "design_spec.md"

    if not outline_path.exists():
        raise SystemExit(f"缺少 outline 文件: {outline_path}")
    if output_path.exists() and not args.force:
        raise SystemExit(f"输出文件已存在，请使用 --force 覆盖: {output_path}")

    spec_text = read_text(spec_path) if spec_path.exists() else ""
    outline_text = read_text(outline_path)
    sections = parse_outline(outline_text)
    requested_slide_count = detect_slide_count(spec_text)
    slides = expand_sections_to_slides(sections, requested_slide_count)
    if not slides:
        raise SystemExit("outline.md 中未解析到可用章节。")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_slides_markdown(project_path.name, slides), encoding="utf-8")

    print(f"project={project_path}")
    print(f"outline={outline_path}")
    print(f"output={output_path}")
    print(f"slides={len(slides)}")


if __name__ == "__main__":
    main()
