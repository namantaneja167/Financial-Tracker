"""
Export transactions to various formats.

Supports CSV and Excel exports with customizable date ranges and filters.
"""

import io
from datetime import datetime
from typing import Optional
import pandas as pd


def export_transactions_to_csv(
    df: pd.DataFrame,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    categories: Optional[list[str]] = None
) -> bytes:
    """
    Export transactions to CSV format.
    
    Args:
        df: DataFrame with transactions
        start_date: Optional start date filter
        end_date: Optional end date filter
        categories: Optional list of categories to include
        
    Returns:
        CSV content as bytes
    """
    filtered_df = _filter_transactions(df, start_date, end_date, categories)
    
    # Convert to CSV
    csv_buffer = io.StringIO()
    filtered_df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue().encode('utf-8')


def export_transactions_to_excel(
    df: pd.DataFrame,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    categories: Optional[list[str]] = None
) -> bytes:
    """
    Export transactions to Excel format with formatting.
    
    Args:
        df: DataFrame with transactions
        start_date: Optional start date filter
        end_date: Optional end date filter
        categories: Optional list of categories to include
        
    Returns:
        Excel content as bytes
    """
    filtered_df = _filter_transactions(df, start_date, end_date, categories)
    
    # Create Excel file in memory
    excel_buffer = io.BytesIO()
    
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        # Write main transactions sheet
        filtered_df.to_excel(writer, sheet_name='Transactions', index=False)
        
        # Add summary sheet if we have data
        if not filtered_df.empty and 'Category' in filtered_df.columns and 'Amount' in filtered_df.columns:
            summary = _create_summary(filtered_df)
            summary.to_excel(writer, sheet_name='Summary', index=True)
    
    excel_buffer.seek(0)
    return excel_buffer.getvalue()


def _filter_transactions(
    df: pd.DataFrame,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    categories: Optional[list[str]]
) -> pd.DataFrame:
    """Apply filters to transaction DataFrame."""
    if df.empty:
        return df
    
    result = df.copy()
    
    # Date filtering
    if 'Date' in result.columns:
        result['Date'] = pd.to_datetime(result['Date'], errors='coerce')
        
        if start_date:
            result = result[result['Date'] >= start_date]
        
        if end_date:
            result = result[result['Date'] <= end_date]
    
    # Category filtering
    if categories and 'Category' in result.columns:
        result = result[result['Category'].isin(categories)]
    
    return result


def _create_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create summary statistics for exported data."""
    summary_data = []
    
    # Total transactions
    summary_data.append(('Total Transactions', len(df)))
    
    # Date range
    if 'Date' in df.columns:
        dates = pd.to_datetime(df['Date'], errors='coerce').dropna()
        if not dates.empty:
            summary_data.append(('Date Range', f"{dates.min().date()} to {dates.max().date()}"))
    
    # Amount statistics
    if 'Amount' in df.columns:
        amounts = pd.to_numeric(df['Amount'], errors='coerce')
        summary_data.append(('Total Amount', amounts.sum()))
        summary_data.append(('Average Amount', amounts.mean()))
    
    # Type breakdown
    if 'Type' in df.columns:
        type_counts = df['Type'].value_counts()
        for tx_type, count in type_counts.items():
            summary_data.append((f'{tx_type} Count', count))
    
    # Category breakdown
    if 'Category' in df.columns:
        summary_data.append(('', ''))  # Blank row
        summary_data.append(('Category Breakdown', ''))
        
        category_amounts = df.groupby('Category')['Amount'].apply(
            lambda x: pd.to_numeric(x, errors='coerce').sum()
        ).sort_values(ascending=False)
        
        for category, amount in category_amounts.items():
            summary_data.append((f'  {category}', amount))
    
    return pd.DataFrame(summary_data, columns=['Metric', 'Value'])


def get_export_filename(format_type: str, prefix: str = "transactions") -> str:
    """
    Generate timestamped filename for export.
    
    Args:
        format_type: 'csv' or 'excel'
        prefix: Filename prefix
        
    Returns:
        Filename with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extension = 'xlsx' if format_type == 'excel' else 'csv'
    return f"{prefix}_{timestamp}.{extension}"
