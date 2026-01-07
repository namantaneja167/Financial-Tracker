
import json
import requests
from typing import List, Dict, Any, Generator
from financial_tracker.database import get_all_transactions
from financial_tracker.analytics import prep_analytics_frame
from financial_tracker.config import get_ollama_url, get_ollama_model, get_ollama_timeout
from financial_tracker.logging_config import get_logger

logger = get_logger(__name__)

def get_financial_context() -> str:
    """Aggregates financial data into a clean text summary for the AI."""
    try:
        df = get_all_transactions()
        if df.empty:
            return "No financial data available yet."

        analytics = prep_analytics_frame(df)
        
        # 1. Totals
        total_income = analytics["Income"].sum()
        total_expense = analytics["Expense"].sum()
        net_worth = total_income - total_expense
        savings_rate = ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0

        # 2. Monthly Trend (Last 3 months)
        recent_months = analytics.groupby("Month").agg({"Income": "sum", "Expense": "sum"}).sort_index(ascending=False).head(3)
        formatted_months = recent_months.to_string()

        # 3. Top Spending Categories (All time)
        top_categories = df[df["Type"] == "Debit"].groupby("Category")["Amount"].sum().sort_values(ascending=False).head(5)
        formatted_categories = top_categories.to_string()

        # 4. Recent Transactions (Last 5)
        recent_tx = df.sort_values("Date", ascending=False).head(5)[["Date", "Description", "Amount", "Category"]]
        formatted_tx = recent_tx.to_string(index=False)

        context = f"""
Financial Summary:
- Net Worth: ${net_worth:,.2f}
- Total Income: ${total_income:,.2f}
- Total Spend: ${total_expense:,.2f}
- Savings Rate: {savings_rate:.1f}%

Recent Monthly Trend (Last 3 Months):
{formatted_months}

Top 5 Spending Categories:
{formatted_categories}

Most Recent 5 Transactions:
{formatted_tx}
"""
        return context
    except Exception as e:
        logger.error(f"Error generating context: {e}")
        return "Error loading financial context."

def stream_chat_response(user_message: str) -> Generator[str, None, None]:
    """Streams response from Gemini with financial context."""
    import google.generativeai as genai
    from financial_tracker.config import get_google_api_key, get_gemini_model

    api_key = get_google_api_key()
    if not api_key:
        yield "Error: GOOGLE_API_KEY not found. Please check your .env file."
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(get_gemini_model())
    
    context = get_financial_context()
    
    system_prompt = (
        "You are an AI Financial Analyst. You have access to the user's financial data below.\n"
        "Your goal is to provide helpful, concise, and actionable insights.\n"
        "If you don't know the answer, say so.\n"
        "Be professional but approachable (like a helpful advisor).\n\n"
        f"--- USER FINANCIAL DATA ---\n{context}\n---------------------------\n"
    )

    # Gemini Chat History
    # We combine system prompt and user message for a single turn if sticking to simple usage,
    # or we can start a chat session. For strict system instruction adherence in Gemini, 
    # explicitly constructing the prompt is often robust.
    
    full_prompt = f"{system_prompt}\nUser: {user_message}\nAnalyst:"

    try:
        logger.info("Sending chat request to Gemini...")
        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        logger.error(f"Gemini Chat error: {e}")
        yield f"Error connecting to AI: {str(e)}"
