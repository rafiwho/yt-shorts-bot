import os
import re
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "output.txt")
MAX_RETRIES = 3

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

def generate_gemini(api_key):
    from google import genai
    client = genai.Client(api_key=api_key)
    prompt = """Generate one short sentence for a YouTube Shorts script. Catchy hook or surprising fact. Max 80 characters. No quotes. End with "Follow for more." Output only the script."""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
            if response and getattr(response, "text", None):
                return response.text.strip()
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                m = re.search(r"retry in (\d+(?:\.\d+)?)s", err, re.I)
                wait = int(float(m.group(1))) + 1 if m else 60
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait)
                else:
                    return None
            else:
                return None
    return None

QUOTA_EXCEEDED_EXIT = 2

def main():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("GEMINI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)
    script = generate_gemini(api_key)
    if not script:
        print("Gemini quota exceeded.", file=sys.stderr)
        sys.exit(QUOTA_EXCEEDED_EXIT)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(script)
    print(script)

if __name__ == "__main__":
    main()
