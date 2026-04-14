---
name: ppt-master
description: 将 PDF、DOCX、URL、Markdown 等内容转成可编辑 PPTX 的 WorkBuddy 技能封装，适合生成演示文稿、内容卡片和营销物料。
allowed-tools:
  - read_file
  - write_to_file
  - replace_in_file
  - search_file
  - search_content
  - execute_command
  - web_fetch
  - deliver_attachments
---

# PPT Master for WorkBuddy

这个技能把 `hugohe3/ppt-master` 项目的工作流整理成 WorkBuddy 可直接调用的技能说明。

## 何时使用
当用户出现以下需求时，使用本技能：
- “帮我做 PPT”
- “把这份文档转成演示文稿”
- “生成可编辑 PPTX”
- “把 PDF / DOCX / URL / Markdown 做成 PPT”
- “做社交媒体卡片 / 营销海报 / 小红书图文”

## 核心能力
- 将源内容转换为 Markdown 语义底稿
- 规划演示结构、页面节奏和视觉规范
- 选择适合的画布格式和输出比例
- 基于 `ppt-master` 仓库生成 SVG 页面与最终 PPTX
- 可选接入 AI 图片生成后端
- 输出可继续编辑的 PowerPoint 文件，而不是整页截图

## 工作方式
本技能是 **WorkBuddy 封装层**，不替代上游 `ppt-master` 仓库本身。

默认执行策略：
1. 先确认输入材料、输出格式、页数和风格
2. 再确认是否使用模板
3. 生成 `design_spec.md`
4. 必要时生成图片提示词和图片资源
5. 先把 `outline.md` 展开成 `slides.md`，再汇总为 `notes/total.md`
6. 把 `slides.md` 生成逐页 SVG 任务单和可选 stub
7. 根据任务单生成真实 SVG 草稿页
8. 基于草稿页继续精修或替换真实 SVG
9. 执行后处理并导出 PPTX




## 强约束
- 必须串行执行，不要跨阶段乱跳
- 模板选择和设计确认属于阻塞点，没确认就不要继续
- SVG 页面应逐页生成，不要一口气批量瞎拼
- 后处理和导出要分步骤执行，不要偷懒合并成一个大命令
- 图片策略如果依赖 AI 生图，必须先确认后端和密钥配置
- 最终交付物至少应包含：设计规范、SVG 输出、备注文件、PPTX 导出物

## 推荐对话流程
### 第一步：收集输入
至少确认这些信息：
1. 源材料类型：PDF / DOCX / URL / Markdown / 纯文本
2. 输出格式：PPT 16:9、PPT 4:3、小红书、方图、竖版海报等
3. 页数范围：例如 8-10 页
4. 受众：老板、客户、投资人、内部团队、课堂听众
5. 风格：商务、科技、极简、学术、营销
6. 是否需要图片：真实图片、图标、AI 生图、纯图形化表达
7. 是否使用模板：用现有模板 / 自由设计

### 第二步：建立项目上下文
建议在项目工作目录里组织如下结构：

```text
ppt-project/
  sources/
  images/
  notes/
  svg_output/
  svg_final/
  exports/
  design_spec.md
```

### 第三步：生成设计规范
优先使用内置模板 `scripts/design_spec_template.md` 作为起点，或先用 `scripts/brief_to_bundle.py` / `run_pipeline.py bundle` 把结构化 brief 写成项目包，再补齐项目级 `design_spec.md`。


生成 `design_spec.md` 时，至少包含：
- Project Summary
- Audience
- Canvas Format
- Slide Count
- Visual Style
- Color Palette
- Typography
- Icon Strategy
- Image Strategy
- Content Outline
- Page-by-page Plan

注意：即使正文是中文，也建议这些 section 标题保留英文，方便和上游仓库约定保持一致。


### 第四步：图片生成（可选）
当图片策略是 “AI generation” 时：
- 先生成 `images/image_prompts.md`
- 再调用上游脚本完成图片生成
- 图片文件统一落在 `images/`

