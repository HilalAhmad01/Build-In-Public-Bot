import base64
import os

import requests
from dotenv import load_dotenv

from readme_checker import is_readme_ready

load_dotenv()

GITHUB_API_TOKEN = os.environ["GITHUB_API_TOKEN"]


def fetch_readme(owner: str, repo: str) -> str:
    """
    Fetches the README content for a given repo via the GitHub API.
    Returns the decoded plain text.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {
        "Authorization": f"Bearer {GITHUB_API_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # raises an error if the request failed

    data = response.json()
    encoded_content = data["content"]
    decoded_bytes = base64.b64decode(encoded_content)
    readme_text = decoded_bytes.decode("utf-8")

    return readme_text


if __name__ == "__main__":
    text = fetch_readme("HilalAhmad01", "Minds-Eye")
    result = is_readme_ready(text)
    for key, value in result.items():
        print(f"{key}: {value}")
