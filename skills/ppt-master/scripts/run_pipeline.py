#!/usr/bin/env python3
"""WorkBuddy wrapper for selected ppt-master pipeline stages.

This script does not replace the upstream project. It provides a stable wrapper
for project initialization, source import, validation, design spec scaffolding,
and the sequential post-processing/export chain required by ppt-master.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List


SUPPORTED_FORMATS = {
    "ppt169",
    "ppt43",
    "xhs",
    "story",
    "square",
    "wechat-cover",
    "a4",
}

ROOT = Path(__file__).resolve().parent
TEMPLATE_PATH = ROOT / "design_spec_template.md"
BRIEF_TO_BUNDLE_PATH = ROOT / "brief_to_bundle.py"
OUTLINE_TO_SLIDES_PATH = ROOT / "outline_to_slides.py"
BUNDLE_TO_NOTES_PATH = ROOT / "bundle_to_notes.py"
SLIDE_PLAN_TO_SVG_TASKS_PATH = ROOT / "slide_plan_to_svg_tasks.py"
SVG_TASKS_TO_PAGES_PATH = ROOT / "svg_tasks_to_pages.py"




def eprint(*args: object) -> None:

    print(*args, file=sys.stderr)


def resolve_repo(explicit: str | None) -> Path:
    candidates: List[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env_repo = os.environ.get("PPT_MASTER_REPO")
    if env_repo:
        candidates.append(Path(env_repo).expanduser())
    cwd = Path.cwd()
    candidates.extend(
        [
            cwd / "ppt-master",
            cwd.parent / "ppt-master",
            Path.home() / "ppt-master",
            Path.home() / "WorkBuddy" / "ppt-master",
        ]
    )

    checked = []
    for candidate in candidates:
        candidate = candidate.resolve()
        checked.append(str(candidate))
        if (candidate / "scripts" / "project_manager.py").exists():
            return candidate

    raise SystemExit(
        "未找到 ppt-master 仓库。请通过 --repo 指定，或设置环境变量 PPT_MASTER_REPO。\n"
        f"已检查位置:\n- " + "\n- ".join(checked)
    )


def ensure_file(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"缺少{label}: {path}")


def ensure_dir(path: Path, label: str) -> None:
    if not path.exists() or not path.is_dir():
        raise SystemExit(f"缺少{label}: {path}")


def run_cmd(cmd: Iterable[str], cwd: Path, dry_run: bool = False) -> None:
    rendered = " ".join(f'"{part}"' if " " in part else part for part in cmd)
    print(f"\n>>> {rendered}")
    if dry_run:
        return
    result = subprocess.run(list(cmd), cwd=str(cwd))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def normalize_project_path(project_path: str | None, project_root: str | None, project_name: str | None) -> Path:
    if project_path:
        return Path(project_path).expanduser().resolve()
    if not project_root or not project_name:
        raise SystemExit("必须提供 --project-path，或同时提供 --project-root 和 --project-name。")
    return (Path(project_root).expanduser() / project_name).resolve()


def project_scaffold_paths(project_path: Path) -> List[Path]:
    return [
        project_path / "sources",
        project_path / "images",
        project_path / "notes",
        project_path / "svg_output",
        project_path / "svg_final",
        project_path / "exports",
    ]


def build_template_content(
    template: str,
    project_name: str,
    fmt: str,
    viewbox: str,
    audience: str,
    slide_count: str,
    style: str,
    summary: str,
) -> str:
    replacements = {
        "- 项目名称：": f"- 项目名称：{project_name}",
        "- 一句话目标：": f"- 一句话目标：{summary}",
        "- 主要受众：": f"- 主要受众：{audience}",
        "- Format: ppt169": f"- Format: {fmt}",
        "- ViewBox: 0 0 1280 720": f"- ViewBox: {viewbox}",
        "- 目标页数：": f"- 目标页数：{slide_count}",
        "- 风格关键词：": f"- 风格关键词：{style}",
    }
    for old, new in replacements.items():
        template = template.replace(old, new, 1)
    return template


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


def cmd_check(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    required = [
        repo / "scripts" / "project_manager.py",
        repo / "scripts" / "total_md_split.py",
        repo / "scripts" / "finalize_svg.py",
        repo / "scripts" / "svg_to_pptx.py",
    ]
    for item in required:
        ensure_file(item, "脚本")

    ensure_file(TEMPLATE_PATH, "design_spec 模板")
    ensure_file(BRIEF_TO_BUNDLE_PATH, "brief_to_bundle 脚本")
    ensure_file(OUTLINE_TO_SLIDES_PATH, "outline_to_slides 脚本")
    ensure_file(BUNDLE_TO_NOTES_PATH, "bundle_to_notes 脚本")
    ensure_file(SLIDE_PLAN_TO_SVG_TASKS_PATH, "slide_plan_to_svg_tasks 脚本")
    ensure_file(SVG_TASKS_TO_PAGES_PATH, "svg_tasks_to_pages 脚本")

    print("ppt-master 仓库检查通过")
    print(f"repo={repo}")
    print(f"python={sys.executable}")
    print(f"template={TEMPLATE_PATH}")
    print(f"brief_bundle={BRIEF_TO_BUNDLE_PATH}")
    print(f"outline_slides={OUTLINE_TO_SLIDES_PATH}")
    print(f"bundle_notes={BUNDLE_TO_NOTES_PATH}")
    print(f"svg_tasks={SLIDE_PLAN_TO_SVG_TASKS_PATH}")
    print(f"svg_pages={SVG_TASKS_TO_PAGES_PATH}")






def cmd_scaffold(args: argparse.Namespace) -> None:
    project_path = normalize_project_path(args.project_path, args.project_root, args.project_name)
    if args.dry_run:
        print(f"将创建项目脚手架：{project_path}")
        for item in project_scaffold_paths(project_path):
            print(f"- {item}")
        print(f"- {project_path / 'design_spec.md'}")
        return

    project_path.mkdir(parents=True, exist_ok=True)
    for item in project_scaffold_paths(project_path):
        item.mkdir(parents=True, exist_ok=True)

    spec_path = project_path / "design_spec.md"
    if spec_path.exists() and not args.force:
        print(f"已存在 design_spec.md，保留原文件：{spec_path}")
    else:
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        filled = build_template_content(
            template=template,
            project_name=project_path.name,
            fmt=args.format,
            viewbox=infer_viewbox(args.format),
            audience=args.audience,
            slide_count=args.slide_count,
            style=args.style,
            summary=args.summary,
        )
        spec_path.write_text(filled, encoding="utf-8")
        print(f"已生成 design_spec.md：{spec_path}")

    print(f"项目脚手架已准备完成：{project_path}")


def cmd_bundle(args: argparse.Namespace) -> None:
    project_path = normalize_project_path(args.project_path, args.project_root, args.project_name)
    cmd = [
        sys.executable,
        str(BRIEF_TO_BUNDLE_PATH),
        "--brief",
        str(Path(args.brief).expanduser().resolve()),
        "--project-path",
        str(project_path),
    ]
    if args.force:
        cmd.append("--force")
    run_cmd(cmd, cwd=ROOT, dry_run=args.dry_run)


def cmd_slides(args: argparse.Namespace) -> None:
    project_path = normalize_project_path(args.project_path, args.project_root, args.project_name)
    cmd = [
        sys.executable,
        str(OUTLINE_TO_SLIDES_PATH),
        "--project-path",
        str(project_path),
    ]
    if args.outline:
        cmd.extend(["--outline", str(Path(args.outline).expanduser().resolve())])
    if args.output:
        cmd.extend(["--output", str(Path(args.output).expanduser().resolve())])
    if args.force:
        cmd.append("--force")
    run_cmd(cmd, cwd=ROOT, dry_run=args.dry_run)


def cmd_notes(args: argparse.Namespace) -> None:
    project_path = normalize_project_path(args.project_path, args.project_root, args.project_name)
    cmd = [
        sys.executable,
        str(BUNDLE_TO_NOTES_PATH),
        "--project-path",
        str(project_path),
    ]
    if args.slides:
        cmd.extend(["--slides", str(Path(args.slides).expanduser().resolve())])
    if args.output:
        cmd.extend(["--output", str(Path(args.output).expanduser().resolve())])
    if args.force:
        cmd.append("--force")
    run_cmd(cmd, cwd=ROOT, dry_run=args.dry_run)


def cmd_svg_tasks(args: argparse.Namespace) -> None:
    project_path = normalize_project_path(args.project_path, args.project_root, args.project_name)
    cmd = [
        sys.executable,
        str(SLIDE_PLAN_TO_SVG_TASKS_PATH),
        "--project-path",
        str(project_path),
    ]
    if args.slides:
        cmd.extend(["--slides", str(Path(args.slides).expanduser().resolve())])
    if args.tasks_dir:
        cmd.extend(["--tasks-dir", str(Path(args.tasks_dir).expanduser().resolve())])
    if args.manifest:
        cmd.extend(["--manifest", str(Path(args.manifest).expanduser().resolve())])
    if args.format:
        cmd.extend(["--format", args.format])
    if args.viewbox:
        cmd.extend(["--viewbox", args.viewbox])
    if args.create_svg_stubs:
        cmd.append("--create-svg-stubs")
    if args.force:
        cmd.append("--force")
    run_cmd(cmd, cwd=ROOT, dry_run=args.dry_run)


def cmd_svg_pages(args: argparse.Namespace) -> None:
    project_path = normalize_project_path(args.project_path, args.project_root, args.project_name)
    cmd = [
        sys.executable,
        str(SVG_TASKS_TO_PAGES_PATH),
        "--project-path",
        str(project_path),
    ]
    if args.tasks_dir:
        cmd.extend(["--tasks-dir", str(Path(args.tasks_dir).expanduser().resolve())])
    if args.output_dir:
        cmd.extend(["--output-dir", str(Path(args.output_dir).expanduser().resolve())])
    if args.manifest:
        cmd.extend(["--manifest", str(Path(args.manifest).expanduser().resolve())])
    if args.format:
        cmd.extend(["--format", args.format])
    if args.viewbox:
        cmd.extend(["--viewbox", args.viewbox])
    if getattr(args, "theme", None):
        cmd.extend(["--theme", args.theme])
    if args.force:
        cmd.append("--force")

    run_cmd(cmd, cwd=ROOT, dry_run=args.dry_run)


def cmd_init(args: argparse.Namespace) -> None:



    repo = resolve_repo(args.repo)
    if args.format not in SUPPORTED_FORMATS:
        print(f"警告：格式 {args.format} 不在包装脚本内置列表中，仍尝试交给上游处理。")
    root = Path(args.project_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "scripts/project_manager.py", "init", args.project_name, "--format", args.format]
    run_cmd(cmd, cwd=repo, dry_run=args.dry_run)

    expected = root / args.project_name
    if not expected.exists() and not args.dry_run:
        print(f"提示：上游脚本可能在其默认目录创建项目，请检查输出。预期路径：{expected}")
    else:
        print(f"项目初始化目标：{expected}")





def cmd_import(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    project_path = normalize_project_path(args.project_path, args.project_root, args.project_name)
    sources = [str(Path(item).expanduser().resolve()) for item in args.sources]
    missing = [item for item in sources if not Path(item).exists()]
    if missing:
        raise SystemExit("以下源文件不存在:\n- " + "\n- ".join(missing))
    cmd = [sys.executable, "scripts/project_manager.py", "import-sources", str(project_path), *sources]
    cmd.append("--move" if args.move else "--copy")
    run_cmd(cmd, cwd=repo, dry_run=args.dry_run)


def cmd_validate(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    project_path = normalize_project_path(args.project_path, args.project_root, args.project_name)
    cmd = [sys.executable, "scripts/project_manager.py", "validate", str(project_path)]
    run_cmd(cmd, cwd=repo, dry_run=args.dry_run)


def cmd_finalize(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    project_path = normalize_project_path(args.project_path, args.project_root, args.project_name)
    ensure_dir(project_path / "svg_output", "svg_output 目录")
    ensure_file(project_path / "notes" / "total.md", "notes/total.md")

    run_cmd([sys.executable, "scripts/total_md_split.py", str(project_path)], cwd=repo, dry_run=args.dry_run)
    run_cmd([sys.executable, "scripts/finalize_svg.py", str(project_path)], cwd=repo, dry_run=args.dry_run)
    if args.skip_export:
        return
    run_cmd([sys.executable, "scripts/svg_to_pptx.py", str(project_path), "-s", "final"], cwd=repo, dry_run=args.dry_run)


def cmd_run(args: argparse.Namespace) -> None:
    repo = resolve_repo(args.repo)
    project_path = normalize_project_path(args.project_path, args.project_root, args.project_name)

    if args.scaffold:
        scaffold_args = argparse.Namespace(
            project_path=str(project_path),
            project_root=None,
            project_name=None,
            format=args.format,
            audience=args.audience,
            slide_count=args.slide_count,
            style=args.style,
            summary=args.summary,
            force=args.force,
            dry_run=args.dry_run,
        )
        cmd_scaffold(scaffold_args)

    if args.bundle:
        if not args.brief:
            raise SystemExit("启用 --bundle 时必须同时提供 --brief。")
        bundle_args = argparse.Namespace(
            brief=args.brief,
            project_path=str(project_path),
            project_root=None,
            project_name=None,
            force=args.force,
            dry_run=args.dry_run,
        )
        cmd_bundle(bundle_args)

    if args.slides_stage:
        slides_args = argparse.Namespace(
            project_path=str(project_path),
            project_root=None,
            project_name=None,
            outline=args.outline,
            output=args.slides_output,
            force=args.force,
            dry_run=args.dry_run,
        )
        cmd_slides(slides_args)

    if args.notes_stage:
        notes_args = argparse.Namespace(
            project_path=str(project_path),
            project_root=None,
            project_name=None,
            slides=args.slides_input,
            output=args.notes_output,
            force=args.force,
            dry_run=args.dry_run,
        )
        cmd_notes(notes_args)

    if args.svg_tasks_stage:
        svg_tasks_args = argparse.Namespace(
            project_path=str(project_path),
            project_root=None,
            project_name=None,
            slides=args.svg_tasks_slides,
            tasks_dir=args.tasks_dir,
            manifest=args.svg_manifest,
            format=args.svg_format,
            viewbox=args.svg_viewbox,
            create_svg_stubs=args.create_svg_stubs,
            force=args.force,
            dry_run=args.dry_run,
        )
        cmd_svg_tasks(svg_tasks_args)

    if args.svg_pages_stage:
        svg_pages_args = argparse.Namespace(
            project_path=str(project_path),
            project_root=None,
            project_name=None,
            tasks_dir=args.svg_pages_tasks_dir,
            output_dir=args.svg_pages_output_dir,
            manifest=args.svg_pages_manifest,
            format=args.svg_pages_format,
            viewbox=args.svg_pages_viewbox,
            theme=args.theme,
            force=args.force,
            dry_run=args.dry_run,

        )
        cmd_svg_pages(svg_pages_args)

    if args.init:



        init_args = argparse.Namespace(
            repo=str(repo),
            project_root=args.project_root,
            project_name=args.project_name,
            format=args.format,
            dry_run=args.dry_run,
        )
        cmd_init(init_args)

    if args.sources:

        import_args = argparse.Namespace(
            repo=str(repo),
            project_path=str(project_path),
            project_root=None,
            project_name=None,
            sources=args.sources,
            move=args.move,
            dry_run=args.dry_run,
        )
        cmd_import(import_args)

    if args.validate:
        validate_args = argparse.Namespace(
            repo=str(repo),
            project_path=str(project_path),
            project_root=None,
            project_name=None,
            dry_run=args.dry_run,
        )
        cmd_validate(validate_args)

    if args.finalize:
        finalize_args = argparse.Namespace(
            repo=str(repo),
            project_path=str(project_path),
            project_root=None,
            project_name=None,
            skip_export=args.skip_export,
            dry_run=args.dry_run,
        )
        cmd_finalize(finalize_args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WorkBuddy wrapper for ppt-master pipeline stages")
    parser.add_argument("--repo", help="ppt-master 仓库根目录；未提供时会自动探测")

    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="检查仓库和关键脚本是否存在")
    check.set_defaults(func=cmd_check)

    scaffold = subparsers.add_parser("scaffold", help="创建项目脚手架并生成 design_spec 模板")
    scaffold.add_argument("--project-path", help="项目目录")
    scaffold.add_argument("--project-root", help="项目父目录")
    scaffold.add_argument("--project-name", help="项目名称")
    scaffold.add_argument("--format", default="ppt169", help="画布格式")
    scaffold.add_argument("--audience", default="待补充", help="目标受众")
    scaffold.add_argument("--slide-count", default="待补充", help="目标页数")
    scaffold.add_argument("--style", default="商务 / 科技 / 极简（待定）", help="风格关键词")
    scaffold.add_argument("--summary", default="待补充项目目标", help="一句话目标")
    scaffold.add_argument("--force", action="store_true", help="覆盖已有 design_spec.md")
    scaffold.add_argument("--dry-run", action="store_true", help="仅打印将执行内容，不落盘")
    scaffold.set_defaults(func=cmd_scaffold)

    bundle = subparsers.add_parser("bundle", help="把结构化 brief 生成为 design_spec、brief 和 outline 项目包")
    bundle.add_argument("--brief", required=True, help="brief JSON 文件路径")
    bundle.add_argument("--project-path", help="项目目录")
    bundle.add_argument("--project-root", help="项目父目录")
    bundle.add_argument("--project-name", help="项目名称")
    bundle.add_argument("--force", action="store_true", help="覆盖已有规划文件")
    bundle.add_argument("--dry-run", action="store_true", help="仅打印命令，不执行")
    bundle.set_defaults(func=cmd_bundle)

    init = subparsers.add_parser("init", help="初始化 ppt 项目")
    init.add_argument("--project-root", required=True, help="项目父目录")
    init.add_argument("--project-name", required=True, help="项目名称")
    init.add_argument("--format", default="ppt169", help="画布格式，例如 ppt169 / ppt43 / xhs")
    init.add_argument("--dry-run", action="store_true", help="仅打印命令，不执行")
    init.set_defaults(func=cmd_init)

    slides = subparsers.add_parser("slides", help="根据 outline.md 生成逐页 slides.md 计划")
    slides.add_argument("--project-path", help="项目目录")
    slides.add_argument("--project-root", help="项目父目录")
    slides.add_argument("--project-name", help="项目名称")
    slides.add_argument("--outline", help="自定义 outline.md 路径")
    slides.add_argument("--output", help="输出 slides.md 路径")
    slides.add_argument("--force", action="store_true", help="覆盖已有 slides.md")
    slides.add_argument("--dry-run", action="store_true", help="仅打印命令，不执行")
    slides.set_defaults(func=cmd_slides)

    notes = subparsers.add_parser("notes", help="根据规划包生成 notes/total.md 初稿")
    notes.add_argument("--project-path", help="项目目录")
    notes.add_argument("--project-root", help="项目父目录")
    notes.add_argument("--project-name", help="项目名称")
    notes.add_argument("--slides", help="自定义 slides.md 路径")
    notes.add_argument("--output", help="输出 total.md 路径")
    notes.add_argument("--force", action="store_true", help="覆盖已有 total.md")
    notes.add_argument("--dry-run", action="store_true", help="仅打印命令，不执行")
    notes.set_defaults(func=cmd_notes)

    svg_tasks = subparsers.add_parser("svg-tasks", help="根据 slides.md 生成逐页 SVG 任务单和可选 stub")
    svg_tasks.add_argument("--project-path", help="项目目录")
    svg_tasks.add_argument("--project-root", help="项目父目录")
    svg_tasks.add_argument("--project-name", help="项目名称")
    svg_tasks.add_argument("--slides", help="自定义 slides.md 路径")
    svg_tasks.add_argument("--tasks-dir", help="任务输出目录，默认 <project>/tasks")
    svg_tasks.add_argument("--manifest", help="manifest 输出路径，默认 <project>/svg_output_manifest.json")
    svg_tasks.add_argument("--format", help="显式指定画布格式")
    svg_tasks.add_argument("--viewbox", help="显式指定 viewBox")
    svg_tasks.add_argument("--create-svg-stubs", action="store_true", help="同时生成 svg_output/*.svg 占位文件")
    svg_tasks.add_argument("--force", action="store_true", help="覆盖已有任务文件和 stub")
    svg_tasks.add_argument("--dry-run", action="store_true", help="仅打印命令，不执行")
    svg_tasks.set_defaults(func=cmd_svg_tasks)

    svg_pages = subparsers.add_parser("svg-pages", help="根据任务单生成真实 SVG 草稿页")
    svg_pages.add_argument("--project-path", help="项目目录")
    svg_pages.add_argument("--project-root", help="项目父目录")
    svg_pages.add_argument("--project-name", help="项目名称")
    svg_pages.add_argument("--tasks-dir", help="任务目录，默认 <project>/tasks")
    svg_pages.add_argument("--output-dir", help="SVG 输出目录，默认 <project>/svg_output")
    svg_pages.add_argument("--manifest", help="SVG 草稿 manifest 输出路径，默认 <project>/svg_page_drafts.json")
    svg_pages.add_argument("--format", help="显式指定画布格式")
    svg_pages.add_argument("--viewbox", help="显式指定 viewBox")
    svg_pages.add_argument("--theme", help="显式指定主题，如 tech-blue、consulting")
    svg_pages.add_argument("--force", action="store_true", help="覆盖已有 SVG 草稿")

    svg_pages.add_argument("--dry-run", action="store_true", help="仅打印命令，不执行")
    svg_pages.set_defaults(func=cmd_svg_pages)

    imp = subparsers.add_parser("import", help="导入源文件到项目")




    imp.add_argument("--project-path", help="项目目录")
    imp.add_argument("--project-root", help="项目父目录")
    imp.add_argument("--project-name", help="项目名称")
    imp.add_argument("sources", nargs="+", help="待导入的源文件")
    imp.add_argument("--move", action="store_true", help="使用上游推荐的 --move 模式")
    imp.add_argument("--copy", dest="move", action="store_false", help="使用复制模式")
    imp.set_defaults(move=True)
    imp.add_argument("--dry-run", action="store_true", help="仅打印命令，不执行")
    imp.set_defaults(func=cmd_import)

    validate = subparsers.add_parser("validate", help="校验项目结构")
    validate.add_argument("--project-path", help="项目目录")
    validate.add_argument("--project-root", help="项目父目录")
    validate.add_argument("--project-name", help="项目名称")
    validate.add_argument("--dry-run", action="store_true", help="仅打印命令，不执行")
    validate.set_defaults(func=cmd_validate)

    finalize = subparsers.add_parser("finalize", help="按上游规范顺序执行 total_md_split、finalize_svg、svg_to_pptx")
    finalize.add_argument("--project-path", help="项目目录")
    finalize.add_argument("--project-root", help="项目父目录")
    finalize.add_argument("--project-name", help="项目名称")
    finalize.add_argument("--skip-export", action="store_true", help="只做拆分和 SVG 后处理，不导出 PPTX")
    finalize.add_argument("--dry-run", action="store_true", help="仅打印命令，不执行")
    finalize.set_defaults(func=cmd_finalize)

    run = subparsers.add_parser("run", help="组合执行 scaffold/bundle/slides/notes/svg-tasks/svg-pages/init/import/validate/finalize")
    run.add_argument("--project-path", help="项目目录")
    run.add_argument("--project-root", required=True, help="项目父目录")
    run.add_argument("--project-name", required=True, help="项目名称")
    run.add_argument("--format", default="ppt169", help="画布格式")
    run.add_argument("--audience", default="待补充", help="目标受众")
    run.add_argument("--slide-count", default="待补充", help="目标页数")
    run.add_argument("--style", default="商务 / 科技 / 极简（待定）", help="风格关键词")
    run.add_argument("--summary", default="待补充项目目标", help="一句话目标")
    run.add_argument("--brief", help="brief JSON 文件路径；与 --bundle 配合使用")
    run.add_argument("--outline", help="slides 阶段使用的 outline.md 路径")
    run.add_argument("--slides-output", help="slides 阶段输出路径")
    run.add_argument("--slides-input", help="notes 阶段读取的 slides.md 路径")
    run.add_argument("--notes-output", help="notes 阶段输出 total.md 路径")
    run.add_argument("--svg-tasks-slides", help="svg-tasks 阶段读取的 slides.md 路径")
    run.add_argument("--tasks-dir", help="svg-tasks 阶段任务输出目录")
    run.add_argument("--svg-manifest", help="svg-tasks 阶段 manifest 输出路径")
    run.add_argument("--svg-format", help="svg-tasks 阶段显式指定画布格式")
    run.add_argument("--svg-viewbox", help="svg-tasks 阶段显式指定 viewBox")
    run.add_argument("--svg-pages-tasks-dir", help="svg-pages 阶段任务目录")
    run.add_argument("--svg-pages-output-dir", help="svg-pages 阶段 SVG 输出目录")
    run.add_argument("--svg-pages-manifest", help="svg-pages 阶段 manifest 输出路径")
    run.add_argument("--svg-pages-format", help="svg-pages 阶段显式指定画布格式")
    run.add_argument("--svg-pages-viewbox", help="svg-pages 阶段显式指定 viewBox")
    run.add_argument("--theme", help="svg-pages 阶段显式指定主题，如 tech-blue、consulting")

    run.add_argument("--sources", nargs="*", default=[], help="待导入的源文件")

    run.add_argument("--move", action="store_true", help="导入时使用 --move")
    run.add_argument("--copy", dest="move", action="store_false", help="导入时使用复制模式")
    run.set_defaults(move=True)
    run.add_argument("--scaffold", action="store_true", help="创建项目脚手架和 design_spec 模板")
    run.add_argument("--bundle", action="store_true", help="根据 brief JSON 生成项目规划包")
    run.add_argument("--slides-stage", action="store_true", help="根据 outline 生成逐页 slides 计划")
    run.add_argument("--notes-stage", action="store_true", help="根据规划包生成 notes/total.md")
    run.add_argument("--svg-tasks-stage", action="store_true", help="根据 slides 生成 SVG 任务单和可选 stub")
    run.add_argument("--svg-pages-stage", action="store_true", help="根据任务单生成真实 SVG 草稿页")
    run.add_argument("--create-svg-stubs", action="store_true", help="在 svg-tasks 阶段同时生成 svg_output 占位文件")
    run.add_argument("--force", action="store_true", help="覆盖已有 design_spec.md / 规划文件 / 任务文件 / SVG 草稿")
    run.add_argument("--init", action="store_true", help="执行项目初始化")
    run.add_argument("--validate", action="store_true", help="执行项目校验")
    run.add_argument("--finalize", action="store_true", help="执行后处理与导出")

    run.add_argument("--skip-export", action="store_true", help="与 --finalize 配合，只做后处理不导出")
    run.add_argument("--dry-run", action="store_true", help="仅打印命令，不执行")
    run.set_defaults(func=cmd_run)




    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
