import os
from dotenv import load_dotenv
load_dotenv()

from langgraph.types import Command
from langgraph.checkpoint.postgres import PostgresSaver
from graph_build import build_graph

DATABASE_URL = os.environ["DATABASE_URL"]

# Every graph run needs a unique thread_id — this is the key LangGraph
# uses to find and resume a specific paused run later.
OWNER = "HilalAhmad01"
REPO = "Minds-Eye"
THREAD_ID = f"{OWNER}/{REPO}"

config = {"configurable": {"thread_id": THREAD_ID}}

initial_state = {
    "owner": OWNER,
    "repo": REPO,
    "full_name": f"{OWNER}/{REPO}",
}

# The `with` block keeps the Postgres connection open for as long as we
# need it — this must wrap EVERY graph.invoke() call, including the
# resume call after approval. Closing it early is what caused the
# "connection is closed" error.
with PostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
    checkpointer.setup()  # creates the checkpoint tables on first run, safe to call repeatedly
    graph = build_graph(checkpointer)

    print("--- Starting graph run ---")
    result = graph.invoke(initial_state, config=config)

    # If the graph hit request_approval, it will have paused here.
    # LangGraph surfaces this as an "__interrupt__" key in the result.
    if "__interrupt__" in result:
        interrupt_data = result["__interrupt__"][0].value
        print("\n--- PAUSED FOR APPROVAL ---")
        print("Draft tweet:\n", interrupt_data["draft_tweet"])
        print("Images:", interrupt_data["images"])

        decision = input("\nApprove this tweet? (y/n): ").strip().lower()
        resume_value = "approved" if decision == "y" else "rejected"

        print("\n--- Resuming graph ---")
        final_result = graph.invoke(Command(resume=resume_value), config=config)
        print("\n--- Final state ---")
        print(final_result)
    else:
        print("\n--- Graph finished without pausing (README likely not ready) ---")
        print(result)
