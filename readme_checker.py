import re


def is_readme_ready(readme_text: str) -> dict:
    """
    Analyzes README text and decides if it's substantial enough to tweet about.
    Returns a dict with individual check results and a final verdict.
    """

    readme_text = readme_text.replace("\\n", "\n")
    readme_text = readme_text.replace("\r\n", "\n")

    word_count = len(readme_text.split())
    has_enough_words = word_count >= 100

    # Allow leading whitespace before the # (handles indented test strings too)
    headers = re.findall(r"^[ \t]*#{1,3}\s.+", readme_text, re.MULTILINE)
    header_count = len(headers)
    has_enough_headers = header_count >= 2

    images = re.findall(r"!\[.*?\]\((.*?)\)", readme_text)
    has_image = len(images) > 0

    demo_domains = re.findall(
        r"https?://[^\s\)]*(?:vercel\.app|netlify\.app|github\.io|herokuapp\.com)[^\s\)]*",
        readme_text,
    )
    demo_line_match = re.search(
        r"^.*(demo|live)[:\s].*https?://\S+", readme_text, re.IGNORECASE | re.MULTILINE
    )
    has_demo_link = bool(demo_domains or demo_line_match)

    is_ready = has_enough_words and has_enough_headers and has_image

    return {
        "ready": is_ready,
        "word_count": word_count,
        "has_enough_words": has_enough_words,
        "header_count": header_count,
        "has_enough_headers": has_enough_headers,
        "has_image": has_image,
        "image_urls": images,
        "has_demo_link": has_demo_link,
        "demo_urls": demo_domains,
    }


