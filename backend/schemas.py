from pydantic import BaseModel, Field
from typing import List, Optional, Union

class Transaction(BaseModel):
    Date: Optional[str] = None
    Description: str
    Amount: float
    Type: str
    Balance: Optional[float] = None
    Category: Optional[str] = Field(default="Uncategorized")
    Merchant: Optional[str] = None
    SourceFile: Optional[str] = None
    ImportedAt: Optional[str] = None

class MonthlyTrendItem(BaseModel):
    Month: str
    Income: float
    Expense: float

class StatsResponse(BaseModel):
    total_income: float
    total_spend: float
    savings_rate: float
    monthly_trend: List[MonthlyTrendItem]

class UploadResponse(BaseModel):
    status: str
    inserted: int
    skipped: int
    transactions: List[Transaction]

class CategorizeRequest(BaseModel):
    description: str
    category: str

class ChatRequest(BaseModel):
    message: str

class SubscriptionItem(BaseModel):
    merchant: str
    amount: float
    frequency: str
    yearly_cost: float
    last_paid: str

class SubscriptionResponse(BaseModel):
    total_monthly: float
    items: List[SubscriptionItem]

class GoalItem(BaseModel):
    id: int
    name: str
    target_amount: float
    current_amount: float
    target_date: Optional[str] = None
    icon: Optional[str] = None
    is_completed: bool

class GoalCreate(BaseModel):
    name: str
    target_amount: float
    target_date: Optional[str] = None
    icon: Optional[str] = None

class GoalContribution(BaseModel):
    amount: float

class AssetItem(BaseModel):
    id: int
    name: str
    type: str
    quantity: float
    value: float
    last_updated: Optional[str] = None

class AssetCreate(BaseModel):
    name: str
    type: str
    value: float
    quantity: float = 1.0

class PortfolioResponse(BaseModel):
    net_worth: float
    total_assets: float
    total_liabilities: float
    assets: List[AssetItem]

class GenericResponse(BaseModel):
    status: str
    message: str
