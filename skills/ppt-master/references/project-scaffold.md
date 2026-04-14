# 项目脚手架说明

## 推荐目录结构

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

## 每个目录干什么
- `sources/`：原始输入材料，PDF / DOCX / Markdown / 文本等
- `images/`：图片资源与 `image_prompts.md`
- `notes/`：备注、讲稿、`total.md`
- `svg_output/`：初始 SVG 页面输出
- `svg_final/`：后处理后的 SVG 页面
- `exports/`：最终 PPTX 等导出物
- `design_spec.md`：整个项目的设计总控文件

## 推荐使用顺序
1. 初始化项目目录
2. 复制 design_spec 模板到项目根目录
3. 导入源文件到 `sources/`
4. 完成 `design_spec.md`
5. 生成 `svg_output/` 和 `notes/total.md`
6. 执行 finalize 导出链路

## 说明
脚手架只负责把工作台摆整齐，不会替你决定内容、风格和版式。那些仍然应该由 agent 来判断。