if __name__ == "__main__":
    good_readme = """
    <div align="center">

    # MINDS EYE

    ### An AI-powered Copilot that lives inside your Obsidian vault.

    **Chat with your notes. Generate flashcards. Summarize topics. All locally.**



    </div>

    ---

    ## 📖 What is this?

    **Obsidian Recall** turns your static Markdown notes into a living, queryable knowledge base — directly inside Obsidian's sidebar. Point it at your vault, sync once, and you can:

    - **Ask questions** about anything you've ever written
    - **Summarize** entire files or broad topics with one command
    - **Generate flashcards** from technical notes for active recall
    - **Find files** by describing what's in them, not by remembering the name

    It runs **100% locally** — your notes never leave your machine. The only external call is to the Cohere API for embeddings.

    ---


    ![Python](https://github.com/HilalAhmad01/Obsidian-Recall/blob/main/images/summarize%20command.png)

    ---

    ![LangChain](https://github.com/HilalAhmad01/Obsidian-Recall/blob/main/images/flashcard.png)

    ---

    ![ChromaDB](https://github.com/HilalAhmad01/Obsidian-Recall/blob/main/images/summarize%20command.png)


    ---

    ## ✨ Features

    | Feature | Description |
    |---|---|
    | 🔄 **Incremental Sync** | Only indexes new notes. Saves Cohere API credits and CPU on every sync. |
    | 💬 **RAG Chat** | Ask natural language questions, get answers grounded in your actual notes. |
    | 📄 **File Summarization** | Condense any single note into clean key takeaways instantly. |
    | 🌐 **Topic Summarization** | Synthesize information spread across multiple files on any subject. |
    | 🃏 **Flashcard Generation** | Auto-generate Q&A study cards from technical notes for exam prep. |
    | 🔍 **Semantic File Search** | Find files by describing their content — no exact filename needed. |
    | 📋 **Vault Index** | See every file the AI can currently "see" and interact with. |
    | 🖥️ **Obsidian Sidebar UI** | A clean, native-feeling panel built directly into Obsidian. |

    ---

    ## 🛠️ Tech Stack

    ```
    ┌─────────────────────────────────────────────────────┐
    │                   Obsidian Plugin                   │  ← main.ts (TypeScript)
    │              Sidebar UI + Command Router             │
    └─────────────────────────┬───────────────────────────┘
                              │ HTTP (localhost:8000)
    ┌─────────────────────────▼───────────────────────────┐
    │                  FastAPI Server                     │  ← server.py
    │            REST API + LangChain Chains              │
    └──────┬────────────────────────────┬─────────────────┘
           │                            │
    ┌──────▼──────┐             ┌───────▼───────┐
    │   Ollama    │             │    ChromaDB   │
    │  Gemma 2B   │             │  Vector Store │  ← ./chroma_db
    │    (LLM)    │             │  (cosine sim) │
    └─────────────┘             └───────┬───────┘
                                        │
                                ┌───────▼───────┐
                                │    Cohere     │
                                │  Embeddings   │
                                │   embed-v4.0  │
                                └───────────────┘
    ```

    ---

    ## 📁 Project Structure

    ```
    obsidian-recall/
    │
    ├── main.py              # Core logic: loading, embedding, RAG chains, commands
    ├── server.py            # FastAPI server exposing all features as REST endpoints
    ├── main.ts              # Obsidian plugin (TypeScript) — the sidebar UI
    │
    ├── chroma_db/           # Auto-generated: persisted vector store (gitignored)
    ├── .env                 # Your API keys (gitignored)
    ├── requirements.txt     # Python dependencies
    └── README.md
    ```

    ---

    ## 🚀 Setup & Installation

    ### Prerequisites

    Make sure you have these installed before you begin:

    - [Python 3.10+](https://www.python.org/downloads/)
    - [Ollama](https://ollama.com/) with Gemma 2B pulled
    - [Node.js](https://nodejs.org/) (for building the Obsidian plugin)
    - An active [Cohere API Key](https://dashboard.cohere.com/)

    ---

    ### Step 1 — Clone the Repository

    ```bash
    git clone https://github.com/HilalAhmad01/Obsidian-Recall.git
    cd Obsidian-Recall
    ```

    ### Step 2 — Install Python Dependencies

    ```bash
    pip install -r requirements.txt
    ```

    ### Step 3 — Pull the LLM via Ollama

    ```bash
    ollama pull gemma2:2b
    ```

    ### Step 4 — Configure Your Environment

    Create a `.env` file in the root of the project:

    ```env
    COHERE_API_KEY=your_cohere_api_key_here
    ```

    ### Step 5 — Set Your Vault Path

    Open `main.py` and `server.py` and update the vault path to point to your Obsidian notes folder:

    ```python
    # In main.py and server.py, find this line and update it:
    vault_path = "/your/path/to/Notes"   # ← change this
    ```

    ### Step 6 — Build & Install the Obsidian Plugin

    Copy `main.ts` (compiled to `main.js`) into your vault's plugin folder:

    ```
    YourVault/.obsidian/plugins/obsidian-recall/main.js
    ```

    Then go to **Obsidian → Settings → Community Plugins** and enable **Obsidian Recall**.

    ### Step 7 — Start the Server

    ```bash
    python server.py
    ```

    The API will be live at `http://127.0.0.1:8000`.

    ### Step 8 — Sync Your Vault

    Click the **🔄 Sync** button in the Obsidian sidebar to index your notes for the first time. This only needs to run fully once — future syncs are incremental.

    ---

    ## 💬 Commands Reference

    Open the **Vault Copilot** panel from the left ribbon (🤖 icon) and use these commands:

    | Command | Usage | Description |
    |---|---|---|
    | `/list` | `/list` | Lists every Markdown file currently indexed in the vector store. |
    | `/find` | `/find mlops architecture` | Semantically searches for files matching a description. |
    | `/summarize_file` | `/summarize_file Biology.md` | Summarizes a single specific file from your vault. |
    | `/summarize` | `/summarize Neural Networks` | Synthesizes notes on a topic across your entire vault. |
    | `/flashcards` | `/flashcards OS_Notes.md` | Generates 5 study flashcards from the specified file. |
    | **Chat** | `What is backpropagation?` | Any non-command text triggers a full RAG chat query. |

    > **Tip:** Click the `/list`, `/summarize`, or `/flashcards` hint chips at the bottom of the panel to auto-fill the command prefix.

    ---

    ## 🔌 API Endpoints

    If you want to interact with the backend directly (e.g., for scripting or testing):

    | Method | Endpoint | Payload | Description |
    |---|---|---|---|
    | `GET` | `/sync` | — | Re-scans vault and indexes new files |
    | `GET` | `/list` | — | Returns all indexed filenames |
    | `POST` | `/chat` | `{ "message": "..." }` | General RAG chat |
    | `POST` | `/summarize` | `{ "topic": "..." }` | Topic-based summarization |
    | `POST` | `/summarize_file` | `{ "filename": "..." }` | Single-file summarization |
    | `POST` | `/flashcards` | `{ "filename": "..." }` | Flashcard generation |
    | `POST` | `/find-notes` | `{ "topic": "..." }` | Semantic file search |

    Interactive docs available at: `http://127.0.0.1:8000/docs`

    ---

    ## ⚙️ How It Works

    ```
    Your .md files
          │
          ▼
    MarkdownHeaderTextSplitter   ← splits on #, ##, ###
          │
          ▼
    RecursiveCharacterTextSplitter  ← 512 tokens, 60 overlap
          │
          ▼
    Cohere embed-v4.0            ← generates dense vectors
          │
          ▼
    ChromaDB (cosine similarity) ← persisted to ./chroma_db
          │
          ▼
    Query → Retrieve top-k chunks → LangChain Chain → Gemma 2B → Response
    ```

    On every sync, only **new files** are embedded — existing ones are skipped. This keeps your Cohere API usage minimal.

    ---

    ## 🗺️ Roadmap

    - [ ] Delete/re-index individual files from the UI
    - [ ] Support for PDF and web clip ingestion
    - [ ] Streaming responses in the sidebar
    - [ ] Spaced repetition tracker for flashcards
    - [ ] Multi-vault support
    - [ ] Local embeddings option (eliminate Cohere dependency)

    ---

    ## 🤝 Contributing

    Contributions are welcome! Here's how to get started:

    ```bash
    # 1. Fork the repo and clone your fork
    git clone https://github.com/YOUR_USERNAME/Obsidian-Recall.git

    # 2. Create a feature branch
    git checkout -b feature/your-feature-name

    # 3. Make your changes and commit
    git commit -m "feat: add your feature"

    # 4. Push and open a Pull Request
    git push origin feature/your-feature-name
    ```

    Please open an issue first for major changes so we can discuss the approach.

    ---

    ## ⚠️ Known Limitations

    - The LLM (Gemma 2B) is small and fast, but may hallucinate on complex reasoning. Always verify important answers against your actual notes.
    - First-time indexing of large vaults may take several minutes depending on the number of files and your Cohere API tier.
    - The plugin currently requires `server.py` to be running manually before use.

    ---

    ## 📄 License

    This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

    ---



"""

    bad_readme = "# my-repo\n\nTODO: add description"

    for name, text in [("good_readme", good_readme), ("bad_readme", bad_readme)]:
        result = is_readme_ready(text)
        print(f"\n--- {name} ---")
        for key, value in result.items():
            print(f"{key}: {value}")