### 第五步：执行产出
推荐顺序：
1. 准备或导入源内容
2. 生成设计规范
3. 逐页生成 SVG 到 `svg_output/`
4. 生成备注文件 `notes/total.md`
5. 执行 SVG 后处理到 `svg_final/`
6. 从 `svg_final/` 导出 PPTX 到 `exports/`

## 环境要求
- Python 3.10+
- 可选：Node.js 18+
- 可选：Pandoc
- 可选：Cairo（如果使用 `cairosvg`）

详见：
- `references/setup.md`
- `references/canvas-formats.md`
- `references/execution-wiring.md`
- `references/project-scaffold.md`
- `references/brief-bundle.md`
- `references/mid-pipeline.md`
- `references/svg-task-stage.md`
- `references/svg-draft-stage.md`







## 常见命令
以下命令来自上游项目，供 WorkBuddy 在需要时调用：

```bash
git clone https://github.com/hugohe3/ppt-master.git
cd ppt-master
pip install -r requirements.txt
```

准备并检查上游仓库：
```bash
git clone https://github.com/hugohe3/ppt-master.git
cd ppt-master
pip install -r requirements.txt
```

生成项目脚手架与 `design_spec.md` 模板：
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py scaffold --project-root C:\work\ppt-jobs --project-name q3-report --format ppt169 --audience 投资人 --slide-count 10 --style 科技极简 --summary Q3 业务汇报
```

把结构化 brief 生成项目包：
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\brief_to_bundle.py --brief C:\work\briefs\q3.json --project-path C:\work\ppt-jobs\q3-report
```

或通过统一入口调用：
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py bundle --brief C:\work\briefs\q3.json --project-root C:\work\ppt-jobs --project-name q3-report
```

生成逐页 slide plan：
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py slides --project-path C:\work\ppt-jobs\q3-report
```

汇总备注初稿：
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py notes --project-path C:\work\ppt-jobs\q3-report
```

把 slide plan 生成逐页 SVG 任务单和占位 stub：
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py svg-tasks --project-path C:\work\ppt-jobs\q3-report --create-svg-stubs
```

根据任务单生成真实 SVG 草稿页（内置版式识别、页级文案改写、takeaway 提炼、subtitle 生成、supporting bullets 重组、按版式定制内容分配、结构化版式字段、文本压缩、轻量组件、重点版式视觉精修，以及 default/dark/tech-blue/business-dark/brand-light/consulting 主题系统；主题会下沉到 chip/callout/cover/comparison/hero/kpi-grid/section-divider/data-highlight 等组件层）：








```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py svg-pages --project-path C:\work\ppt-jobs\q3-report --force
```





## 图片生成配置



`.env` 示例：

```env
IMAGE_BACKEND=gemini
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.1-flash-image-preview
```

支持的后端包括：
- gemini
- openai
- qwen
- zhipu
- volcengine
- stability
- bfl
- ideogram
- siliconflow
- fal
- replicate

## 交付标准
完成一次任务时，应该尽量给出：
- `design_spec.md`
- `images/image_prompts.md`（如有 AI 生图）
- `notes/total.md`
- `svg_output/` 和 / 或 `svg_final/`
- `exports/*.pptx`

## 不该做的事
- 不要把它当成“随便生成几页 PPT”的玩具脚本
- 不要跳过设计规范直接导出
- 不要在未确认模板/风格/画幅时擅自推进
- 不要直接从 `svg_output/` 导出最终 PPTX（应优先走后处理产物）
- 不要假设用户已经配好图片 API 密钥

## 与 WorkBuddy 的映射建议
如果用户只是想“先规划”，那就停在：
- 收集需求
- 输出 `design_spec.md`
- 给出下一步执行建议

如果用户希望“直接生成”，则继续：
- 检查依赖
- 调上游仓库命令
- 生成中间文件
- 导出最终 PPTX
- 交付生成物

## 参考资料
- `references/canvas-formats.md`
- `references/setup.md`

## 一句话总结
这是一个把 `ppt-master` 严格流水线包装进 WorkBuddy 的技能：先确认，再设计，再生成，最后导出。别跳步，别乱来，PPT 才不会长得像事故现场。
