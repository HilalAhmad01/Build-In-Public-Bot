import os
import re
import psycopg2
from langgraph.types import interrupt

from state import TweetBotState
from fetch_readme import fetch_readme          # your existing module
from readme_checker import is_readme_ready     # your existing module

import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
GEMINI_MODEL = genai.GenerativeModel("gemini-3.5-flash")

DATABASE_URL = os.environ["DATABASE_URL"]


# ---------- Node 1: fetch_repo_data ----------
def fetch_repo_data(state: TweetBotState) -> dict:
    """Fetches the README and runs it through the quality checker."""
    try:
        readme_text = fetch_readme(state["owner"], state["repo"])
        check = is_readme_ready(readme_text)
        return {
            "readme_text": readme_text,
            "readme_check": check,
        }
    except Exception as e:
        return {"error": f"fetch_repo_data failed: {e}"}


# ---------- Conditional gate ----------
def is_ready_router(state: TweetBotState) -> str:
    """Decides whether to continue to extraction or stop the run."""
    if state.get("error"):
        return "end"
    if state.get("readme_check", {}).get("ready"):
        return "continue"
    return "end"


# ---------- Node 2: extract_context ----------
def extract_context(state: TweetBotState) -> dict:
    """Pulls clean image URLs and a demo link out of the README."""
    check = state["readme_check"]

    # Convert GitHub 'blob' viewer links into real raw image URLs
    fixed_images = []
    for url in check.get("image_urls", []):
        raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        fixed_images.append(raw_url)

    demo_urls = check.get("demo_urls", [])
    demo_link = demo_urls[0] if demo_urls else None

    return {
        "images": fixed_images,
        "demo_link": demo_link,
    }


# ---------- Node 3: generate_tweet ----------
def generate_tweet(state: TweetBotState) -> dict:
    """Calls Gemini to draft a build-in-public tweet from the repo context."""
    readme_snippet = state["readme_text"][:3000]  # keep prompt lean
    demo_line = f"\nDemo link: {state['demo_link']}" if state.get("demo_link") else ""

    prompt = f"""You write short, punchy "build in public" tweets announcing a
finished side project. Given the README content below, write ONE tweet
(under 280 characters) that:
- Opens with a strong hook, not just the project name
- Mentions 2-3 standout features
- Sounds like an excited indie developer, not marketing copy
- Includes the demo link if one is given
- No hashtags, no emojis unless truly natural

Repo: {state['full_name']}{demo_line}

README:
{readme_snippet}

Return ONLY the tweet text, nothing else."""

    response = GEMINI_MODEL.generate_content(prompt)
    draft = response.text.strip()

    return {"draft_tweet": draft}


# ---------- Node 4: request_approval ----------
def request_approval(state: TweetBotState) -> dict:
    """
    Pauses the graph here using LangGraph's interrupt mechanism.
    Execution stops, state is checkpointed to Postgres, and this function
    call effectively "returns" only when the graph is resumed externally
    (e.g. by your Telegram bot's Approve button) with a Command(resume=...).
    """
    decision = interrupt({
        "draft_tweet": state["draft_tweet"],
        "images": state.get("images", []),
        "full_name": state["full_name"],
    })
    # `decision` is whatever value the resume call passes in, e.g. "approved"
    return {"approval_status": decision}


# ---------- Conditional gate after approval ----------
def approval_router(state: TweetBotState) -> str:
    if state.get("approval_status") == "approved":
        return "post"
    return "skip"


# ---------- Node 5: post_tweet ----------
def post_tweet(state: TweetBotState) -> dict:
    """
    Placeholder for the X API call — wire this up once you've set up
    X API credentials (the next build step after this pipeline works).
    """
    # TODO: replace with real tweepy / twitter-api-v2 call
    print(f"[POST_TWEET STUB] Would post:\n{state['draft_tweet']}")
    fake_tweet_id = "PENDING_X_API_INTEGRATION"
    return {"tweet_id": fake_tweet_id}


# ---------- Node 6: log_result ----------
def log_result(state: TweetBotState) -> dict:
    """Writes the final outcome back to your repo_status table."""
    final_status = "posted" if state.get("tweet_id") else "rejected"

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO repo_status (full_name, status, tweet_text, tweet_id, last_checked_at)
        VALUES (%s, %s, %s, %s, NOW())
        ON CONFLICT (full_name)
        DO UPDATE SET status = EXCLUDED.status,
                      tweet_text = EXCLUDED.tweet_text,
                      tweet_id = EXCLUDED.tweet_id,
                      last_checked_at = NOW()
        """,
        (state["full_name"], final_status, state.get("draft_tweet"), state.get("tweet_id")),
    )
    conn.commit()
    cur.close()
    conn.close()

    return {}
