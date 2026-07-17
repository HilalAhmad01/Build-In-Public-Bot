import hashlib
import hmac
import os
from contextlib import asynccontextmanager

import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command

from graph_build import build_graph
from telegram_bot import answer_callback_query, edit_message_after_decision

load_dotenv()

WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"].encode()
DATABASE_URL = os.environ["DATABASE_URL"]

# These get set once at startup and reused for every request —
# see lifespan() below.
app_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):

    checkpointer_cm = PostgresSaver.from_conn_string(DATABASE_URL)
    checkpointer = checkpointer_cm.__enter__()
    checkpointer.setup()  # safe to call every startup, no-op if tables exist

    graph = build_graph(checkpointer)

    app_state["graph"] = graph
    app_state["checkpointer_cm"] = checkpointer_cm

    print("Startup complete: graph + checkpointer ready")

    yield  # app runs here

    # Shutdown: close the Postgres connection cleanly
    checkpointer_cm.__exit__(None, None, None)
    print("Shutdown complete: checkpointer connection closed")


app = FastAPI(lifespan=lifespan)


def verify_signature(payload_body: bytes, signature_header: str):
    if not signature_header:
        raise HTTPException(status_code=403, detail="Missing signature")
    expected = "sha256=" + hmac.new(WEBHOOK_SECRET, payload_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=403, detail="Invalid signature")


def get_repo_status(full_name: str):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT status FROM repo_status WHERE full_name = %s", (full_name,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


@app.post("/webhook")
async def webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None),
):
    body = await request.body()
    verify_signature(body, x_hub_signature_256)
    payload = await request.json()

    if x_github_event != "push":
        return {"status": "ignored", "reason": "not a push event"}

    full_name = payload["repository"]["full_name"]
    owner, repo = full_name.split("/")

    current_status = get_repo_status(full_name)
    if current_status in ("ready", "posted"):
        print(f"{full_name} already processed (status={current_status}), skipping")
        return {"status": "skipped", "reason": current_status}

    print(f"push event received for repo {full_name}, starting graph run")

    graph = app_state["graph"]
    config = {"configurable": {"thread_id": full_name}}
    initial_state = {"owner": owner, "repo": repo, "full_name": full_name}


    result = await run_in_threadpool(graph.invoke, initial_state, config=config)

    if "__interrupt__" in result:
        print(f"{full_name}: paused for approval, draft ready")
        return {"status": "awaiting_approval", "repo": full_name}

    print(f"{full_name}: run finished without pausing (README likely not ready yet)")
    return {"status": "not_ready", "repo": full_name}


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):

    update = await request.json()

    callback_query = update.get("callback_query")
    if not callback_query:
        return {"status": "ignored"}

    callback_data = callback_query["data"]
    decision_raw, full_name = callback_data.split("|", 1)
    decision = "approved" if decision_raw == "approve" else "rejected"

    graph = app_state["graph"]
    config = {"configurable": {"thread_id": full_name}}

    await run_in_threadpool(graph.invoke, Command(resume=decision), config=config)

    answer_callback_query(callback_query["id"], f"Marked as {decision}")

    message = callback_query["message"]
    has_photo = "photo" in message
    original_text = message.get("caption") or message.get("text") or ""

    edit_message_after_decision(
        chat_id=message["chat"]["id"],
        message_id=message["message_id"],
        original_text=original_text,
        decision=decision,
        has_photo=has_photo,
    )

    print(f"{full_name}: resumed with decision={decision}")
    return {"status": "processed", "decision": decision, "repo": full_name}
