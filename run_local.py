import os
import re
import sys
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))

def ffmpeg_encoder():
    if os.environ.get("USE_GPU", "1").strip().lower() in ("0", "false", "no"):
        return "libx264", []
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=5,
    )
    if r.returncode != 0:
        return "libx264", []
    out = (r.stdout or "") + (r.stderr or "")
    if "h264_nvenc" in out:
        return "h264_nvenc", ["-preset", "p4", "-tune", "hq"]
    if "h264_amf" in out:
        return "h264_amf", ["-quality", "quality"]
    if "h264_qsv" in out:
        return "h264_qsv", []
    return "libx264", []

def main():
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as k:
                machine = winreg.QueryValueEx(k, "Path")[0]
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                user = winreg.QueryValueEx(k, "Path")[0]
            os.environ["Path"] = (machine or "") + ";" + (user or "")
        except Exception:
            pass
    os.chdir(ROOT)

    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "generate.py")],
        cwd=ROOT
    )
    if r.returncode == 2:
        sys.exit(2)
    r.check_returncode()

    r_bg = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "generate_bg.py")],
        cwd=ROOT,
    )
    if r_bg.returncode != 0:
        print("Background: using existing assets/bg.jpg or solid fallback.", file=sys.stderr)

    with open(os.path.join(ROOT, "output.txt"), "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    clean = re.sub(r"[^a-zA-Z0-9 .,?!]", " ", raw)

    voice_out = os.path.join(ROOT, "voice.wav")
    try:
        subprocess.run([
            "espeak-ng", "-s", "145", "-p", "55", "-v", "en", "-w", voice_out, clean
        ], check=True, cwd=ROOT)
    except FileNotFoundError:
        try:
            import asyncio
            import edge_tts
            async def _edge():
                communicate = edge_tts.Communicate(clean, "en-US-GuyNeural")
                mp3_path = os.path.join(ROOT, "voice_tts.mp3")
                await communicate.save(mp3_path)
                return mp3_path
            mp3_path = asyncio.run(_edge())
            subprocess.run(
                ["ffmpeg", "-y", "-i", mp3_path, "-ar", "22050", "-ac", "1", voice_out],
                check=True, cwd=ROOT, capture_output=True
            )
            try:
                os.remove(mp3_path)
            except Exception:
                pass
        except Exception:
            import time
            import pyttsx3
            for attempt in range(2):
                engine = pyttsx3.init()
                engine.setProperty("rate", 145)
                engine.save_to_file(clean, voice_out)
                engine.runAndWait()
                time.sleep(0.5)
                if os.path.isfile(voice_out) and os.path.getsize(voice_out) > 5000:
                    break
                if attempt == 1:
                    print("TTS produced an empty or invalid voice.wav", file=sys.stderr)
                    sys.exit(1)
    if not os.path.isfile(voice_out) or os.path.getsize(voice_out) < 5000:
        print("voice.wav missing or too small", file=sys.stderr)
        sys.exit(1)

    bg_path = os.path.join(ROOT, "assets", "bg.jpg")
    if not os.path.isfile(bg_path):
        os.makedirs(os.path.dirname(bg_path), exist_ok=True)
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x1a1a2e:s=720x1280:d=1",
            "-frames:v", "1", bg_path
        ], check=True, cwd=ROOT, capture_output=True)
    silent_mp4 = os.path.join(ROOT, "silent.mp4")
    vcodec, vopts = ffmpeg_encoder()
    if vcodec == "libx264":
        cmd = ["ffmpeg", "-y", "-threads", "1", "-loop", "1", "-i", bg_path, "-vf", "scale=720:1280", "-t", "8", "-pix_fmt", "yuv420p", silent_mp4]
    else:
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", bg_path, "-vf", "scale=720:1280", "-t", "8", "-pix_fmt", "yuv420p", "-c:v", vcodec] + vopts + [silent_mp4]
    try:
        subprocess.run(cmd, check=True, cwd=ROOT, capture_output=(vcodec != "libx264"))
    except subprocess.CalledProcessError:
        if vcodec != "libx264":
            subprocess.run([
                "ffmpeg", "-y", "-threads", "1",
                "-loop", "1", "-i", bg_path,
                "-vf", "scale=720:1280",
                "-t", "8", "-pix_fmt", "yuv420p", silent_mp4
            ], check=True, cwd=ROOT)
        else:
            raise

    out_mp4 = os.path.join(ROOT, "output.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", silent_mp4,
        "-i", voice_out,
        "-stream_loop", "-1", "-i", os.path.join(ROOT, "audio", "bg.mp3"),
        "-filter_complex", "[2:a]volume=0.15[a_bg];[1:a][a_bg]sidechaincompress=threshold=0.02:ratio=10:attack=5:release=200[a_mix]",
        "-map", "0:v", "-map", "[a_mix]", "-c:v", "copy", "-c:a", "aac", "-shortest",
        "-metadata:s:v:0", "rotate=0",
        out_mp4
    ], check=True, cwd=ROOT)

    print("Done. Output: output.mp4")

if __name__ == "__main__":
    main()
