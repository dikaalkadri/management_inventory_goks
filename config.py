"""
Centralized configuration for Goks! Stock-In Manager & eResto Analysis.
"""
import os

# ─── GENERAL ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')
MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB

# ─── eRESTO COLUMN MAPPING ──────────────────────────────────────────────────
# Column indices (0-based) in the eResto order report export
ERESTO_COL_ORDER_DATE = 0     # Column A
ERESTO_COL_PRODUCT = 15       # Column P
ERESTO_COL_RAW_QTY = 21       # Column V (Quantity in raw eResto Excel)
ERESTO_COL_CLEANED_QTY = 16   # Column Q (Target position in cleaned dataframe)

# Columns to hide: B through O (1-based indices 2–15 for openpyxl)
ERESTO_HIDE_COLS_START = 2    # Column B (1-based)
ERESTO_HIDE_COLS_END = 15     # Column O (1-based)

# Summary area placement (1-based, openpyxl convention)
ERESTO_SUMMARY_PRODUCT_COL = 19   # Column S
ERESTO_DATE_START_COL = 20        # Column T

# ─── MASTER PRODUCT FILE ────────────────────────────────────────────────────
MASTER_PRODUCTS_FILE = os.path.join(BASE_DIR, 'data', 'master_products.json')

# ─── EXCEL STYLING COLORS ───────────────────────────────────────────────────
COLOR_HEADER_BG = "5A189A"        # Medium purple (#5a189a)
COLOR_HEADER_FONT = "FFFFFF"      # White
COLOR_DATE_HEADER_BG = "7B2CBF"   # Main purple (#7b2cbf)
COLOR_DATE_HEADER_FONT = "FFFFFF" # White
COLOR_PRODUCT_BG = "E0AAFF"       # Light purple/lavender (#e0aaff)
COLOR_ZEBRA_EVEN = "F7F0FC"       # Very light lavender/white zebra
COLOR_ZEBRA_ODD = "FFFFFF"        # White
COLOR_BORDER = "D6C1EB"           # Soft lavender border (#d6c1eb)

# Ensure required directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
