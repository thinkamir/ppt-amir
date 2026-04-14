# SVG Draft Stage

这一阶段把 `tasks/slide-XX.md` 转成真实可查看的 SVG 草稿页，而不是只有 stub 占位。

## 输入
- `tasks/slide-XX.md`
- 可选：`design_spec.md`

## 输出
- `svg_output/slide-XX.svg`
- `svg_page_drafts.json`

## 支持的稳定版式
- `title-bullets`
- `two-column`
- `hero`
- `data-highlight`
- `timeline`
- `comparison`
- `cover`
- `section-divider`
- `quote`
- `kpi-grid`
- `process`
- `matrix`
- `table-lite`

脚本会根据任务单中的 `Layout Guidance`、`Visual Guidance`、标题、目标、核心信息与支撑信息联合推断版式；推断不到时默认使用 `title-bullets`。同时会在渲染前做页级文案改写：压缩标题、收敛 bullet、去掉冗余表达，并自动提炼一个简短 takeaway，避免 bullet 和说明文字在草稿页中爆行。新版本还会额外生成 subtitle，并优先重组出 2-5 条更像 PPT 支撑论点的 supporting bullets，让页面更接近“结论 + 证据”的表达方式。对于 `comparison`、`timeline`、`process`、`kpi-grid`、`matrix`、`table-lite` 等版式，系统还会先生成结构化版式字段，再交给对应渲染器消费，例如 `left_items/right_items`、`stages`、`steps`、`kpis`、`quadrants`、`rows`，避免不同版式重新把通用 bullets 硬拆回去。当前还额外对 `comparison`、`kpi-grid`、`matrix`、`process`、`timeline`、`table-lite` 做了视觉精修：对比页带左右标题条与差异标签、KPI 页强化数字卡层级、矩阵页加入四象限底色与更明确的标签位置；流程页增加步骤状态条、节点编号和箭头、时间线页加入进度线与交错里程碑标签、轻表格页补了斑马纹和结果列强调。









## 主题系统
当前支持这些主题：
- `default`
- `dark`
- `tech-blue`
- `business-dark`
- `brand-light`
- `consulting`

可以显式传入 `--theme`，也可以让脚本根据 `Visual Guidance` / 标题里的风格关键词自动推断主题，例如科技蓝、深色商务、轻品牌、顾问报告风。主题系统现在不只是换配色：`chip`、`callout`、`cover`、`comparison`、`hero`、`kpi-grid`、`section-divider`、`data-highlight` 会按主题切换组件语气，比如深色商务会强化描边与压暗右列、品牌浅色会用更柔和圆角和粉色标签、顾问风会偏证据与建议标签，科技蓝会强化 hero 信息卡、KPI 标签和数据指标卡的系统感，章节页也会随主题切换底板和分隔线语气。




## 命令示例
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\svg_tasks_to_pages.py --project-path C:\work\ppt-jobs\q3-report --theme tech-blue --force
```

通过统一入口调用：

```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py svg-pages --project-path C:\work\ppt-jobs\q3-report --theme consulting --force
```


## 说明
- 这一步生成的是“结构化页面草稿”，不是最终精修视觉稿。
- 它的价值是让 `svg_output/` 不再空着，并且让后续 refine / finalize 有稳定基础。
- 如果已有更高质量的 SVG 页面，可以直接覆盖这些草稿。
