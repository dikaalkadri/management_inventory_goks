"""
Processor for eResto Mass Analysis.

Takes the combined cleaned DataFrame, splits it per outlet,
generates one Excel file per outlet (identical to eresto/excel_generator.py output),
and zips all files into a single downloadable archive.
"""
import io
import json
import os
import zipfile
from datetime import date

import config
from modules.eresto.excel_generator import generate_excel
from modules.eresto.master_product import load_master_products
from services.file_handler import generate_output_filename


BULAN_NAMES = [
    '', 'januari', 'februari', 'maret', 'april', 'mei', 'juni',
    'juli', 'agustus', 'september', 'oktober', 'november', 'desember'
]


def load_outlets_inventory() -> list:
    """Load the numbered outlet list from inventory.json."""
    try:
        inv_path = os.path.join(config.BASE_DIR, 'data', 'inventory.json')
        with open(inv_path, 'r', encoding='utf-8') as f:
            inv = json.load(f)
        return inv.get('outlets', [])
    except Exception as e:
        print(f"[WARN] Gagal membaca inventory.json: {e}")
        return []


def match_outlet_to_numbered(raw_name: str, outlets_list: list) -> str:
    """Match a raw outlet name (no number) to the numbered version from inventory.

    Example: 'Pauh Kambar' -> '29. Pauh Kambar'

    Falls back to raw_name if no match found.
    """
    raw_lower = raw_name.strip().lower()
    for o in outlets_list:
        # Strip number prefix for comparison: "29. Pauh Kambar" -> "pauh kambar"
        parts = o.split('.', 1)
        name_part = parts[1].strip().lower() if len(parts) > 1 else o.lower()
        if raw_lower == name_part or raw_lower in name_part or name_part in raw_lower:
            return o
    return raw_name.strip()


def process_mass_to_zip(
    df,
    date_col: str,
    outlet_col: str,
    product_col: str,
    qty_col: str,
    zip_output_path: str,
) -> dict:
    """Split DataFrame by outlet, generate Excel per outlet, zip all together.

    Args:
        df            : Full cleaned DataFrame (all outlets).
        date_col      : Name of Order Date column.
        outlet_col    : Name of Outlet column.
        product_col   : Name of Product column.
        qty_col       : Name of Quantity column.
        zip_output_path: Absolute path to write the output ZIP file.

    Returns:
        dict with keys:
        - 'zip_path'        : Path to the generated ZIP file.
        - 'outlets_processed': List of outlet names that were processed.
        - 'outlets_skipped' : List of outlet names skipped (no valid data).
        - 'file_count'      : Number of xlsx files in the ZIP.
    """
    master_products = load_master_products()
    if not master_products:
        raise ValueError(
            "Master product list kosong. Isi terlebih dahulu di menu eResto Analysis → Master Product."
        )

    outlets_list = load_outlets_inventory()
    unique_outlets = sorted(df[outlet_col].astype(str).unique().tolist())

    outlets_processed = []
    outlets_skipped = []

    # We'll build the ZIP in memory, writing xlsx files directly into it
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for raw_outlet in unique_outlets:
            df_outlet = df[df[outlet_col].astype(str) == raw_outlet].copy()

            if df_outlet.empty:
                outlets_skipped.append(raw_outlet)
                continue

            # Match to numbered outlet name
            outlet_named = match_outlet_to_numbered(raw_outlet, outlets_list)

            # Determine date range FROM THIS OUTLET'S DATA
            valid_dates = df_outlet[date_col].dropna()
            if valid_dates.empty:
                outlets_skipped.append(raw_outlet)
                continue

            min_dt = valid_dates.min()
            max_dt = valid_dates.max()
            min_day = int(min_dt.day)
            max_day = int(max_dt.day)
            month = int(min_dt.month)
            year = int(min_dt.year)

            tglperiode = f"{min_day:02d}-{max_day:02d}"

            # Build output filename (same format as eresto single-outlet)
            xlsx_filename = generate_output_filename(
                original_name='mass_upload',
                month=month,
                year=year,
                outlet=outlet_named,
                tglperiode=tglperiode,
            )

            # Generate Excel to an in-memory bytes buffer
            xlsx_buffer = io.BytesIO()
            try:
                generate_excel(
                    df=df_outlet,
                    date_col=date_col,
                    product_col=product_col,
                    qty_col=qty_col,
                    master_products=master_products,
                    month=month,
                    year=year,
                    output_path=xlsx_buffer,
                )
                xlsx_buffer.seek(0)
                zf.writestr(xlsx_filename, xlsx_buffer.read())
                outlets_processed.append(outlet_named)
            except Exception as e:
                print(f"[WARN] Gagal generate Excel untuk outlet '{raw_outlet}': {e}")
                outlets_skipped.append(raw_outlet)

    # Write ZIP to disk
    zip_buffer.seek(0)
    os.makedirs(os.path.dirname(zip_output_path), exist_ok=True)
    with open(zip_output_path, 'wb') as f:
        f.write(zip_buffer.read())

    return {
        'zip_path': zip_output_path,
        'outlets_processed': outlets_processed,
        'outlets_skipped': outlets_skipped,
        'file_count': len(outlets_processed),
    }
