# YouTube Shorts Bot

Generate and upload vertical Shorts: **only the idea** is from Gemini; then TTS → FFmpeg → output.mp4 → upload.

## Structure

```
├── scripts/
│   ├── generate.py               # Idea/script (Gemini)
│   ├── generate_bg.py            # Background image (Gemini, optional)
│   └── upload_local.py           # YouTube upload (OAuth Desktop)
├── run_local.py                  # Pipeline: Gemini idea → TTS → FFmpeg → output.mp4
├── run_loop.py                   # Loop: generate → upload → delete (Ctrl+C to stop)
├── requirements.txt
├── .env.example                  # Copy to .env, set GEMINI_API_KEY
└── README.md
```

## Setup

1. **Python 3.9+**, **FFmpeg** on PATH.
2. **Gemini:** Set `GEMINI_API_KEY` in `.env` (idea only). No Veo or Grok.
3. **TTS:** espeak-ng, or edge-tts / pyttsx3 on Windows.
4. **Upload:** `client_secret.json` (OAuth Desktop) in repo root; first run opens browser to sign in.
5. **Background:** A new background image is generated each run from the current idea (Gemini image API). If it fails, uses existing `assets/bg.jpg` or a solid color.

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env: GEMINI_API_KEY=your_key
```

## Usage

| Command | Description |
|---------|-------------|
| `python run_loop.py` | Loop: Gemini idea → TTS + FFmpeg → upload → delete. Stops when Gemini quota exceeded or Ctrl+C. `LOOP_DELAY=60` between runs. |
| `python scripts/generate_bg.py` | Generate `assets/bg.jpg` with Gemini once (or `GEN_BG=1` before run_loop to regenerate each time). |

## CI (GitHub Actions)

Workflow: **Actions → Shorts pipeline → Run workflow**.  
Add repo secret `GEMINI_API_KEY` so CI can generate idea. Video is TTS + FFmpeg. Produces `output.mp4` as an artifact; download and run `upload_local.py` locally.

## Notes

- Upload uses OAuth Desktop (free, no billing); must run on your machine.
- Shorts: vertical 720×1280, &lt;60s, title/description include #Shorts.
- **GPU:** FFmpeg uses GPU encoding when available (NVIDIA NVENC, AMD AMF, or Intel QSV). Set `USE_GPU=0` to force CPU (libx264). Idea and bg image run on Gemini’s servers; TTS is light; the main local load is video encoding.
