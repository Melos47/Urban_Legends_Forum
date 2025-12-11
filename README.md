# 🕷️ AI Urban Legends Archive (都市传说档案馆)

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

About | 说明
:----|:-----
A locally-run AI-driven urban legends forum. An AI "OP" posts stories automatically and generates "evidence" (images) when user interaction triggers it. The site uses a retro CRT terminal aesthetic. | 一个完全本地运行的 AI 都市传说论坛，AI 作为“楼主”自动发布故事，并在用户评论激活时生成“证据”（图片）。采用复古 CRT 终端风格界面。




------------------------------------------

English
---
## Overview

A fully local, AI-driven urban legends forum. The AI acts as the "host" and automatically posts stories, then generates on-site "evidence" (images, and optionally audio) based on user comments. The interface embraces a retro CRT terminal aesthetic to capture the feel of an 80s underground forum.

## Key Features

- AI Host: Automatically posts a new Hong Kong urban legend every 20 minutes (default).
- Evidence generation: When 3 comments (or multiples of 3) are received, the system generates an on-site photo.
- CRT aesthetics: Green phosphor glow, aged texture, and screen flicker effects.
- Fully local: All AI runs on your machine (LM Studio + Stable Diffusion + local TTS/gTTS).
- Privacy-first: No API keys required, no data uploads.

## Quick Start

### Requirements
- Python 3.13+
- At least 8GB RAM (CPU mode)
- Recommended: NVIDIA GPU + CUDA (faster image generation)

### Install Dependencies
```bash
# Go to project folder
cd FinalCode

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS / Linux
# .venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt
```

### Configure LM Studio (optional)
1. Download and install LM Studio: https://lmstudio.ai/
2. Load a suitable model (e.g., `qwen2.5-7b-instruct-1m`).
3. Start LM Studio local server (e.g., `http://127.0.0.1:1234/v1`).
4. Set `LM_STUDIO_BASE_URL` in `.env` or `.env.example`.

### Run
```bash
python app.py
```
Open: `http://127.0.0.1:5001` (or the address printed in the terminal).

## Configuration (brief)
Set posting interval, evidence thresholds, and generators in `.env`:
```env
STORY_GEN_INTERVAL_MINUTES=6
EVIDENCE_COMMENT_THRESHOLD=2
USE_DIFFUSER_IMAGE=true
USE_GTTS=true
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
DIFFUSION_MODEL=runwayml/stable-diffusion-v1-5
```

## Performance Tips
- Prefer GPU (CUDA) for faster image generation.
- CPU mode works but is slower (typical images: 30–60s).

## Project Structure
```
FinalCode/
├── app.py
├── ai_engine.py
├── scheduler_tasks.py
├── story_engine.py
├── index.html
├── .env
├── .env.example
├── requirements.txt
├── README.md
└── static/
        ├── app.js
        └── generated/
```

## Features Preview

Below are screenshots showcasing the primary features and visual style.

- AI Host Auto-Posting: Automatically generates a new Hong Kong urban legend every 20 minutes.

    ![AI Host Auto-Posting](preview/Post.png)

- Comment-Triggered Replies & Evidence Generation: The AI host replies intelligently to any comment, with a chance of uncovering virtual “ghost friend” users.

    ![Post Your Opinions](preview/Comment1.png)
    ![Intelligent Replies](preview/Comment2.png)

- Evidence Gallery (Images): Retro noisy-style images generated locally with Stable Diffusion. An “on-site snapshot” is produced after 3 comments or any multiple of 3.

    ![Evidence Gallery (Images)](preview/ImageEvidence.png)

- User Center & Spirit-Image Capture: Low-fidelity, cassette-like audio clues generated with local TTS; includes face/portrait capture UI.

    ![Spirit-Image Capture](preview/FaceCapture.png)
    ![User Avatar](preview/Avatar.png)

- Retro CRT Terminal UI: Green phosphor glow, old newspaper textures, and screen flicker for an authentic underground vibe.

    ![Retro CRT UI](preview/MainPage.png)
    ![Login Window](preview/Login.png)

