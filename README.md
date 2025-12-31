# 💰 Financial Tracker

A personal finance dashboard powered by Streamlit, designed to give you a clear and comprehensive overview of your financial life. This application allows you to import bank statements from PDF or CSV files, automatically categorizes your transactions using AI, and provides visualizations to help you understand your spending habits, track your net worth, and manage your budget.

![Financial Tracker Dashboard](httpsp://i.imgur.com/your-screenshot.png) <!-- Replace with an actual screenshot -->

## ✨ Key Features

-   **📄 Import from PDF & CSV**: Seamlessly import your transaction history from both PDF bank statements and CSV files.
-   **🤖 AI-Powered Categorization**: Leveraging the power of local language models (via Ollama), the app automatically categorizes your expenses and income.
-   **📊 Interactive Dashboard**: A comprehensive overview of your finances, including spending by category, income vs. expense, and recent transactions.
-   **📈 Net Worth Tracking**: Monitor your net worth over time by adding your assets and liabilities.
-   **💰 Budget Management**: Set monthly budgets for different categories and track your progress.
-   **🔄 Recurring Transactions**: Keep an eye on your subscriptions and recurring payments.
-   **💼 Investment Tracking**: A dedicated section to monitor the performance of your investment portfolio.
-   **Normalize Merchants**: Clean up and group messy merchant names (e.g., "AMZNMKTPLACE" becomes "Amazon").
-   **🌙 Light & Dark Themes**: Choose a theme that's easy on your eyes.
-   **🔒 Privacy-Focused**: Your financial data stays on your local machine.

## 🚀 Getting Started

Follow these instructions to get the Financial Tracker up and running on your local machine.

### Prerequisites

-   **Python 3.10+**
-   **Ollama**: This application uses a locally running Ollama instance for AI-based transaction extraction and categorization.
    -   [Download and install Ollama](https://ollama.com)
    -   Pull a model for the application to use. For example:
        ```bash
        ollama pull llama3
        ```

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd financial-tracker
    ```

2.  **Create and activate a virtual environment:**
    -   On Windows:
        ```powershell
        python -m venv .venv
        .\.venv\Scripts\Activate.ps1
        ```
    -   On macOS/Linux:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Ensure Ollama is running** in the background.

2.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```

3.  Open your web browser and navigate to the URL provided by Streamlit (usually `http://localhost:8501`).

## usage

### Importing Data

1.  On the left sidebar, you'll find the **"📂 Import Data"** section.
2.  Choose the import type: **"Bank Statement PDF"** or **"CSV"**.
3.  Click the **"Upload..."** button and select the file from your computer.

The application will process the file, extract the transactions, categorize them, and add them to your dashboard.

## ⚙️ Configuration

You can configure the application by setting environment variables.

-   `OLLAMA_HOST`: The URL of your Ollama instance.
    -   Default: `http://localhost:11434`
-   `OLLAMA_MODEL`: The name of the Ollama model to use.
    -   Default: `gemma3:4b`
-   `OLLAMA_API_KEY`: Bearer token if your Ollama endpoint requires authentication (e.g., secured or cloud endpoint).
    -   Default: none (not needed for local default install)
-   `MAX_FILE_SIZE_MB`: The maximum file size for uploads in megabytes.
    -   Default: `20`

**Example (PowerShell):**
```powersall
$env:OLLAMA_MODEL="mistral"
```

## 🛠️ Built With

-   [Streamlit](https://streamlit.io/) - The web framework for the UI
-   [Pandas](https://pandas.pydata.org/) - For data manipulation and analysis
-   [Ollama](https://ollama.com/) - For local AI-powered features
-   [Plotly](https://plotly.com/python/) - For interactive charts and graphs

---