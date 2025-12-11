# 🕷️ AI Urban Legends Archive

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

Below are screenshots showcasing the primary features and visual style. Replace paths with your actual images if needed (these placeholders reference files under `preview/`).

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

Tip: If your images live elsewhere, update the relative paths accordingly, e.g.:
```markdown
![Your Image Title](static/uploads/your-image-name.png)
```

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

---
Last updated: 2025-12-11
