# 执行接线说明

## 这份文档在说什么
这个包装层不是为了替代上游 `ppt-master`，而是为了让 WorkBuddy / agent 在几个稳定阶段上有一条可重复、可检查、少翻车的执行入口。

## 当前包装了哪些阶段
### 1. `check`
检查：
- 是否能找到 `ppt-master` 仓库
- `project_manager.py`
- `total_md_split.py`
- `finalize_svg.py`
- `svg_to_pptx.py`
- `design_spec_template.md`

### 2. `scaffold`
创建项目脚手架并生成 `design_spec.md` 初稿：
- `sources/`
- `images/`
- `notes/`
- `svg_output/`
- `svg_final/`
- `exports/`
- `design_spec.md`

### 3. `bundle`
把结构化 brief 写成：
- `design_spec.md`
- `sources/brief.md`
- `notes/outline.md`
- `images/image_prompts.md`（如需要）

### 4. `init`
调用上游 `project_manager.py init` 初始化项目。

### 5. `import`
把源文件导入项目目录。

### 6. `validate`
调用上游校验项目结构。

### 7. `slides`
把 `notes/outline.md` 扩成 `notes/slides.md`，固定逐页计划。

### 8. `notes`
把 `design_spec.md`、`sources/brief.md`、`notes/outline.md`、`notes/slides.md` 汇总成 `notes/total.md` 初稿。

### 9. `finalize`

严格顺序执行：
1. `total_md_split.py`
2. `finalize_svg.py`
3. `svg_to_pptx.py -s final`

### 10. `run`
组合执行 `scaffold / bundle / slides / notes / init / import / validate / finalize`。



## 典型使用方式
### 先创建工作台
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py scaffold --project-root C:\work\ppt-jobs --project-name q3-report --format ppt169 --audience 投资人 --slide-count 10 --style 科技极简 --summary Q3 业务汇报
```

### 然后初始化上游项目
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py --repo C:\path\to\ppt-master init --project-root C:\work\ppt-jobs --project-name q3-report --format ppt169
```

### 再导入源文件
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py --repo C:\path\to\ppt-master import --project-path C:\work\ppt-jobs\q3-report C:\input\report.pdf --move
```

### 把大纲展开成逐页计划
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py slides --project-path C:\work\ppt-jobs\q3-report
```

### 把规划文件汇总为备注初稿
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py notes --project-path C:\work\ppt-jobs\q3-report
```

## 重要边界

### 1. 这不是全自动 PPT 工厂
它只包装稳定阶段，不负责替你理解内容、决定风格、写完所有页面。

### 2. `scaffold` 不是设计完成
它只是把项目工作台和 `design_spec.md` 骨架搭起来。真正的设计规范仍然需要 agent 补齐。

### 3. `finalize` 前必须有中间产物
至少要有：
- `svg_output/`
- `notes/total.md`

没有这两项，说明 Executor 还没干完活，不能强行导出。

### 4. `import --move` 会移动源文件
如果用户不接受移动原文件，应改用 `--copy`。

## 推荐策略
- 第一次跑流程时，优先 `--dry-run`
- 初次建项目时，先 `scaffold` 再 `init`
- 导出前，先人工检查 `design_spec.md`、`svg_output/`、`notes/total.md`
- 交付时，尽量一起提供规范、备注、SVG 和 PPTX
