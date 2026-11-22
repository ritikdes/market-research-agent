# Multi-Agent Market Research App

This project is a market research tool built with Python, Streamlit, Pydantic, DuckDuckGo search (`ddgs`), and the Google Gemini API (`google-genai`). You enter a topic or company query, and four steps run in sequence: **Orchestrator**, **Researcher**, **Analyst**, and **Critic**.

Tested with **Python 3.14.4** and **Gemini 3.1-Flash-lite** (`gemini-3.1-flash-lite`).

---

## How It Works

```text
User Query (Streamlit UI)
        |
        v
  [Orchestrator] -- Starts the workflow and passes data between steps
        |
        v
   [Researcher]  -- Runs search queries via ddgs (or uses sample fallback data if search returns nothing)
        |
        v
    [Analyst]    -- Turns search snippets into a structured brief (summary, up to 2 competitors, observations, sources, missing info)
        |
        v
     [Critic]    -- Checks the draft against the gathered snippets and asks for one revision if needed
        |
        ├── Approved ─────────────────────────► Final Brief + Markdown Download
        └── Revision Needed (at most 1 time) ► [Analyst Revision] ► [Critic Check] ► Final Brief
```

### Key Choices
* **Pydantic models (`schemas.py`):** Each step reads and updates a shared `ResearchState` object so data stays structured from start to finish.
* **Sticking to snippets:** The Analyst prompt tells the model to rely on the returned search snippets instead of guessing numbers, and to list gaps under **Missing Information**.
* **One revision cap:** The Critic can ask for a rewrite at most once so the app does not get stuck in a loop.
* **URL cleanup (`tools.py`):** Some search links come back as redirect URLs, so `_clean_url` extracts the target link when possible.

---

## Project Structure

```text
market-research-agent/
├── app.py              # Streamlit interface and Markdown export
├── agents.py           # Orchestrator, Researcher, Analyst, and Critic logic
├── schemas.py          # Pydantic data models
├── llm.py              # Gemini API helper
├── tools.py            # DuckDuckGo search and URL cleanup
├── requirements.txt    # Python packages
├── .env.example        # Example environment file
├── .gitignore          # Ignored files and folders
├── sample_output.md    # Example output generated from the query: "Analyze the electric vehicle (EV) market in Nepal."
└── README.md           # Setup and usage notes
```

---

## Local Setup & Running the App

### 1. Clone the Repository
```bash
git clone [https://github.com/ritikdes/market-research-agent.git](https://github.com/ritikdes/market-research-agent.git)
cd market-research-agent
```

### 2. Create & Activate a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
*(On macOS/Linux, you can run `cp .env.example .env`.)*

Open `.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
```

### 5. Launch the Streamlit Application
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser, type a query such as `Analyze the electric vehicle (EV) market in Nepal.`, run the research, and download the Markdown report.

---

## Limitations

* **Snippets only, not full articles:** The Researcher reads short search result snippets rather than scraping or reading entire web pages, so detailed figures from long reports can be missed.
* **Thin results for smaller markets:** DuckDuckGo results can be limited or uneven for niche topics and smaller markets such as Nepal, which is why **Missing Information** and sample fallback data exist.
* **No guarantee of full accuracy after one revision:** Because revisions are capped at one pass, a brief may still note remaining gaps or critic concerns when displayed.