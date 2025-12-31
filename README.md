# Financial Tracker — Module 1 (PDF → DataFrame)

This Streamlit app uploads a **PDF bank statement**, extracts its raw text, sends it to a **locally running Ollama LLM**, and converts the structured JSON response into a **Pandas DataFrame**.

## Prereqs
- Python 3.10+ recommended
- Ollama installed and running: https://ollama.com
- A model pulled locally (example):
  - `ollama pull llama3.2`

## Configure (optional)
Set environment variables (PowerShell examples):
- `setx OLLAMA_HOST "http://localhost:11434"`
- `setx OLLAMA_MODEL "llama3.2"`

Defaults:
- `OLLAMA_HOST=http://localhost:11434`
- `OLLAMA_MODEL=gemini-3-flash-preview:cloud`

## Install
```powershell
cd "d:\Code\Financial Tracker"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run
```powershell
cd "d:\Code\Financial Tracker"
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Upload a PDF statement and the app will display the raw extracted DataFrame.