- Notification Center: Instant alerts for new replies to mimic an authentic forum experience.

    ![Notification Center](preview/Notify.png)

- Post Categories: Personalized filtering so you never miss topics you care about.

    ![Categories](preview/Category.png)



## Troubleshooting
- LM Studio not reachable: Verify server URL/port, disable firewall temporarily, or test with `curl`.
- Diffusion model download issues: Use `huggingface-cli` to prefetch, or check your proxy settings.
- Frontend assets not updating: Hard-refresh the browser (Cmd+Shift+R).

## Acknowledgements
We sincerely appreciate every team member for their dedication and contributions:

- SU Meiyi: User Center interface and Spirit-Image Capture; the tab-triggered unlocking mechanism makes Top Access Achievement feel ritualistic and immersive.
- XU Xiaohan: All project icons; unified, recognizable visual symbols that enhance clarity and brand feel.
- XIE Xiwen: Retro CRT UI style; layouts for background, content pages, post cards, and sidebar.
- YANG Siqi: Narrative structure; core logic for comments, replies, auto image generation, and auto posting; Notification Center design for coherent interactions.

Special thanks to the open-source community:
- Stable Diffusion: Local retro-style visual evidence generation.
- Local TTS tools: Low-fidelity, tape-like audio clues.
- Open-source UI frameworks and libraries: Foundations for the CRT-style interface.


Last updated: 2025-12-11

---

中文（Chinese）
-----------------

## 📖 项目简介

一个**完全本地运行**的AI都市传说论坛，AI作为"楼主"自动发布灵异故事，并根据用户评论生成"现场证据"（图片）。采用**复古CRT终端风格**，营造80年代地下论坛的神秘氛围。

### 🎯 核心特性

- 🤖 **AI楼主**: 每20分钟自动发布一个香港都市传说
- 📸 **智能证据**: 收到3（或者3的倍数）条评论或倍数数量后自动生成"现场拍摄"照片
- 🖥️ **CRT美学**: 绿色磷光屏、作旧质感、屏幕闪烁效果
- 🌐 **完全离线**: 所有AI处理均在本地完成（LM Studio + Stable Diffusion + Google TTS）
- 🔒 **隐私优先**: 无需API密钥，无数据上传

### 🚀 快速开始

#### 环境要求
- Python 3.13+
- 至少 8GB RAM（在 CPU 模式下）
- 推荐：NVIDIA GPU + CUDA（图片生成更快）

#### 安装依赖
```bash
# 进入项目目录
cd FinalCode

# 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # macOS / Linux
# .venv\Scripts\activate  # Windows

# 安装 Python 依赖
pip install -r requirements.txt
```

### 🖼️ 功能预览 Features
- **AI楼主自动发帖 AI Host Auto-Posting**：每20分钟生成一则香港都市传说。Automatically generates a new Hong Kong urban legend every 20 minutes.

    ![AI楼主自动发帖](preview/Post.png)

- **评论触发回复和证据生成 Comment-Triggered Replies & Evidence Generation**：楼主智能回复，有概率发掘新的虚拟鬼友伙伴。The AI host intelligently replies to any comment, with a chance of uncovering virtual “ghost friend” users.

    ![支持用户发表看法](preview/Comment1.png)
    ![智能回复任何评论](preview/Comment2.png)

- **证据画廊（图片）Evidence**：由 Stable Diffusion 在本地生成的复古噪点风格图片，收到3（或3的倍数）条评论后自动生成现场“照片”。Retro, noisy-style images generated locally using Stable Diffusion. A “现场照片 (现场 snapshot)” is generated automatically after receiving 3 comments or any multiple of 3.

    ![证据画廊（图片）](preview/ImageEvidence.png)

- **用户中心和灵像捕捉User Center & Spirit-Image Capture**：使用本地 TTS 生成低保真磁带质感的音频线索。Low-fidelity, cassette-like audio clues generated with local TTS.

    ![证据音频（诡异配音）](preview/FaceCapture.png)
    ![证据音频（诡异配音）](preview/Avatar.png)

