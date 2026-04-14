#!/usr/bin/env python3
"""Generate notes/total.md from planning artifacts.

This script consolidates design_spec.md, sources/brief.md, notes/outline.md, and
notes/slides.md into a speaker-notes style draft that downstream ppt-master
steps can keep refining.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List


SLIDE_RE = re.compile(r"^##\s+Slide\s+(\d+):\s*(.+?)\s*$")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_value(text: str, label: str, default: str = "待补充") -> str:
    match = re.search(rf"{re.escape(label)}\s*(.+)", text)
    if match:
        value = match.group(1).strip()
        if value:
            return value
    return default


def extract_section(text: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "待补充"


def parse_slides(slides_text: str) -> List[dict]:
    slides: List[dict] = []
    current: dict | None = None
    for raw_line in slides_text.splitlines():
        line = raw_line.rstrip()
        slide_match = SLIDE_RE.match(line)
        if slide_match:
            if current:
                slides.append(current)
            current = {
                "index": int(slide_match.group(1)),
                "title": slide_match.group(2).strip(),
                "goal": "待补充",
                "message": "待补充",
                "evidence": "待补充",
                "layout": "待补充",
                "notes": "待补充",
            }
            continue
        if not current:
            continue
        if line.startswith("- 页面目标："):
            current["goal"] = line.split("：", 1)[1].strip() or "待补充"
        elif line.startswith("- 核心信息："):
            current["message"] = line.split("：", 1)[1].strip() or "待补充"
        elif line.startswith("- 支撑数据/案例："):
            current["evidence"] = line.split("：", 1)[1].strip() or "待补充"
        elif line.startswith("- 建议版式："):
            current["layout"] = line.split("：", 1)[1].strip() or "待补充"
        elif line.startswith("- 备注："):
            current["notes"] = line.split("：", 1)[1].strip() or "待补充"
    if current:
        slides.append(current)
    return slides


def build_total_md(project_path: Path, design_spec: str, brief_text: str, outline_text: str, slides: List[dict]) -> str:
    summary = extract_value(design_spec, "- 一句话目标：")
    audience = extract_value(design_spec, "- 主要受众：")
    fmt = extract_value(design_spec, "- Format:")
    style = extract_value(design_spec, "- 风格关键词：")
    source_summary = extract_section(brief_text, "Source Summary")

    lines = [
        "# Speaker Notes",
        "",
        f"- 项目目录：{project_path}",
        f"- 一句话目标：{summary}",
        f"- 目标受众：{audience}",
        f"- 输出格式：{fmt}",
        f"- 风格关键词：{style}",
        "",
        "## 全局说明",
        f"- 内容来源概述：{source_summary}",
        "- 使用方式：本文件作为逐页备注初稿，供 agent 和后续生成链继续打磨。",
        "",
        "## 大纲来源",
        outline_text.strip() or "待补充",
        "",
        "## 逐页备注",
        "",
    ]

    for slide in slides:
        lines.extend(
            [
                f"### Slide {slide['index']}: {slide['title']}",
                f"- 页面目标：{slide['goal']}",
                f"- 讲述重点：{slide['message']}",
                f"- 支撑数据/案例：{slide['evidence']}",
                f"- 版式提醒：{slide['layout']}",
                f"- 讲者备注：{slide['notes']}",
                "- 过渡建议：承接上一页并引出下一页，避免机械念稿。",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate notes/total.md from planning bundle")
    parser.add_argument("--project-path", required=True, help="项目目录")
    parser.add_argument("--slides", help="slides.md 路径，默认 notes/slides.md")
    parser.add_argument("--output", help="输出 total.md 路径，默认 notes/total.md")
    parser.add_argument("--force", action="store_true", help="覆盖已有 total.md")
    args = parser.parse_args()

    project_path = Path(args.project_path).expanduser().resolve()
    design_spec_path = project_path / "design_spec.md"
    brief_path = project_path / "sources" / "brief.md"
    outline_path = project_path / "notes" / "outline.md"
    slides_path = Path(args.slides).expanduser().resolve() if args.slides else project_path / "notes" / "slides.md"
    output_path = Path(args.output).expanduser().resolve() if args.output else project_path / "notes" / "total.md"

    required = [design_spec_path, brief_path, outline_path, slides_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("缺少生成 notes/total.md 所需文件:\n- " + "\n- ".join(missing))
    if output_path.exists() and not args.force:
        raise SystemExit(f"输出文件已存在，请使用 --force 覆盖: {output_path}")

    slides = parse_slides(read_text(slides_path))
    if not slides:
        raise SystemExit(f"未从 slides 文件解析出页面: {slides_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_total_md(
            project_path=project_path,
            design_spec=read_text(design_spec_path),
            brief_text=read_text(brief_path),
            outline_text=read_text(outline_path),
            slides=slides,
        ),
        encoding="utf-8",
    )

    print(f"project={project_path}")
    print(f"slides={slides_path}")
    print(f"output={output_path}")
    print(f"notes={len(slides)}")


if __name__ == "__main__":
    main()
