import base64
import json
import os
import time
import urllib.error
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG_PATH = os.path.join(BASE_DIR, "assets", "bg.jpg")
OUTPUT_TXT = os.path.join(BASE_DIR, "output.txt")
TARGET_SIZE = (720, 1280)

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

def main():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("Set GEMINI_API_KEY in .env or environment.", file=__import__("sys").stderr)
        return False
    script = ""
    if os.path.isfile(OUTPUT_TXT):
        try:
            with open(OUTPUT_TXT, "r", encoding="utf-8", errors="replace") as f:
                script = f.read().strip()
        except Exception:
            pass
    if script:
        prompt = f"Generate a single image: vertical 9:16 background for a short video about this topic: \"{script[:200]}\". Style: cinematic, engaging, visually striking, mood that fits the topic. No text, no people. Portrait 9:16."
    else:
        prompt = "Generate a single image: vertical 9:16 background for a short video. Cinematic, engaging, visually striking. No text, no people."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    last_err = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
            break
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code == 429:
                if attempt == 0:
                    time.sleep(45)
                    continue
                print("Background image: API rate limit (429). Using existing or fallback.", file=__import__("sys").stderr)
            else:
                print(f"API request failed: {e}", file=__import__("sys").stderr)
            __import__("sys").exit(1)
        except Exception as e:
            last_err = e
            print(f"API request failed: {e}", file=__import__("sys").stderr)
            __import__("sys").exit(1)
    else:
        if last_err:
            print(f"API request failed: {last_err}", file=__import__("sys").stderr)
        __import__("sys").exit(1)
    for c in data.get("candidates", []):
        for part in c.get("content", {}).get("parts", []):
            if "inlineData" in part:
                raw = base64.b64decode(part["inlineData"]["data"])
                mime = part["inlineData"].get("mimeType", "image/png")
                break
        else:
            continue
        break
    else:
        print("No image in response.", file=__import__("sys").stderr)
        __import__("sys").exit(1)
    os.makedirs(os.path.dirname(BG_PATH), exist_ok=True)
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        img.save(BG_PATH, "JPEG", quality=90)
    except ImportError:
        with open(BG_PATH, "wb") as f:
            f.write(raw)
    print(f"Saved {BG_PATH}")
    return True

if __name__ == "__main__":
    sys = __import__("sys")
    if not main():
        sys.exit(1)
