from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List, Optional, Dict
import shutil
import os
import pandas as pd
from datetime import date

# Import from existing logic
from financial_tracker.database import get_all_transactions, insert_transactions
from financial_tracker.pdf_parser import extract_text_from_pdf
from financial_tracker.ollama_client import ollama_extract_transactions
from financial_tracker.csv_importer import parse_csv_to_transactions
from financial_tracker.categorizer import categorize_transactions, get_category_overrides, save_overrides
from financial_tracker.merchant_normalizer import normalize_merchant
from financial_tracker.analytics import prep_analytics_frame
from financial_tracker.logging_config import get_logger
from backend.chat_service import stream_chat_response
from fastapi.responses import StreamingResponse

# Import Pydantic Schemas
from backend.schemas import (
    Transaction, StatsResponse, UploadResponse, CategorizeRequest, 
    GenericResponse, ChatRequest, SubscriptionResponse,
    GoalItem, GoalCreate, GoalContribution,
    AssetItem, AssetCreate, PortfolioResponse
)

logger = get_logger(__name__)
router = APIRouter()

@router.get("/transactions", response_model=List[Transaction])
def get_transactions():
    """Get all transactions sorted by date."""
    logger.info("Fetching all transactions")
    try:
        df = get_all_transactions()
        if df.empty:
            return []
        
        # Convert dates to string for JSON serialization
        if 'Date' in df.columns:
            df['Date'] = df['Date'].astype(str)
            
        # Robust NaN cleaning
        records = df.to_dict('records')
        cleaned = [{k: (v if pd.notnull(v) else None) for k, v in r.items()} for r in records]
            
        return cleaned
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """Get dashboard statistics (Net Worth, Monthly Spend, etc)."""
    logger.info("Calculating dashboard stats")
    try:
        df = get_all_transactions()
        if df.empty:
            return {
                "total_income": 0,
                "total_spend": 0,
                "savings_rate": 0,
                "monthly_trend": []
            }
            
        analytics = prep_analytics_frame(df)
        total_income = float(analytics["Income"].sum()) if not analytics.empty else 0.0
        total_spend = float(analytics["Expense"].sum()) if not analytics.empty else 0.0
        savings_rate = ((total_income - total_spend) / total_income * 100.0) if total_income > 0 else 0.0
        
        # Calculate monthly trend
        monthly_trend = analytics.groupby("Month").agg({"Income": "sum", "Expense": "sum"}).reset_index()
        
        # Convert Month to string if it's not
        monthly_trend['Month'] = monthly_trend['Month'].astype(str)
        
        # Robust NaN cleaning for trend
        trend_records = monthly_trend.to_dict('records')
        cleaned_trend = [{k: (v if pd.notnull(v) else None) for k, v in r.items()} for r in trend_records]
        
        return {
            "total_income": total_income,
            "total_spend": total_spend,
            "savings_rate": savings_rate,
            "monthly_trend": cleaned_trend
        }
    except Exception as e:
        logger.error(f"Error calculating stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...), type: str = "pdf"):
    """Handle file upload (PDF or CSV) and process transactions."""
    logger.info(f"Received file upload: {file.filename} (type={type})")
    try:
        contents = await file.read()
        
        transactions = []
        if type == "pdf":
            # PDF Processing
            logger.info("Extracting text from PDF...")
            text = extract_text_from_pdf(contents)
            if not text:
                logger.warning("PDF extraction returned empty text")
                raise HTTPException(status_code=400, detail="Could not extract text from PDF")
            transactions = ollama_extract_transactions(text)
        elif type == "csv":
            # CSV Processing
            logger.info("Parsing CSV...")
            transactions = parse_csv_to_transactions(contents)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {type}")
            
        if not transactions:
            logger.warning("No transactions found after parsing")
            raise HTTPException(status_code=400, detail="No transactions found in file")
            
        # DataFrame Processing (Reuse existing logic)
        temp_df = pd.DataFrame(transactions, columns=["Date", "Description", "Amount", "Type", "Balance"])
        if "Date" in temp_df.columns:
            temp_df["Date"] = pd.to_datetime(temp_df["Date"], errors="coerce").dt.date
            
        temp_df["Merchant"] = temp_df["Description"].apply(normalize_merchant)
        temp_df = categorize_transactions(temp_df, use_embeddings=True)
        
        # Insert to DB
        records = temp_df.to_dict('records')
        inserted, skipped = insert_transactions(records, source_file=file.filename)
        
        logger.info(f"Import complete: {inserted} inserted, {skipped} skipped")
        
        # Clean for response
        cleaned_records = [{k: (v if pd.notnull(v) else None) for k, v in r.items()} for r in records]
        
        return {
            "status": "success", 
            "inserted": inserted, 
            "skipped": skipped,
            "transactions": cleaned_records[:5] # Return preview
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/categorize", response_model=GenericResponse)
def update_category(request: CategorizeRequest):
    """Update a category override manually."""
    logger.info(f"Manual category override: {request.description} -> {request.category}")
    try:
        overrides = get_category_overrides()
        overrides[request.description] = request.category
        save_overrides(overrides)
        return {"status": "success", "message": f"Updated category for '{request.description}' to '{request.category}'"}
    except Exception as e:
        logger.error(f"Category update failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
def chat_with_analyst(request: ChatRequest):
    """Stream a chat response from the AI Financial Analyst."""
    logger.info(f"Chat request: {request.message}")
    
    return StreamingResponse(
        stream_chat_response(request.message), 
        media_type="text/plain"
    )

@router.get("/subscriptions", response_model=SubscriptionResponse)
def get_subscriptions():
    from backend.subscription_service import detect_subscriptions
    subs = detect_subscriptions()
    total_monthly = sum(item["amount"] for item in subs)
    return {"total_monthly": total_monthly, "items": subs}

# --- Goals Endpoints ---

@router.get("/goals", response_model=List[GoalItem])
def get_user_goals():
    from financial_tracker.database import get_goals
    return get_goals()

@router.post("/goals", response_model=Dict[str, int])
def create_goal(goal: GoalCreate):
    from financial_tracker.database import add_goal
    goal_id = add_goal(goal.name, goal.target_amount, goal.target_date, goal.icon)
    return {"id": goal_id}

@router.post("/goals/{goal_id}/contribute")
def contribute_to_goal(goal_id: int, contribution: GoalContribution):
    from financial_tracker.database import update_goal_progress
    update_goal_progress(goal_id, contribution.amount)
    return {"status": "success", "message": f"Added ${contribution.amount} to goal"}

@router.delete("/goals/{goal_id}")
def remove_goal(goal_id: int):
    from financial_tracker.database import delete_goal
    delete_goal(goal_id)
    return {"status": "success", "message": "Goal deleted"}

# --- Portfolio Endpoints ---

@router.get("/portfolio", response_model=PortfolioResponse)
def get_portfolio():
    from financial_tracker.database import get_assets
    assets = get_assets()
    
    total_assets = sum(a['value'] for a in assets if a['type'] != 'Liability')
    total_liabilities = sum(a['value'] for a in assets if a['type'] == 'Liability')
    net_worth = total_assets - total_liabilities
    
    return {
        "net_worth": net_worth,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "assets": assets
    }

@router.post("/portfolio", response_model=Dict[str, int])
def create_asset(asset: AssetCreate):
    from financial_tracker.database import add_asset
    asset_id = add_asset(asset.name, asset.type, asset.value, asset.quantity)
    return {"id": asset_id}

@router.delete("/portfolio/{asset_id}")
def remove_asset(asset_id: int):
    from financial_tracker.database import delete_asset
    delete_asset(asset_id)
    return {"status": "success", "message": "Asset deleted"}
