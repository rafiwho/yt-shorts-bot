import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CLIENT_SECRET = os.path.join(ROOT, "client_secret.json")
TOKEN_PATH = os.path.join(ROOT, "token.json")
VIDEO_PATH = os.path.join(ROOT, "output.mp4")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]

def main():
    if not os.path.isfile(CLIENT_SECRET):
        print("Missing client_secret.json. Create OAuth Desktop credentials in Google Cloud Console.")
        sys.exit(1)
    if not os.path.isfile(VIDEO_PATH):
        print("Missing output.mp4. Run run_local.py or download the workflow artifact first.")
        sys.exit(1)

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = None
    if os.path.isfile(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    youtube = build("youtube", "v3", credentials=creds)

    output_txt_path = os.path.join(ROOT, "output.txt")
    script_text = ""
    if os.path.isfile(output_txt_path):
        try:
            with open(output_txt_path, "r", encoding="utf-8", errors="replace") as f:
                script_text = f.read().strip()
        except Exception:
            pass
    title = (script_text[:80] + "…") if len(script_text) > 80 else script_text
    if not title:
        title = "Shorts #shorts"

    body = {
        "snippet": {
            "title": title + " #shorts",
            "description": script_text + "\n\n#Shorts",
            "tags": ["shorts", "short"],
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "public",
        },
    }

    media = MediaFileUpload(VIDEO_PATH, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    try:
        response = request.execute()
    except Exception as e:
        err = str(e).lower()
        if "uploadlimit" in err and "exceeded" in err or "exceeded the number of videos" in err:
            print("YouTube upload limit exceeded.", file=sys.stderr)
            sys.exit(3)
        raise
    vid = response.get("id")
    print(f"Uploaded video id: {vid}")
    print(f"https://www.youtube.com/shorts/{vid}")
    del media
    for _ in range(5):
        try:
            time.sleep(1)
            os.remove(VIDEO_PATH)
            break
        except PermissionError:
            pass
    for _ in range(5):
        try:
            time.sleep(0.5)
            if os.path.isfile(output_txt_path):
                os.remove(output_txt_path)
            break
        except (PermissionError, FileNotFoundError):
            pass

if __name__ == "__main__":
    main()
