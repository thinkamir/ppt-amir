# ppt-master-agent 使用说明

## 定位
`ppt-master-agent` 是面向演示文稿生产流程的专用代理，不是通用排版助手。

它适合处理两类任务：
1. **先规划**：梳理内容、确认风格、生成 `design_spec.md`
2. **直接执行**：在规划完成后，继续驱动 `ppt-master` 工作流生成 SVG 与最终 PPTX

## 推荐触发词
- 帮我做 PPT
- 把这份文档转成演示文稿
- 生成可编辑 PPTX
- 把这篇文章做成小红书图文
- 帮我做路演 deck / 培训讲义 / 商务汇报

## 推荐输入
最好提前给代理这些信息：
- 源文件或链接
- 目标页数
- 输出比例
- 目标受众
- 风格关键词
- 是否需要配图
- 是否需要最终导出 PPTX

## 推荐配合资料
- `C:\Users\amir\.workbuddy\skills\ppt-master\SKILL.md`
- `C:\Users\amir\.workbuddy\skills\ppt-master\references\canvas-formats.md`
- `C:\Users\amir\.workbuddy\skills\ppt-master\references\setup.md`
- `C:\Users\amir\.workbuddy\skills\ppt-master\references\execution-wiring.md`
- `C:\Users\amir\.workbuddy\skills\ppt-master\references\brief-bundle.md`
- `C:\Users\amir\.workbuddy\skills\ppt-master\references\mid-pipeline.md`
- `C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py`
- `C:\Users\amir\.workbuddy\skills\ppt-master\scripts\brief_to_bundle.py`
- `C:\Users\amir\.workbuddy\skills\ppt-master\scripts\outline_to_slides.py`
- `C:\Users\amir\.workbuddy\skills\ppt-master\scripts\bundle_to_notes.py`



## 建议使用方式

### 方案 A：先规划
先让代理只输出：
- 需求摘要
- 演示结构
- `design_spec.md`
- 页面级规划

适合内容还没定稿、风格还需要讨论的时候。

### 方案 B：直接执行
在输入充分、依赖已装好的前提下，让代理继续完成：
- 目录组织
- 如果已拿到结构化 brief，先生成项目包（`design_spec.md`、`sources/brief.md`、`notes/outline.md`）
- 生成 `notes/slides.md` 逐页计划
- 汇总 `notes/total.md` 备注初稿
- 中间 SVG 输出
- 后处理
- PPTX 导出



## 注意事项
- 该代理会把“模板确认”和“设计确认”视为阻塞点
- 没有确认关键信息时，它不应该直接开做
- 如果环境依赖不完整，它应明确报出卡点，而不是假装完成
- 如果目标是社媒卡片，代理会优先按平台比例设计，而不是默认套 PPT 比例
