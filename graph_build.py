import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

from state import TweetBotState
from nodes import (
    fetch_repo_data,
    is_ready_router,
    extract_context,
    generate_tweet,
    request_approval,
    approval_router,
    post_tweet,
    log_result,
)

DATABASE_URL = os.environ["DATABASE_URL"]


def build_graph():
    builder = StateGraph(TweetBotState)

    builder.add_node("fetch_repo_data", fetch_repo_data)
    builder.add_node("extract_context", extract_context)
    builder.add_node("generate_tweet", generate_tweet)
    builder.add_node("request_approval", request_approval)
    builder.add_node("post_tweet", post_tweet)
    builder.add_node("log_result", log_result)

    builder.add_edge(START, "fetch_repo_data")

    builder.add_conditional_edges(
        "fetch_repo_data",
        is_ready_router,
        {"continue": "extract_context", "end": END},
    )

    builder.add_edge("extract_context", "generate_tweet")
    builder.add_edge("generate_tweet", "request_approval")

    builder.add_conditional_edges(
        "request_approval",
        approval_router,
        {"post": "post_tweet", "skip": "log_result"},
    )

    builder.add_edge("post_tweet", "log_result")
    builder.add_edge("log_result", END)

    # Postgres checkpointer: this is what lets the graph pause at
    # request_approval and survive until you resume it later, even
    # across server restarts.
    checkpointer_cm = PostgresSaver.from_conn_string(DATABASE_URL)
    checkpointer = checkpointer_cm.__enter__()
    checkpointer.setup()  # creates the checkpoint tables on first run, safe to call repeatedly

    graph = builder.compile(checkpointer=checkpointer)
    return graph
