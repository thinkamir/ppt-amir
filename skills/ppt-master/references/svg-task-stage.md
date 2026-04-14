# SVG Task Stage

这一阶段的目标不是直接生成最终视觉稿，而是把 `notes/slides.md` 变成稳定、可执行的页面任务清单，避免 agent 每次都从零临场发挥。

## 输入
- `notes/slides.md`
- `design_spec.md`（可选，用于推断 Format）

## 输出
- `tasks/slide-01.md`、`tasks/slide-02.md` ...
- `svg_output/slide-01.svg` 等占位文件（可选）
- `svg_output_manifest.json`

## 推荐命令
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\slide_plan_to_svg_tasks.py --project-path C:\work\ppt-jobs\q3-report --create-svg-stubs
```

或通过统一入口：

```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py svg-tasks --project-path C:\work\ppt-jobs\q3-report --create-svg-stubs
```

## 每页任务文件包含什么
- 页面编号和标题
- 目标 SVG 路径
- ViewBox
- 页面目标
- 核心信息
- 支撑数据 / 案例
- 建议版式
- 视觉提示
- 演讲备注种子
- 原始逐页计划片段

## 为什么要加这一层
1. 让中段生产过程有标准输入
2. 让 SVG 设计 / 生成环节可并行或逐页检查
3. 让人工设计师或后续 agent 能明确知道每页该做什么
4. 让 `svg_output/` 至少先有结构化占位，不至于空目录硬推进后处理

## 建议顺序
1. `scaffold`
2. `bundle`
3. `slides`
4. `notes`
5. `svg-tasks`
6. 真正生成或替换 `svg_output/*.svg`
7. `validate`
8. `finalize`

## 注意
- 占位 SVG 只是脚手架，不是最终视觉稿
- 如果已经有人工绘制的页面，不要盲目覆盖，除非显式加 `--force`
- `svg_output_manifest.json` 可作为后续执行器的标准输入
