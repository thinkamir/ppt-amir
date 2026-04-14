#!/usr/bin/env python3
"""Generate a reusable ppt-master project bundle from a brief.

This helper turns a compact JSON brief into the stable planning artifacts used by
WorkBuddy's ppt-master skill and agent.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent
TEMPLATE_PATH = ROOT / "design_spec_template.md"

DEFAULT_OUTLINE = [
    "封面",
    "背景 / 问题",
    "方案 / 方法",
    "关键亮点",
    "数据 / 证据",
    "案例 / 演示",
    "结论 / 行动建议",
]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def text_or_default(value: Any, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def normalize_list(value: Any, default: List[str] | None = None) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        items = [item.strip() for item in value.split("\n") if item.strip()]
        return items or (default or [])
    return list(default or [])


def infer_viewbox(fmt: str) -> str:
    mapping = {
        "ppt169": "0 0 1280 720",
        "ppt43": "0 0 1024 768",
        "xhs": "0 0 1242 1660",
        "square": "0 0 1080 1080",
        "story": "0 0 1080 1920",
        "wechat-cover": "0 0 900 383",
        "a4": "0 0 1240 1754",
    }
    return mapping.get(fmt, "请按实际格式补充 viewBox")


def build_design_spec(data: Dict[str, Any], template: str) -> str:
    project_name = text_or_default(data.get("project_name"), "未命名项目")
    summary = text_or_default(data.get("summary"), "待补充项目目标")
    audience = text_or_default(data.get("audience"), "待补充")
    fmt = text_or_default(data.get("format"), "ppt169")
    slide_count = text_or_default(data.get("slide_count"), "待补充")
    style = text_or_default(data.get("style"), "商务 / 科技 / 极简（待定）")

    replacements = {
        "- 项目名称：": f"- 项目名称：{project_name}",
        "- 一句话目标：": f"- 一句话目标：{summary}",
        "- 主要受众：": f"- 主要受众：{audience}",
        "- Format: ppt169": f"- Format: {fmt}",
        "- ViewBox: 0 0 1280 720": f"- ViewBox: {infer_viewbox(fmt)}",
        "- 目标页数：": f"- 目标页数：{slide_count}",
        "- 风格关键词：": f"- 风格关键词：{style}",
    }
    for old, new in replacements.items():
        template = template.replace(old, new, 1)

    extra_replacements = {
        "- 核心信息源：": f"- 核心信息源：{text_or_default(data.get('source_summary'), '待补充')}",
        "- 使用场景：": f"- 使用场景：{text_or_default(data.get('usage_scenario'), '待补充')}",
        "- 他们最关心什么：": f"- 他们最关心什么：{text_or_default(data.get('audience_focus'), '待补充')}",
        "- 允许浮动范围：": f"- 允许浮动范围：{text_or_default(data.get('slide_range'), '±2 页')}",
        "- 整体气质：": f"- 整体气质：{text_or_default(data.get('tone'), '清晰、可信、可落地')}",
        "- 参考方向：": f"- 参考方向：{text_or_default(data.get('reference_direction'), '待补充')}",
        "- 不要出现的风格：": f"- 不要出现的风格：{text_or_default(data.get('avoid_style'), '廉价感、信息爆炸、花哨动效')}",
        "- 主色：": f"- 主色：{text_or_default(data.get('primary_color'), '待补充')}",
        "- 辅助色：": f"- 辅助色：{text_or_default(data.get('secondary_color'), '待补充')}",
        "- 强调色：": f"- 强调色：{text_or_default(data.get('accent_color'), '待补充')}",
        "- 背景色：": f"- 背景色：{text_or_default(data.get('background_color'), '待补充')}",
        "- 禁用颜色：": f"- 禁用颜色：{text_or_default(data.get('forbidden_colors'), '待补充')}",
        "- 中文字体：": f"- 中文字体：{text_or_default(data.get('font_zh'), '待补充')}",
        "- 英文字体：": f"- 英文字体：{text_or_default(data.get('font_en'), '待补充')}",
        "- 标题层级：": f"- 标题层级：{text_or_default(data.get('heading_scale'), '待补充')}",
        "- 正文字号策略：": f"- 正文字号策略：{text_or_default(data.get('body_font_strategy'), '待补充')}",
        "- 图标风格：": f"- 图标风格：{text_or_default(data.get('icon_style'), '待补充')}",
        "- 是否统一描边：": f"- 是否统一描边：{text_or_default(data.get('icon_stroke'), '待补充')}",
        "- 是否允许 emoji：": f"- 是否允许 emoji：{text_or_default(data.get('allow_emoji'), '否')}",
        "- 图片来源：真实图片 / 品牌图库 / AI generation / 无图片": f"- 图片来源：{text_or_default(data.get('image_strategy'), '待补充')}",
        "- 使用原则：": f"- 使用原则：{text_or_default(data.get('image_rule'), '待补充')}",
        "- 禁用类型：": f"- 禁用类型：{text_or_default(data.get('image_forbidden'), '待补充')}",
    }
    for old, new in extra_replacements.items():
        template = template.replace(old, new, 1)

    outline = normalize_list(data.get("content_outline"), DEFAULT_OUTLINE)
    outline_md = "\n".join(f"{idx}. {item}" for idx, item in enumerate(outline, start=1))
    start = template.index("1. 封面")
    end = template.index("# Page-by-page Plan")
    template = template[:start] + outline_md + "\n\n" + template[end:]

    pages = data.get("page_plan")
    if isinstance(pages, list) and pages:
        page_blocks = []
        for idx, item in enumerate(pages, start=1):
            if not isinstance(item, dict):
                continue
            page_blocks.append(
                "\n".join(
                    [
                        f"## Slide {idx}",
                        f"- 目标：{text_or_default(item.get('goal'), '待补充')}",
                        f"- 核心文案：{text_or_default(item.get('copy'), '待补充')}",
                        f"- 建议版式：{text_or_default(item.get('layout'), '待补充')}",
                        f"- 视觉重点：{text_or_default(item.get('visual_focus'), '待补充')}",
                    ]
                )
            )
        if page_blocks:
            page_start = template.index("## Slide 1")
            asset_idx = template.index("# Asset Checklist")
            template = template[:page_start] + "\n\n".join(page_blocks) + "\n\n" + template[asset_idx:]

    return template


def build_brief_md(data: Dict[str, Any]) -> str:
    lines = [
        "# Project Brief",
        f"- 项目名称：{text_or_default(data.get('project_name'), '未命名项目')}",
        f"- 一句话目标：{text_or_default(data.get('summary'), '待补充项目目标')}",
        f"- 输入类型：{text_or_default(data.get('input_type'), '待补充')}",
        f"- 目标受众：{text_or_default(data.get('audience'), '待补充')}",
        f"- 输出比例：{text_or_default(data.get('format'), 'ppt169')}",
        f"- 目标页数：{text_or_default(data.get('slide_count'), '待补充')}",
        f"- 风格关键词：{text_or_default(data.get('style'), '待补充')}",
        f"- 图片策略：{text_or_default(data.get('image_strategy'), '待补充')}",
        "",
        "## Source Summary",
        text_or_default(data.get('source_summary'), '待补充'),
        "",
        "## Must Include",
    ]
    must_include = normalize_list(data.get("must_include"), ["待补充"])
    lines.extend([f"- {item}" for item in must_include])
    lines.extend(["", "## Must Avoid"])
    must_avoid = normalize_list(data.get("must_avoid"), ["待补充"])
    lines.extend([f"- {item}" for item in must_avoid])
    lines.extend(["", "## Notes", text_or_default(data.get("notes"), "待补充")])
    return "\n".join(lines) + "\n"


def build_outline_md(data: Dict[str, Any]) -> str:
    outline = normalize_list(data.get("content_outline"), DEFAULT_OUTLINE)
    lines = ["# Outline", ""]
    for idx, item in enumerate(outline, start=1):
        lines.append(f"## Section {idx}: {item}")
        lines.append("- 目标：待补充")
        lines.append("- 关键论点：待补充")
        lines.append("- 需要的数据/案例：待补充")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_image_prompts_md(data: Dict[str, Any]) -> str:
    prompts = data.get("image_prompts")
    prompt_list = normalize_list(prompts)
    lines = [
        "# Image Prompts",
        "",
        f"- 图片策略：{text_or_default(data.get('image_strategy'), '待补充')}",
        f"- 风格关键词：{text_or_default(data.get('style'), '待补充')}",
        "",
    ]
    if not prompt_list:
        lines.append("当前未提供具体 prompt，请由 agent 根据 design_spec.md 补充。")
    else:
        for idx, prompt in enumerate(prompt_list, start=1):
            lines.append(f"## Prompt {idx}")
            lines.append(prompt)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def generate_bundle(brief_path: Path, project_path: Path, force: bool) -> List[Path]:
    data = read_json(brief_path)
    project_path.mkdir(parents=True, exist_ok=True)
    for child in ["sources", "images", "notes", "svg_output", "svg_final", "exports"]:
        (project_path / child).mkdir(parents=True, exist_ok=True)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    outputs = {
        project_path / "design_spec.md": build_design_spec(data, template),
        project_path / "sources" / "brief.md": build_brief_md(data),
        project_path / "notes" / "outline.md": build_outline_md(data),
    }

    image_strategy = text_or_default(data.get("image_strategy"), "").lower()
    if "ai" in image_strategy or normalize_list(data.get("image_prompts")):
        outputs[project_path / "images" / "image_prompts.md"] = build_image_prompts_md(data)

    written = []
    for path, content in outputs.items():
        if path.exists() and not force:
            continue
        ensure_parent(path)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ppt-master planning bundle from a JSON brief")
    parser.add_argument("--brief", required=True, help="brief JSON 文件路径")
    parser.add_argument("--project-path", required=True, help="目标项目目录")
    parser.add_argument("--force", action="store_true", help="覆盖已存在文件")
    args = parser.parse_args()

    brief_path = Path(args.brief).expanduser().resolve()
    project_path = Path(args.project_path).expanduser().resolve()
    written = generate_bundle(brief_path, project_path, args.force)

    print(f"brief={brief_path}")
    print(f"project={project_path}")
    if written:
        print("已生成文件:")
        for item in written:
            print(f"- {item}")
    else:
        print("没有写入新文件；目标文件已存在。可加 --force 覆盖。")


if __name__ == "__main__":
    main()
