# 中段生成链说明

## 这份文档是干什么的
前面的 `scaffold` 和 `bundle` 解决的是“把项目搭起来、把 brief 写成规划文件”。
后面的 `finalize` 解决的是“把已有 SVG 和备注做后处理并导出 PPTX”。

真正最容易断层的，是中间这段：
- 从 `outline.md` 扩成逐页计划
- 从逐页计划汇总出 `notes/total.md`

这份文档说的就是这条中段链路。

## 新增的两个脚本
### 1. `outline_to_slides.py`
把 `notes/outline.md` 扩成 `notes/slides.md`。

输出内容包括：
- Slide 编号
- 页面标题
- 页面目标
- 核心信息
- 支撑数据/案例
- 建议版式
- 视觉提示占位
- 备注占位

它不是 SVG 生成器。
它的作用是先把“结构化页面计划”定下来，供 agent 或后续执行器继续加工。

### 2. `bundle_to_notes.py`
把这些规划文件汇总成 `notes/total.md`：
- `design_spec.md`
- `sources/brief.md`
- `notes/outline.md`
- `notes/slides.md`

输出是逐页备注初稿，不是最终讲稿，但足够作为后续 PPT 生成链的稳定输入。

## 推荐执行顺序
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py scaffold --project-root C:\work\ppt-jobs --project-name q3-report --format ppt169
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py bundle --brief C:\work\briefs\q3.json --project-root C:\work\ppt-jobs --project-name q3-report
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py slides --project-path C:\work\ppt-jobs\q3-report
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py notes --project-path C:\work\ppt-jobs\q3-report
```

## 重要边界
- `slides` 不是最终页面，只是逐页计划
- `notes` 不是最终演讲稿，只是备注底稿
- 如果 `design_spec.md`、`brief.md`、`outline.md` 还很粗糙，这两个脚本只会把粗糙放大，不会神奇变聪明
- 真正的视觉产出和 SVG 生成，仍需要 agent 或上游流程继续完成

## 推荐做法
- 先用这两个脚本把中段产物固定下来
- 再由 agent 人工补强：视觉节奏、页面压缩、图表建议、重点字句
- 确认 `svg_output/` 和 `notes/total.md` 都就绪后，再进入 `finalize`
