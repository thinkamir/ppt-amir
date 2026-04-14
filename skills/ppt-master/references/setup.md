# Setup Guide

这是把 `hugohe3/ppt-master` 用在 WorkBuddy 中时的环境配置说明。

## 基础依赖
必需：
- Python 3.10+

可选：
- Node.js 18+（某些网页或扩展转换流程可能用到）
- Pandoc（DOCX / EPUB / HTML / LaTeX / RST 转 Markdown）
- Cairo（如果使用 `cairosvg` 做 Office 兼容 SVG 转换）

## Python 依赖
安装全部依赖：

```bash
pip install -r requirements.txt
```

主要依赖按功能划分如下：

### SVG 转 PPTX
- `python-pptx>=0.6.21`
- 推荐：`cairosvg`
- 备选：`svglib>=1.5.0`
- 备选：`reportlab>=4.0.0`

### PDF 转 Markdown
- `PyMuPDF>=1.23.0`

### 图片处理
- `Pillow>=9.0.0`
- `numpy>=1.20.0`

### 网页抓取 / 转 Markdown
- `requests>=2.31.0`
- `beautifulsoup4>=4.12.0`

### AI 图片生成
- Gemini: `google-genai>=1.0.0`
- OpenAI 兼容接口: `openai>=1.0.0`

## 图片生成环境变量
建议从 `.env.example` 复制一份 `.env`，再按所选后端填写。

最小示例：

```env
IMAGE_BACKEND=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.1-flash-image-preview
```

说明：
- 配置优先级是“当前进程环境变量 > .env 文件”
- 旧变量 `IMAGE_API_KEY`、`IMAGE_MODEL`、`IMAGE_BASE_URL` 已不推荐使用
- 应使用各家自己的命名方式，比如 `GEMINI_API_KEY`、`OPENAI_API_KEY`

## 常见初始化流程

```bash
git clone https://github.com/hugohe3/ppt-master.git
cd ppt-master
pip install -r requirements.txt
```

更新本地仓库：

```bash
python skills/ppt-master/scripts/update_repo.py
```

查看支持的图片后端：

```bash
python skills/ppt-master/scripts/image_gen.py --list-backends
```

## WorkBuddy 接入建议
- 如果只是做方案和页面规划，可以先不安装全部依赖
- 如果要真正导出 PPTX，至少确认 Python 依赖可用
- 如果要启用 AI 生图，必须先确认后端密钥已配置
- 如果在 Windows 上运行，优先用单独的 Python 虚拟环境，别把系统环境搞成实验田

## 排障建议
- 依赖缺失：先检查 Python 版本和虚拟环境
- DOCX/EPUB 无法转 Markdown：多半是 `pandoc` 没装
- SVG 转 PPTX 兼容性差：优先安装 `cairosvg`
- 图片生成失败：先检查 `IMAGE_BACKEND` 和对应 API Key
