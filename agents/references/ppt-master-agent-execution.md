# ppt-master-agent 执行版说明

## 这份文件解决什么问题
前面的 agent 定义已经说明了“怎么规划、怎么判断、怎么阻塞”。
这份文档补的是：**当用户要求直接执行时，agent 到底该怎么稳妥落地。**

## 推荐执行路线
### 路线 A：只做规划
适用场景：
- 素材还不完整
- 还没定风格
- 用户只是想先看提纲或页面规划

此时不要调用包装脚本，只输出：
- 需求摘要
- `design_spec.md`
- 页面规划
- 下一步建议

### 路线 B：执行生产流程
适用场景：
- 输入材料已齐
- 画幅和风格已确认
- 用户明确希望导出 PPTX
- 环境依赖基本可用

推荐顺序：
1. `check`
2. `scaffold`
3. 如有结构化 brief，则执行 `bundle`
4. Agent 补齐和确认 `design_spec.md`
5. 执行 `slides` 生成 `notes/slides.md`
6. 执行 `notes` 生成 `notes/total.md`
7. Agent / 上游流程基于逐页计划完成 `svg_output/`
8. `init`
9. `import`
10. `validate`
11. `finalize`



## 关键阻塞点
这些地方不该硬冲：

### 1. 模板没定
要么确认使用模板，要么确认自由设计。

### 2. 八项设计确认没完成
至少确认：
- 画布格式
- 页数范围
- 受众
- 风格
- 配色
- 图标策略
- 字体
- 图片策略

### 3. Executor 还没产出完整中间结果
在没有下面两项时，禁止导出：
- `svg_output/`
- `notes/total.md`

## 推荐调用示例
### 先检查
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py --repo C:\path\to\ppt-master check
```

### 创建项目脚手架
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py scaffold --project-root C:\work\ppt-jobs --project-name q3-report --format ppt169 --audience 投资人 --slide-count 10 --style 科技极简 --summary Q3 业务汇报
```

### 根据 brief 生成项目包
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py bundle --brief C:\work\briefs\q3.json --project-root C:\work\ppt-jobs --project-name q3-report
```

### 生成逐页计划
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py slides --project-path C:\work\ppt-jobs\q3-report
```

### 汇总备注初稿
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py notes --project-path C:\work\ppt-jobs\q3-report
```

### 初始化项目

```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py --repo C:\path\to\ppt-master init --project-root C:\work\ppt-jobs --project-name q3-report --format ppt169
```


### 导入材料
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py --repo C:\path\to\ppt-master import --project-path C:\work\ppt-jobs\q3-report C:\input\report.pdf --move
```

### 后处理与导出
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\run_pipeline.py --repo C:\path\to\ppt-master finalize --project-path C:\work\ppt-jobs\q3-report
```

## 风险提示
### 1. `import --move`
这是上游推荐方式，但它会移动源文件，不是复制。执行前要确认用户接受。

### 2. `scaffold` 不是设计完成
它只负责搭好工作台并预生成 `design_spec.md` 骨架，不会替你完成内容策略与逐页规划。

### 3. `finalize` 不是魔法
它不会帮你自动补 `design_spec.md`，也不会帮你凭空生成 SVG。它只负责稳定执行后处理和导出链路。

### 4. `run` 适合熟练场景
组合命令方便，但更容易把错误带着一路跑下去。第一次执行建议拆开。

## 推荐策略
- 第一次跑：优先 `--dry-run`
- 真执行前：确认 repo 路径、项目路径、源文件路径
- 真导出前：先检查 `design_spec.md`、`svg_output/` 和 `notes/total.md`
- 交付时：把 `design_spec.md`、`notes/total.md`、`exports/*.pptx` 一起给用户
