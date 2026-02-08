import os
import sys
import time
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_TXT = os.path.join(BASE_DIR, "output.txt")
OUTPUT_MP4 = os.path.join(BASE_DIR, "output.mp4")
QUOTA_EXIT = 2

_env_path = os.path.join(BASE_DIR, ".env")
if os.path.isfile(_env_path):
    try:
        with open(_env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception:
        pass

def is_limit_error(err):
    s = str(err)
    return ("429" in s or "402" in s or "RESOURCE_EXHAUSTED" in s or "PERMISSION_DENIED" in s
            or "credits" in s.lower() or "licenses" in s.lower()
            or "rate" in s.lower() or "quota" in s.lower() or "limit" in s.lower())

def try_veo(prompt):
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None, False
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    try:
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",
                duration_seconds="8",
            ),
        )
    except Exception as e:
        if is_limit_error(e):
            return None, True
        raise
    while not operation.done:
        print("Waiting for Veo...")
        time.sleep(10)
        try:
            operation = client.operations.get(operation)
        except Exception as e:
            if is_limit_error(e):
                return None, True
            raise
    if not operation.response or not getattr(operation.response, "generated_videos", None) or not operation.response.generated_videos:
        return None, False
    generated_video = operation.response.generated_videos[0]
    client.files.download(file=generated_video.video)
    generated_video.video.save(OUTPUT_MP4)
    return OUTPUT_MP4, False

def try_grok(prompt):
    if not os.environ.get("XAI_API_KEY", "").strip():
        return None, False
    try:
        from xai_sdk import Client
    except ImportError:
        return None, False
    client = Client()
    try:
        response = client.video.generate(
            prompt=prompt,
            model="grok-imagine-video",
            aspect_ratio="9:16",
            duration=8,
        )
    except Exception as e:
        if is_limit_error(e):
            return None, True
        raise
    if not response or not getattr(response, "url", None):
        return None, False
    req = urllib.request.Request(response.url, headers={"User-Agent": "yt-shorts-bot"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    with open(OUTPUT_MP4, "wb") as f:
        f.write(data)
    return OUTPUT_MP4, False

def main():
    if not os.path.isfile(OUTPUT_TXT):
        print("output.txt not found. Run generate.py first.", file=sys.stderr)
        sys.exit(1)
    with open(OUTPUT_TXT, "r", encoding="utf-8", errors="replace") as f:
        script = f.read().strip()
    if not script:
        print("output.txt is empty.", file=sys.stderr)
        sys.exit(1)
    prompt = f"A vertical short video for social media. Scene and narration: {script}. Cinematic, clear visuals, 9:16 aspect ratio."
    if not os.environ.get("GEMINI_API_KEY", "").strip() and not os.environ.get("XAI_API_KEY", "").strip():
        print("Set GEMINI_API_KEY or XAI_API_KEY in .env", file=sys.stderr)
        sys.exit(1)
    out, veo_limit = try_veo(prompt)
    if out:
        print(f"Saved to {OUTPUT_MP4} (Veo)")
        return
    if veo_limit:
        print("Veo limit exceeded, trying Grok...")
    out, grok_limit = try_grok(prompt)
    if out:
        print(f"Saved to {OUTPUT_MP4} (Grok)")
        return
    xai_key = os.environ.get("XAI_API_KEY", "").strip()
    if grok_limit or (veo_limit and not xai_key):
        print("Video limit(s) exceeded. Stopping.", file=sys.stderr)
        sys.exit(QUOTA_EXIT)
    print("Video generation failed.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
