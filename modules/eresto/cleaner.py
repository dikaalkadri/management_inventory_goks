"""
Data Cleaning Pipeline for eResto Order Report.

Reads the raw eResto Excel export and produces a cleaned DataFrame
with only the essential columns: Order Date, Product, Quantity.

Key operations:
- Extract columns A (Order Date), P (Product), Q (Quantity)
- Strip time from Order Date (keep date only)
- Handle multiple date formats
- Convert Quantity to numeric
- Remove null/empty rows
"""
import pandas as pd
import numpy as np
from datetime import datetime

import config


def load_raw_data(filepath: str) -> pd.DataFrame:
    """Load the raw eResto export Excel file.

    Reads the entire file preserving all columns.
    Uses xlrd engine for .xls files and openpyxl for other files.

    Args:
        filepath: Path to the uploaded eResto Excel file.

    Returns:
        Raw DataFrame with all columns.
    """
    if filepath.lower().endswith('.xls'):
        df = pd.read_excel(filepath, engine='xlrd', header=0)
    else:
        df = pd.read_excel(filepath, engine='openpyxl', header=0)
    return df


def extract_key_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, str, str, str]:
    """Identify key columns (Order Date, Product, Quantity) by name,
    and reorder the DataFrame so that:
    - Order Date is in Column A (index 0)
    - Product is in Column P (index 15)
    - Quantity is in Column Q (index 16)
    All other columns are preserved in Columns B through O and Column R onwards.
    """
    col_names = df.columns.tolist()

    # Find columns by name (case-insensitive matching)
    order_date_col = None
    product_col = None
    qty_col = None

    for col in col_names:
        col_lower = str(col).strip().lower()
        if col_lower in ['order date', 'tanggal', 'tanggal order']:
            order_date_col = col
        elif col_lower in ['product', 'produk', 'nama produk', 'nama barang']:
            product_col = col
        elif col_lower in ['quantity', 'qty']:
            qty_col = col

    # Fallback to positional indices if not found by name
    if not order_date_col:
        order_date_col = col_names[config.ERESTO_COL_ORDER_DATE]
    if not product_col:
        idx = min(config.ERESTO_COL_PRODUCT, len(col_names) - 1)
        product_col = col_names[idx]
    if not qty_col:
        idx = min(config.ERESTO_COL_RAW_QTY, len(col_names) - 1)
        qty_col = col_names[idx]

    # Rearrange the columns to put Order Date at index 0, Product at index 15, and Quantity at index 16
    other_cols = [c for c in col_names if c not in (order_date_col, product_col, qty_col)]

    # Pad other_cols if there are fewer than 14 columns
    while len(other_cols) < 14:
        other_cols.append(f"_empty_col_{len(other_cols)}")

    new_col_order = [order_date_col] + other_cols[:14] + [product_col, qty_col] + other_cols[14:]

    # Create missing columns if we padded empty ones
    df_reordered = df.copy()
    for col in new_col_order:
        if col not in df_reordered.columns:
            df_reordered[col] = ""

    df_reordered = df_reordered[new_col_order]

    return df_reordered, order_date_col, product_col, qty_col


def parse_order_dates(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Parse Order Date column, stripping time to keep date only.

    Handles multiple date formats:
    - DD/MM/YYYY HH:MM:SS
    - MM/DD/YYYY HH:MM:SS
    - YYYY-MM-DD HH:MM:SS
    - Already datetime objects

    Args:
        df: DataFrame with the date column.
        date_col: Name of the date column.

    Returns:
        DataFrame with cleaned date column (date only, no time).
    """
    df = df.copy()

    # If already datetime, just strip time
    if pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = df[date_col].dt.normalize()
        return df

    # Try parsing with dayfirst=True (DD/MM/YYYY format — common in Indonesia)
    try:
        df[date_col] = pd.to_datetime(
            df[date_col],
            dayfirst=True,
            format='mixed',
            errors='coerce'
        )
    except Exception:
        # Fallback: try without dayfirst
        df[date_col] = pd.to_datetime(
            df[date_col],
            format='mixed',
            errors='coerce'
        )

    # Strip time component — normalize to midnight
    df[date_col] = df[date_col].dt.normalize()

    return df


def clean_qty(df: pd.DataFrame, qty_col: str) -> pd.DataFrame:
    """Convert Quantity column to numeric, handling errors gracefully.

    Args:
        df: DataFrame with the quantity column.
        qty_col: Name of the quantity column.

    Returns:
        DataFrame with numeric quantity column.
    """
    df = df.copy()
    df[qty_col] = pd.to_numeric(df[qty_col], errors='coerce').fillna(0)
    return df


def remove_empty_rows(
    df: pd.DataFrame,
    product_col: str,
    qty_col: str
) -> pd.DataFrame:
    """Remove rows where Product is empty or Quantity is 0/null.

    Args:
        df: DataFrame to clean.
        product_col: Name of the product column.
        qty_col: Name of the quantity column.

    Returns:
        Cleaned DataFrame without empty rows.
    """
    df = df.copy()

    # Remove rows with empty/null product
    df = df.dropna(subset=[product_col])
    df = df[df[product_col].astype(str).str.strip() != '']

    # Remove rows with zero quantity
    df = df[df[qty_col] != 0]

    return df


def clean_data(filepath: str) -> dict:
    """Run the complete data cleaning pipeline on an eResto export file.

    Pipeline:
    1. Load raw Excel
    2. Extract key columns (Order Date, Product, Quantity)
    3. Parse dates (strip time)
    4. Clean quantity (numeric conversion)
    5. Remove empty/invalid rows
    6. Return cleaned data + metadata

    Args:
        filepath: Path to the uploaded eResto xlsx file.

    Returns:
        Dictionary containing:
        - 'df': Cleaned DataFrame (all original columns preserved)
        - 'date_col': Name of the Order Date column
        - 'product_col': Name of the Product column
        - 'qty_col': Name of the Quantity column
        - 'total_rows_raw': Total rows before cleaning
        - 'total_rows_clean': Total rows after cleaning
        - 'unique_products': List of unique products found
        - 'date_range': Tuple of (min_date, max_date)
        - 'all_columns': List of all column names (for reference)
    """
    # Step 1: Load
    df_raw = load_raw_data(filepath)
    total_rows_raw = len(df_raw)
    all_columns = df_raw.columns.tolist()

    # Step 2: Identify key columns
    df, date_col, product_col, qty_col = extract_key_columns(df_raw)

    # Step 3: Parse dates
    df = parse_order_dates(df, date_col)

    # Step 4: Clean quantities
    df = clean_qty(df, qty_col)

    # Step 5: Remove empty rows
    df = remove_empty_rows(df, product_col, qty_col)

    total_rows_clean = len(df)

    # Metadata
    unique_products = sorted(df[product_col].astype(str).unique().tolist())

    date_range = (None, None)
    valid_dates = df[date_col].dropna()
    if len(valid_dates) > 0:
        date_range = (
            valid_dates.min().strftime('%d/%m/%Y'),
            valid_dates.max().strftime('%d/%m/%Y')
        )

    return {
        'df': df,
        'date_col': date_col,
        'product_col': product_col,
        'qty_col': qty_col,
        'total_rows_raw': total_rows_raw,
        'total_rows_clean': total_rows_clean,
        'unique_products': unique_products,
        'date_range': date_range,
        'all_columns': all_columns,
    }
