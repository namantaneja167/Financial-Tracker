"""
Financial Tracker - Main application entry point.

This module handles file uploads, transaction import, and routes to different pages.
"""
import pandas as pd
import streamlit as st

from financial_tracker.logging_config import setup_logging
from financial_tracker.categorizer import categorize_transactions
from financial_tracker.csv_importer import parse_csv_to_transactions
from financial_tracker.ollama_client import ollama_extract_transactions
from financial_tracker.pdf_parser import extract_text_from_pdf
from financial_tracker.database import insert_transactions, get_all_transactions
from financial_tracker.merchant_normalizer import normalize_merchant
from financial_tracker.config import get_max_file_size_mb

from pages.dashboard import render_dashboard
from pages.investments import render_investments
from pages.budgets import render_budgets
from pages.recurring import render_recurring
from pages.networth import render_networth
from pages.rules import render_rules
from pages.merchants import render_merchants
from pages.settings import render_settings


# Initialize logging
setup_logging()

# Page configuration with custom styling
st.set_page_config(
    page_title="Financial Tracker Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Financial Tracker - Personal Finance Management System"
    }
)

# Custom CSS for clean, readable design
st.markdown("""
<style>
    /* Force light theme on everything */
    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    
    /* Override Streamlit's dark theme */
    .st-emotion-cache-13k62yr {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    
    /* Sidebar light theme */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background-color: #f0f2f6 !important;
    }
    
    /* All text must be dark and readable */
    *, p, span, div, label, h1, h2, h3, h4, h5, h6, li, td, th {
        color: #1a1a1a !important;
    }
    
    /* Headers with blue accent */
    h1 {
        color: #1f77b4 !important;
        font-weight: 700 !important;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }
    
    h2 {
        color: #1f77b4 !important;
        font-weight: 600 !important;
        margin-top: 1.5rem;
    }
    
    h3 {
        color: #2c3e50 !important;
        font-weight: 600 !important;
    }
    
    /* Metric cards with clear backgrounds */
    [data-testid="stMetric"] {
        background-color: #f8f9fa !important;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #2c3e50 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #495057 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }
    
    /* Input fields - white with dark text */
    input, textarea, select, [data-baseweb="input"] {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #ced4da !important;
    }
    
    /* Buttons - clear and clickable */
    .stButton > button {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 2px solid #dee2e6 !important;
        border-radius: 6px;
        font-weight: 500;
        padding: 0.5rem 1.5rem;
    }
    
    .stButton > button:hover {
        background-color: #e9ecef !important;
        border-color: #1f77b4 !important;
        transform: translateY(-1px);
    }
    
    .stButton > button[kind="primary"] {
        background-color: #1f77b4 !important;
        color: #ffffff !important;
        border: none !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #1560a8 !important;
    }
    
    /* Tabs - light with clear selection */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #f8f9fa !important;
        padding: 0.5rem;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff !important;
        color: #495057 !important;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e7f3ff !important;
        color: #1a1a1a !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4 !important;
        color: #ffffff !important;
        border-color: #1f77b4 !important;
    }
    
    /* Data tables and dataframes */
    [data-testid="stDataFrame"], .stDataFrame {
        background-color: #ffffff !important;
        border: 2px solid #dee2e6 !important;
        border-radius: 8px;
    }
    
    /* Table headers */
    thead tr, thead th {
        background-color: #f8f9fa !important;
        color: #1a1a1a !important;
        font-weight: 600 !important;
    }
    
    /* Table cells */
    tbody tr, tbody td {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    
    tbody tr:hover {
        background-color: #f8f9fa !important;
    }
    
    /* Success/Info/Warning messages */
    .stSuccess {
        background-color: #d4edda !important;
        color: #155724 !important;
        border: 2px solid #c3e6cb !important;
        border-radius: 6px;
        padding: 1rem;
    }
    
    .stInfo {
        background-color: #d1ecf1 !important;
        color: #0c5460 !important;
        border: 2px solid #bee5eb !important;
        border-radius: 6px;
        padding: 1rem;
    }
    
    .stWarning {
        background-color: #fff3cd !important;
        color: #856404 !important;
        border: 2px solid #ffeeba !important;
        border-radius: 6px;
        padding: 1rem;
    }
    
    .stError {
        background-color: #f8d7da !important;
        color: #721c24 !important;
        border: 2px solid #f5c6cb !important;
        border-radius: 6px;
        padding: 1rem;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #f8f9fa !important;
        color: #1a1a1a !important;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        font-weight: 600;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background-color: #f8f9fa !important;
        border: 2px dashed #adb5bd !important;
        border-radius: 8px;
    }
    
    /* Selectbox and other inputs */
    [data-baseweb="select"], [data-baseweb="popover"] {
        background-color: #ffffff !important;
    }
    
    /* Radio buttons and checkboxes */
    [data-testid="stRadio"] label, [data-testid="stCheckbox"] label {
        color: #1a1a1a !important;
    }
    
    /* Sidebar navigation links */
    [data-testid="stSidebarNav"] a {
        color: #1a1a1a !important;
    }
    
    [data-testid="stSidebarNav"] a:hover {
        background-color: #e9ecef !important;
    }
    
    /* Number input */
    [data-testid="stNumberInput"] input {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    
    /* Code blocks */
    code {
        background-color: #f8f9fa !important;
        color: #e83e8c !important;
        padding: 0.2rem 0.4rem;
        border-radius: 3px;
    }
    
    pre {
        background-color: #f8f9fa !important;
        color: #1a1a1a !important;
        padding: 1rem;
        border-radius: 6px;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

st.title("💰 Financial Tracker Dashboard")

# Sidebar inputs with better organization
st.sidebar.title("📊 Quick Actions")
portfolio_value = st.sidebar.number_input(
    "💼 Current Portfolio Value",
    min_value=0.0,
    value=0.0,
    step=1000.0,
    format="%.2f",
)

# File upload section
st.sidebar.markdown("---")
st.sidebar.subheader("📂 Import Transactions")

MAX_FILE_SIZE_MB = get_max_file_size_mb()
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
PDF_MAGIC_BYTES = b'%PDF'

import_type = st.sidebar.radio("Import Type", ["PDF (via Ollama)", "CSV"], horizontal=False)

uploaded = None
if import_type == "PDF (via Ollama)":
    uploaded = st.sidebar.file_uploader(
        "Upload Bank PDF",
        type=["pdf"],
        help=f"Max size: {MAX_FILE_SIZE_MB} MB"
    )
else:
    uploaded = st.sidebar.file_uploader(
        "Upload Bank CSV",
        type=["csv"],
        help=f"Max size: {MAX_FILE_SIZE_MB} MB"
    )

if uploaded is not None:
    # Validate file size
    if uploaded.size > MAX_FILE_SIZE_BYTES:
        st.error(f"File size exceeds {MAX_FILE_SIZE_MB}MB limit. Please upload a smaller file.")
        st.stop()
    
    source_filename = uploaded.name
    
    if import_type == "PDF (via Ollama)":
        pdf_bytes = uploaded.getvalue()
        
        # Validate PDF signature
        if not pdf_bytes.startswith(PDF_MAGIC_BYTES):
            st.error("Invalid PDF file. The file does not have a valid PDF signature.")
            st.stop()
        
        with st.spinner("Extracting text from PDF..."):
            try:
                raw_text = extract_text_from_pdf(pdf_bytes)
            except Exception as e:
                st.error(f"Failed to extract text from PDF: {e}")
                st.stop()

        if not raw_text:
            st.error("No text could be extracted from this PDF.")
            st.stop()

        with st.spinner("Sending text to Ollama for transaction extraction..."):
            try:
                transactions = ollama_extract_transactions(raw_text)
            except Exception as e:
                st.error(f"Ollama extraction failed: {e}")
                st.stop()
    else:
        csv_bytes = uploaded.getvalue()
        
        # Validate CSV content
        try:
            csv_text = csv_bytes.decode('utf-8')
            if ',' not in csv_text and '\t' not in csv_text:
                st.error("Invalid CSV file. The file does not appear to contain valid CSV data.")
                st.stop()
        except UnicodeDecodeError:
            st.error("Invalid CSV file. The file is not a valid text file.")
            st.stop()
        
        with st.spinner("Parsing CSV..."):
            try:
                transactions = parse_csv_to_transactions(csv_bytes)
            except Exception as e:
                st.error(f"Failed to parse CSV: {e}")
                st.stop()
                
        if not transactions:
            st.error("No transactions could be parsed from this CSV. Check column names.")
            st.stop()

    # Process transactions
    temp_df = pd.DataFrame(transactions, columns=["Date", "Description", "Amount", "Type", "Balance"])
    if "Date" in temp_df.columns:
        temp_df["Date"] = pd.to_datetime(temp_df["Date"], errors="coerce").dt.date
    
    # Add normalized merchant names
    temp_df["Merchant"] = temp_df["Description"].apply(normalize_merchant)
    
    # Categorize
    temp_df = categorize_transactions(temp_df, use_embeddings=True)
    
    # Insert into database
    transactions_to_insert = temp_df.to_dict('records')
    inserted, skipped = insert_transactions(transactions_to_insert, source_file=source_filename)
    
    if inserted > 0:
        st.success(f"✅ Imported {inserted} new transaction(s) from {source_filename}")
    if skipped > 0:
        st.info(f"ℹ️ Skipped {skipped} duplicate transaction(s)")

# Load all transactions
df = get_all_transactions()

if df.empty:
    st.info("No transactions in database. Upload a PDF or CSV to get started.")
    st.stop()

# Create tabs and route to pages
tab_dashboard, tab_investments, tab_budgets, tab_recurring, tab_networth, tab_rules, tab_merchants, tab_settings = st.tabs([
    "📊 Dashboard", "💼 Investments", "💰 Budgets", "🔄 Recurring", "📈 Net Worth", "📋 Rules", "🏪 Merchants", "⚙️ Settings"
])

with tab_dashboard:
    render_dashboard(df)

with tab_investments:
    render_investments(df, portfolio_value)

with tab_budgets:
    render_budgets()

with tab_recurring:
    render_recurring(df)

with tab_networth:
    render_networth()

with tab_rules:
    render_rules()

with tab_merchants:
    render_merchants()

with tab_settings:
    render_settings()