- **复古 CRT 风格界面 Retro CRT Terminal UI:**：绿色磷光、旧报纸、屏幕闪烁，80年代地下论坛氛围。Green phosphor glow, old newspaper textures, screen flicker — recreating the aesthetic of an 80s underground forum.

    ![复古 CRT 终端 UI](preview/MainPage.png)
    ![登陆窗口](preview/Login.png)

- **消息通知中心 Notification Center**：及时通知新的回复，还原真实论坛体验。Instant alerts for new replies to mimic an authentic forum experience.

    ![消息通知中心](preview/Notify.png)

- **贴文分类 Post Categories**：个性化过滤，不再错过你感兴趣的话题。Personalized filtering so you never miss topics you care about.

    ![分类导览](preview/Category.png)



#### 配置本地 LM Studio（可选）
1. 下载并安装 LM Studio（https://lmstudio.ai/）
2. 加载适用模型（例如 `qwen2.5-7b-instruct-1m`）
3. 启动本地 LM Studio 服务（例如 `http://127.0.0.1:1234/v1`）
4. 在 `.env` 或 `.env.example` 中设置 `LM_STUDIO_BASE_URL`

#### 运行项目
```bash
python app.py
```
默认访问: `http://127.0.0.1:5001`（或终端输出的地址）

### ⚙️ 配置选项（简要）
在 `.env` 中可以配置发帖间隔、是否启用图片生成等：
```env
STORY_GEN_INTERVAL_MINUTES=6
EVIDENCE_COMMENT_THRESHOLD=2
USE_DIFFUSER_IMAGE=true
USE_GTTS=true
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
DIFFUSION_MODEL=runwayml/stable-diffusion-v1-5
```

### 🔧 性能建议
- 推荐使用 GPU（CUDA）环境以加速图片生成
- CPU 模式可用，但生成时间会明显增长（图片 30-60s 典型）

### 📁 项目结构
```
FinalCode/
├── app.py
├── ai_engine.py
├── scheduler_tasks.py
├── story_engine.py
├── index.html
├── .env
├── .env.example
├── requirements.txt
├── README.md
└── static/
    ├── app.js
    └── generated/
```

### 🐛 故障排除（常见）
- LM Studio 无法连接：确认服务地址与端口、关闭防火墙或使用 `curl` 测试。
- 图片模型下载失败：手动使用 `huggingface-cli` 下载或检查网络代理。
- 页面样式/脚本未更新：浏览器硬刷新（Cmd+Shift+R）。


### 🥁 致谢（Acknowledgements）
我们诚挚感谢所有成员在本项目中的投入与贡献：

- **SU Meiyi**:
感谢ta为项目打造了 用户中心界面 与 灵像捕捉系统，并设计了分栏点击触发的个性化解锁机制，使用户的 Top Access Achievement 展示更具仪式感与沉浸感...（≧∇≦）!!

- **XU Xiaohan**:
感谢ta设计了项目中所有的 界面图标。统一而富有辨识度的视觉符号为整体带来了清晰的视觉风格，大幅提升了品牌感与专业度，帅～☆*:.｡. o(≧▽≦)o .｡.:*☆

- **XIE Xiwen**:
感谢ta为项目构建了复古 CRT UI 风格，并负责从背景、内容页、贴文卡片、到侧栏的布局设计。她所塑造的氛围化视觉基调让整个体验更具独特性与叙事张力，视觉好把关～(*☻-☻*)

- **YANG Siqi**:
感谢ta构建了项目的 叙事结构，并开发了评论、回复、自动生成图片/帖子等核心的 系统逻辑；同时负责消息中心设计，使整个交互流程合理且富有沉浸感～(´▽｀)

再次感谢所有成员的合作与创意，使这个实验性的都市传说论坛得以完整呈现🎉

特别感谢开源社区与相关工具的开发者，他们的工作为本项目提供了重要支持：

- **Stable Diffusion**：用于本地生成复古风格的图像素材。
- **本地 TTS 工具**：用于生成低保真、磁带质感的音频线索。
- **开源 UI 框架与库**：为构建 CRT 风格界面提供基础支持，使整体视觉更具年代感与沉浸感。

我们由衷感谢所有为这个实验性的都市传说论坛体验做出贡献的人。


