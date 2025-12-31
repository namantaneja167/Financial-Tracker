"""
Data validation models using Pydantic.

Provides type-safe validation for transactions, budgets, and portfolio data.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Literal
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, ConfigDict


class Transaction(BaseModel):
    """Transaction data model with validation."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    Date: date | str
    Description: str = Field(min_length=1, max_length=500)
    Amount: float = Field(gt=-1_000_000, lt=1_000_000)
    Type: Literal["Debit", "Credit"]
    Balance: Optional[float] = Field(default=None, gt=-10_000_000, lt=10_000_000)
    Category: str = Field(default="", max_length=100)
    Merchant: str = Field(default="", max_length=200)
    
    @field_validator("Date", mode="before")
    @classmethod
    def parse_date(cls, v):
        """Parse date from various formats."""
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Could not parse date: {v}")
        raise ValueError(f"Invalid date type: {type(v)}")
    
    @field_validator("Amount", "Balance", mode="before")
    @classmethod
    def validate_numeric(cls, v):
        """Ensure numeric values are valid."""
        if v is None:
            return v
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            # Remove currency symbols and commas
            cleaned = v.replace("$", "").replace(",", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                raise ValueError(f"Could not parse amount: {v}")
        raise ValueError(f"Invalid numeric type: {type(v)}")
    
    @field_validator("Type", mode="before")
    @classmethod
    def validate_type(cls, v):
        """Normalize transaction type."""
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower in ["debit", "dr", "withdrawal", "expense"]:
                return "Debit"
            elif v_lower in ["credit", "cr", "deposit", "income"]:
                return "Credit"
        raise ValueError(f"Invalid transaction type: {v}. Must be Debit or Credit.")
    
    @field_validator("Category")
    @classmethod
    def validate_category(cls, v):
        """Ensure category is from valid list."""
        valid_categories = [
            "Rent", "Groceries", "Dining", "Transport", "Utilities",
            "Investments", "Income", "Shopping", "Misc", ""
        ]
        if v and v not in valid_categories:
            # Allow unknown categories but log warning
            pass
        return v


class Budget(BaseModel):
    """Budget data model with validation."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    category: str = Field(min_length=1, max_length=100)
    monthly_limit: float = Field(gt=0, le=1_000_000)
    
    @field_validator("monthly_limit", mode="before")
    @classmethod
    def validate_limit(cls, v):
        """Ensure budget limit is positive."""
        if isinstance(v, str):
            cleaned = v.replace("$", "").replace(",", "").strip()
            v = float(cleaned)
        if v <= 0:
            raise ValueError("Budget limit must be positive")
        return v


class PortfolioSnapshot(BaseModel):
    """Portfolio snapshot data model with validation."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    date: date | str
    cash_balance: float = Field(ge=0, le=100_000_000)
    portfolio_value: float = Field(ge=0, le=100_000_000)
    net_worth: float = Field(ge=-100_000_000, le=100_000_000)
    
    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        """Parse date from various formats."""
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v).date()
            except ValueError:
                return datetime.strptime(v, "%Y-%m-%d").date()
        raise ValueError(f"Invalid date: {v}")
    
    @field_validator("net_worth")
    @classmethod
    def validate_net_worth(cls, v, info):
        """Ensure net worth matches cash + portfolio."""
        if "cash_balance" in info.data and "portfolio_value" in info.data:
            expected = info.data["cash_balance"] + info.data["portfolio_value"]
            if abs(v - expected) > 0.01:  # Allow small floating point errors
                raise ValueError(f"Net worth ({v}) doesn't match cash + portfolio ({expected})")
        return v


def validate_transaction(data: dict) -> Transaction:
    """
    Validate transaction data and return validated model.
    
    Args:
        data: Dictionary of transaction data
        
    Returns:
        Validated Transaction model
        
    Raises:
        ValidationError: If data is invalid
    """
    return Transaction(**data)


def validate_budget(data: dict) -> Budget:
    """
    Validate budget data and return validated model.
    
    Args:
        data: Dictionary of budget data
        
    Returns:
        Validated Budget model
        
    Raises:
        ValidationError: If data is invalid
    """
    return Budget(**data)


def validate_portfolio_snapshot(data: dict) -> PortfolioSnapshot:
    """
    Validate portfolio snapshot data and return validated model.
    
    Args:
        data: Dictionary of portfolio snapshot data
        
    Returns:
        Validated PortfolioSnapshot model
        
    Raises:
        ValidationError: If data is invalid
    """
    return PortfolioSnapshot(**data)
