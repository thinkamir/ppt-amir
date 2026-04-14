# Brief 到项目包

## 这是什么
这个能力用来把一份结构化 brief 直接落成 ppt-master 项目里的几份核心规划文件，减少 agent 每次从零手写骨架。

它会优先生成：
- `design_spec.md`
- `sources/brief.md`
- `notes/outline.md`
- `images/image_prompts.md`（当图片策略是 AI generation 或提供了 prompts）

## 输入格式
推荐使用 JSON 文件，字段可按需增减。最小示例：

```json
{
  "project_name": "q3-report",
  "summary": "Q3 业务汇报",
  "input_type": "PDF + 补充说明",
  "audience": "投资人",
  "format": "ppt169",
  "slide_count": "10",
  "style": "科技极简",
  "image_strategy": "AI generation",
  "source_summary": "基于季度经营数据和产品进展做一份路演式汇报",
  "content_outline": ["封面", "业务进展", "关键数据", "产品亮点", "下一步计划"],
  "must_include": ["营收增长", "新产品上线", "海外扩展"],
  "must_avoid": ["内部敏感数字泄露", "过度技术细节"],
  "image_prompts": [
    "科技感深色背景，蓝紫渐变，抽象数据流",
    "现代商务人物演示场景，简洁构图"
  ]
}
```

## 调用方式
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\brief_to_bundle.py --brief C:\work\briefs\q3.json --project-path C:\work\ppt-jobs\q3-report
```

覆盖已有文件：
```bash
python C:\Users\amir\.workbuddy\skills\ppt-master\scripts\brief_to_bundle.py --brief C:\work\briefs\q3.json --project-path C:\work\ppt-jobs\q3-report --force
```

## 推荐使用顺序
1. `scaffold` 建项目骨架
2. `brief_to_bundle.py` 生成规划包
3. agent 审阅并补齐 `design_spec.md`
4. 导入真实源文件
5. 继续后续执行链路

## 边界
- 它不会替你理解 PDF 正文，只负责把结构化 brief 稳定写进项目文件
- 它不是最终页面生成器，不会产出 `svg_output/`
- 如果 brief 太空，输出也只会是一个带占位符的清晰骨架，不会凭空编故事
