# ppt-amir

将 `hugohe3/ppt-master` 转成可在 WorkBuddy 中直接使用的完整仓库封装，包含：

- `skills/ppt-master/`：WorkBuddy skill 定义、参考文档与执行脚本
- `agents/`：PPT 生成 agent 定义与使用说明
- `skills/ppt-master/scripts/run_pipeline.py`：统一入口，串行组织 scaffold / bundle / slides / notes / svg-tasks / svg-pages / finalize 等阶段

## 仓库结构

```text
ppt-amir/
  agents/
    ppt-master-agent.md
    references/
  skills/
    ppt-master/
      SKILL.md
      references/
      scripts/
```

## 主要能力

- 将 PDF、DOCX、URL、Markdown、纯文本等内容转为可编辑 PPTX 的工作流说明
- 通过 WorkBuddy agent 驱动演示文稿生产链路
- 支持项目脚手架、brief 打包、slides 规划、notes 汇总、SVG 任务单生成与 SVG 草稿页生成
- 支持主题系统与组件级视觉差异扩展

## 快速开始

### 1. 检查上游 `ppt-master` 仓库

```bash
python skills/ppt-master/scripts/run_pipeline.py --repo C:\path\to\ppt-master check
```

### 2. 创建项目脚手架

```bash
python skills/ppt-master/scripts/run_pipeline.py scaffold --project-root C:\work\ppt-jobs --project-name q3-report --format ppt169 --audience 投资人 --slide-count 10 --style 科技极简 --summary Q3业务汇报
```

### 3. 生成项目包

```bash
python skills/ppt-master/scripts/run_pipeline.py bundle --brief C:\work\briefs\q3.json --project-root C:\work\ppt-jobs --project-name q3-report
```

### 4. 继续执行中段与 SVG 草稿阶段

```bash
python skills/ppt-master/scripts/run_pipeline.py slides --project-path C:\work\ppt-jobs\q3-report
python skills/ppt-master/scripts/run_pipeline.py notes --project-path C:\work\ppt-jobs\q3-report
python skills/ppt-master/scripts/run_pipeline.py svg-tasks --project-path C:\work\ppt-jobs\q3-report --create-svg-stubs
python skills/ppt-master/scripts/run_pipeline.py svg-pages --project-path C:\work\ppt-jobs\q3-report --force
```

### 5. 最终导出

```bash
python skills/ppt-master/scripts/run_pipeline.py --repo C:\path\to\ppt-master finalize --project-path C:\work\ppt-jobs\q3-report
```

## 说明

这个仓库是 WorkBuddy 封装层，不替代上游 `ppt-master` 本身。真正导出 PPTX 时，仍需要你准备好上游仓库和依赖环境。
