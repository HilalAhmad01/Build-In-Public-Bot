import hashlib
import hmac
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

from fetch_readme import fetch_readme
from readme_checker import is_readme_ready

load_dotenv()

app = FastAPI()
WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"].encode()


def verify_signature(payload_body: bytes, signature_header: str):
    if not signature_header:
        raise HTTPException(status_code=403, detail="Missing signature")
    expected = (
        "sha256=" + hmac.new(WEBHOOK_SECRET, payload_body, hashlib.sha256).hexdigest()
    )
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=403, detail="Invalid signature")


@app.post("/webhook")
async def webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None),
):
    body = await request.body()
    verify_signature(body, x_hub_signature_256)
    payload = await request.json()

    if x_github_event == "push":
        full_name = payload["repository"]["full_name"]  # e.g. "HilalAhmad01/Minds-Eye"
        owner, repo = full_name.split("/")
        print(f"push event received for repo {full_name}")

        try:
            readme_text = fetch_readme(owner, repo)
            result = is_readme_ready(readme_text)
            print(f"README ready check for {full_name}: {result['ready']}")
            print(
                f"  words={result['word_count']} headers={result['header_count']} has_image={result['has_image']}"
            )
        except Exception as e:
            print(f"Failed to fetch/check README for {full_name}: {e}")

    return {"status": "ok"}
