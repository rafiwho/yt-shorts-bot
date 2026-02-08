import os
import sys
import time
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))

def main():
    os.chdir(ROOT)
    try:
        delay = int(os.environ.get("LOOP_DELAY", "60"))
    except ValueError:
        delay = 60
    n = 0
    try:
        while True:
            n += 1
            print(f"[{n}] Gen idea -> TTS -> FFmpeg...")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT, "run_local.py")],
                    check=True,
                    cwd=ROOT,
                )
            except subprocess.CalledProcessError as e:
                if e.returncode == 2:
                    print("Quota exceeded. Stopping.")
                    break
                raise
            print(f"[{n}] Upload...")
            r = subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "upload_local.py")],
                cwd=ROOT,
            )
            if r.returncode == 3:
                print("YouTube upload limit exceeded. Stopping.")
                break
            r.check_returncode()
            print(f"[{n}] Done. Next in {delay}s (Ctrl+C to stop).")
            time.sleep(delay)
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
