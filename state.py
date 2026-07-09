from typing import TypedDict, Optional, List


class TweetBotState(TypedDict):
    """
    The shared state object that flows through every node in the graph.
    Each node reads what it needs and writes new keys as it goes.
    """
    owner: str
    repo: str
    full_name: str

    readme_text: Optional[str]
    readme_check: Optional[dict]

    images: Optional[List[str]]
    demo_link: Optional[str]

    draft_tweet: Optional[str]

    approval_status: Optional[str]   # "approved" | "rejected" | None
    tweet_id: Optional[str]

    error: Optional[str]
