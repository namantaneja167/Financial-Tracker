# 💰 Financial Tracker Pro Max

A personal finance dashboard powered by **Next.js** and **FastAPI**, designed to give you a premium, "Pro Max" overview of your financial life. This application allows you to import bank statements from PDF or CSV files, automatically categorizes your transactions using AI, and provides fluid bento-grid visualizations to help you understand your spending habits.

![Financial Tracker Dashboard](https://i.imgur.com/your-screenshot.png) <!-- Replace with an actual screenshot -->

## ✨ Key Features

-   **Pro Max UI**: A stunning, dark-mode first interface built with Tailwind CSS v4 and Framer Motion.
-   **📄 Import from PDF & CSV**: Seamlessly import your transaction history.
-   **🤖 AI-Powered Categorization**: Leveraging local language models (Ollama), the app automatically categorizes transactions.
-   **📊 Bento Grid Dashboard**: A responsive grid showing Net Worth, Monthly Spend, and Trends at a glance.
-   **🔒 Privacy-Focused**: Your financial data stays on your local machine. Backend runs locally.

## 🚀 Getting Started

### Prerequisites

-   **Node.js 18+**
-   **Python 3.10+**
-   **Ollama**: [Download and install Ollama](https://ollama.com).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd financial-tracker
    ```

2.  **Setup Backend:**
    ```powershell
    # Create virtual env
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    
    # Install dependencies
    pip install -r backend/requirements.txt
    ```

3.  **Setup Frontend:**
    ```powershell
    cd frontend
    npm install
    ```

### Running the Application

You need to run both the backend (API) and frontend (UI) terminals.

**Terminal 1: Backend**
```powershell
# From root directory
uvicorn backend.main:app --reload
```
*API running at http://localhost:8000*

**Terminal 2: Frontend**
```powershell
# From root directory
cd frontend
npm run dev
```
*UI running at http://localhost:3000*

## ⚙️ Configuration

-   `OLLAMA_HOST`: Default `http://localhost:11434`
-   `OLLAMA_MODEL`: Default `gemma3:4b` (Change in `financial_tracker/config.py` or env vars)

## 🛠️ Built With

-   **Frontend**: Next.js 14, Tailwind CSS v4, Framer Motion, Shadcn Concepts
-   **Backend**: FastAPI, Pandas
-   **AI**: Ollama