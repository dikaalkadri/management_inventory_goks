import os
import re
import json
import zipfile
import tempfile
from io import BytesIO
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

import config

SCHEDULES_FILE = os.path.join(config.BASE_DIR, 'data', 'outlet_schedules.json')
INVENTORY_FILE = os.path.join(config.BASE_DIR, 'data', 'inventory.json')
MATERIALS_FILE = os.path.join(config.BASE_DIR, 'data', 'master_materials.json')

DAYS_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_ID = {
    "Monday": "Senin",
    "Tuesday": "Selasa",
    "Wednesday": "Rabu",
    "Thursday": "Kamis",
    "Friday": "Jumat",
    "Saturday": "Sabtu",
    "Sunday": "Minggu"
}


def load_schedules() -> Dict[str, Any]:
    """Muat konfigurasi jadwal pengiriman outlet dari disk."""
    if not os.path.exists(SCHEDULES_FILE):
        return {}
    try:
        with open(SCHEDULES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[PUSH-GUDANG] Gagal memuat jadwal: {e}")
        return {}


def save_schedules(schedules: Dict[str, Any]) -> bool:
    """Simpan konfigurasi jadwal pengiriman outlet."""
    try:
        with open(SCHEDULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(schedules, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[PUSH-GUDANG] Gagal menyimpan jadwal: {e}")
        return False


def load_outlets_list() -> List[str]:
    """Muat daftar outlet dari inventory.json."""
    if not os.path.exists(INVENTORY_FILE):
        return []
    try:
        with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
            inv = json.load(f)
            return inv.get('outlets', [])
    except Exception:
        return []


def calculate_delivery_gap(current_day_name: str, delivery_days: List[str]) -> int:
    """
    Hitung gap (jumlah hari) dari hari pengiriman ini sampai ke hari pengiriman BERIKUTNYA.
    Contoh:
      - Jika jadwal ['Tuesday', 'Friday'] dan hari ini Tuesday -> gap = 3 hari (Jumat).
      - Jika jadwal ['Monday'] dan hari ini Monday -> gap = 7 hari (Senin depan).
      - Jika jadwal Daily (Mon-Sat) dan hari ini Monday -> gap = 1 hari (Selasa).
        Hari Sabtu -> gap = 2 hari (Senin).
    """
    if not delivery_days:
        return 7  # default fallback 1 minggu

    curr_idx = DAYS_ORDER.index(current_day_name) if current_day_name in DAYS_ORDER else 0
    deliv_indices = sorted([DAYS_ORDER.index(d) for d in delivery_days if d in DAYS_ORDER])

    if not deliv_indices:
        return 7

    # Jika hari ini ada dalam jadwal, cari hari berikutnya setelah hari ini
    if curr_idx in deliv_indices:
        # Cari hari berikutnya dalam siklus
        for idx in deliv_indices:
            if idx > curr_idx:
                return idx - curr_idx
        # Jika tidak ada yang lebih besar, lompat ke minggu depan (elemen pertama)
        return (7 - curr_idx) + deliv_indices[0]
    else:
        # Jika hari ini BUKAN hari pengiriman, hitung gap dari pengiriman terdekat ke pengiriman sesudahnya
        # 1. Cari pengiriman terdekat berikutnya
        next_deliv_idx = None
        for idx in deliv_indices:
            if idx > curr_idx:
                next_deliv_idx = idx
                break
        if next_deliv_idx is None:
            next_deliv_idx = deliv_indices[0]

        # 2. Hitung gap dari next_deliv_idx ke pengiriman sesudahnya
        for idx in deliv_indices:
            if idx > next_deliv_idx:
                return idx - next_deliv_idx
        return (7 - next_deliv_idx) + deliv_indices[0]


def extract_outlet_code(filename: str, outlets_list: List[str]) -> Optional[str]:
    """Cari kode 2-digit outlet dari nama file kerugian."""
    name_lower = filename.lower()
    for outlet in outlets_list:
        parts = outlet.split('.', 1)
        if len(parts) == 2:
            code = parts[0].strip().zfill(2)
            name = parts[1].strip().lower()
            if name in name_lower or name.replace(' ', '_') in name_lower:
                return code

    # Fallback regex
    m = re.findall(r'(?<!\d)(\d{2})(?:\.[ \t]|_|\s)', filename)
    if m:
        return m[-1].zfill(2)
    return None


def analyze_push_recommendations(
    zip_bytes: bytes,
    target_date_str: str,
    lookback_days: int = 7,
    buffer_days: int = 1,
    include_all_outlets: bool = False
) -> Dict[str, Any]:
    """
    Analisis data kerugian dari ZIP dan hitung rekomendasi push barang per outlet.
    """
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_day_name = target_date.strftime("%A")
    target_day_id = DAYS_ID.get(target_day_name, target_day_name)
    target_day_num = target_date.day

    schedules = load_schedules()
    outlets_list = load_outlets_list()

    # Ekstrak file xlsx dari ZIP
    outlet_files = {}
    with zipfile.ZipFile(BytesIO(zip_bytes), 'r') as zf:
        for info in zf.infolist():
            fname = os.path.basename(info.filename)
            if not fname or info.is_dir() or not fname.lower().endswith(('.xlsx', '.xls')):
                continue
            code = extract_outlet_code(fname, outlets_list)
            if code:
                outlet_files[code] = {
                    "filename": fname,
                    "bytes": zf.read(info.filename)
                }

    results_outlets = []
    total_items_to_ship = 0
    kritis_outlets_count = 0
    waspada_outlets_count = 0
    aman_outlets_count = 0

    all_shipment_items_map = {}  # mat_name -> total_qty

    tmpdir = tempfile.mkdtemp(prefix="push_analysis_")

    try:
        for code, sched in schedules.items():
            outlet_name = sched.get('name', f"Outlet {code}")
            delivery_days = sched.get('delivery_days', [])
            dtype = sched.get('delivery_type', 'DAILY')
            location = sched.get('location', 'Dalam Kota')

            is_scheduled_today = (target_day_name in delivery_days)

            # Jika tidak ingin menyertakan outlet yang tidak terjadwal hari ini
            if not include_all_outlets and not is_scheduled_today:
                continue

            gap_days = calculate_delivery_gap(target_day_name, delivery_days)
            coverage_days = gap_days + buffer_days

            if code not in outlet_files:
                results_outlets.append({
                    "code": code,
                    "name": outlet_name,
                    "scheduled_today": is_scheduled_today,
                    "delivery_type": dtype,
                    "location": location,
                    "gap_days": gap_days,
                    "coverage_days": coverage_days,
                    "status": "DATA_TIDAK_ADA",
                    "status_label": "Tidak Ada Data di ZIP",
                    "items": [],
                    "summary": {
                        "total_items_needed": 0,
                        "kritis_count": 0,
                        "waspada_count": 0
                    }
                })
                continue

            file_info = outlet_files[code]
            tmp_path = os.path.join(tmpdir, f"temp_{code}_{file_info['filename']}")
            with open(tmp_path, 'wb') as f:
                f.write(file_info['bytes'])

            try:
                wb = openpyxl.load_workbook(tmp_path, read_only=True, data_only=True)
            except Exception as e:
                print(f"[PUSH-GUDANG] Gagal buka workbook {file_info['filename']}: {e}")
                continue

            # Cari sheet harian ("01", "02", ..., "31")
            daily_sheets = []
            for sname in wb.sheetnames:
                try:
                    s_int = int(sname.strip())
                    if 1 <= s_int <= 31:
                        daily_sheets.append((s_int, sname))
                except ValueError:
                    pass

            daily_sheets.sort(key=lambda x: x[0])

            if not daily_sheets:
                wb.close()
                continue

            # Pilih sheet sampai dengan target_day_num jika ada, atau sheet paling akhir
            sheets_up_to_target = [s for s in daily_sheets if s[0] <= target_day_num]
            if not sheets_up_to_target:
                sheets_up_to_target = daily_sheets

            latest_day_num, latest_sheet_name = sheets_up_to_target[-1]

            # Pilih sheet lookback untuk burn rate (misal 7 hari terakhir)
            lookback_sheets = [s[1] for s in sheets_up_to_target[-lookback_days:]]
            lookback_count = max(1, len(lookback_sheets))

            # 1. Ambil burn rate POS (Kolom J - 10) dari sheet-sheet lookback
            # Map: row_index -> total POS keluar
            pos_burn_totals = {}
            row_items_meta = {}  # row_idx -> (category, name)

            for s_name in lookback_sheets:
                ws = wb[s_name]
                for r_idx, row in enumerate(ws.iter_rows(min_row=2, max_row=110, min_col=1, max_col=10, values_only=True), start=2):
                    cat = row[0]
                    name = row[1]
                    if not name:
                        continue
                    clean_name = str(name).strip()
                    if r_idx not in row_items_meta:
                        row_items_meta[r_idx] = (str(cat).strip() if cat else "", clean_name)

                    pos_val = row[9] if len(row) >= 10 else 0
                    try:
                        pos_float = float(pos_val) if pos_val is not None else 0.0
                    except (ValueError, TypeError):
                        pos_float = 0.0

                    pos_burn_totals[r_idx] = pos_burn_totals.get(r_idx, 0.0) + max(0.0, pos_float)

            # 2. Ambil Stok Akhir (Kolom F - 6) dari sheet TERAKHIR
            ws_latest = wb[latest_sheet_name]
            stock_akhir_map = {}
            for r_idx, row in enumerate(ws_latest.iter_rows(min_row=2, max_row=110, min_col=1, max_col=6, values_only=True), start=2):
                if len(row) >= 6:
                    val_f = row[5]
                    try:
                        f_float = float(val_f) if val_f is not None else 0.0
                    except (ValueError, TypeError):
                        f_float = 0.0
                    stock_akhir_map[r_idx] = f_float

            wb.close()

            # 3. Hitung Rekomendasi Push per Barang
            outlet_items = []
            kritis_count = 0
            waspada_count = 0

            for r_idx, (cat, name) in sorted(row_items_meta.items()):
                total_pos = pos_burn_totals.get(r_idx, 0.0)
                avg_burn_daily = total_pos / lookback_count
                curr_stock = stock_akhir_map.get(r_idx, 0.0)

                target_stock = avg_burn_daily * coverage_days
                recommend_push = max(0.0, target_stock - curr_stock)

                # Days of stock left
                if avg_burn_daily > 0:
                    days_left = round(curr_stock / avg_burn_daily, 1)
                else:
                    days_left = 999.0

                # Tentukan Urgensi
                if (curr_stock <= 0 and avg_burn_daily > 0) or (days_left < 1.5 and avg_burn_daily > 0):
                    urgency = "KRITIS"
                    kritis_count += 1
                elif recommend_push > 0:
                    urgency = "WASPADA"
                    waspada_count += 1
                else:
                    urgency = "AMAN"

                # Bulatkan rekomendasi
                rec_push_rounded = round(recommend_push, 1)
                if rec_push_rounded.is_integer():
                    rec_push_rounded = int(rec_push_rounded)

                if rec_push_rounded > 0:
                    all_shipment_items_map[name] = all_shipment_items_map.get(name, 0.0) + rec_push_rounded

                outlet_items.append({
                    "row": r_idx,
                    "category": cat,
                    "name": name,
                    "curr_stock": round(curr_stock, 1) if not curr_stock.is_integer() else int(curr_stock),
                    "avg_burn_daily": round(avg_burn_daily, 2),
                    "days_left": days_left if days_left < 100 else "> 30",
                    "target_stock": round(target_stock, 1),
                    "recommend_push": rec_push_rounded,
                    "urgency": urgency
                })

            # Tentukan status keseluruhan outlet
            if kritis_count > 0:
                outlet_status = "KRITIS"
                kritis_outlets_count += 1
            elif waspada_count > 0:
                outlet_status = "WASPADA"
                waspada_outlets_count += 1
            else:
                outlet_status = "AMAN"
                aman_outlets_count += 1

            items_to_ship_count = sum(1 for item in outlet_items if item['recommend_push'] > 0)
            total_items_to_ship += items_to_ship_count

            results_outlets.append({
                "code": code,
                "name": outlet_name,
                "scheduled_today": is_scheduled_today,
                "delivery_type": dtype,
                "location": location,
                "delivery_days": [DAYS_ID.get(d, d) for d in delivery_days],
                "gap_days": gap_days,
                "coverage_days": coverage_days,
                "status": outlet_status,
                "latest_data_day": latest_day_num,
                "items": outlet_items,
                "summary": {
                    "total_items_needed": items_to_ship_count,
                    "kritis_count": kritis_count,
                    "waspada_count": waspada_count
                }
            })

    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

    # Urutkan outlet: KRITIS duluan, lalu WASPADA, lalu AMAN
    status_priority = {"KRITIS": 0, "WASPADA": 1, "AMAN": 2, "DATA_TIDAK_ADA": 3}
    results_outlets.sort(key=lambda x: (0 if x["scheduled_today"] else 1, status_priority.get(x["status"], 99), x["code"]))

    return {
        "target_date": target_date_str,
        "target_day_name": target_day_id,
        "lookback_days": lookback_days,
        "buffer_days": buffer_days,
        "kpi": {
            "total_outlets_scheduled": sum(1 for o in results_outlets if o["scheduled_today"]),
            "kritis_outlets": kritis_outlets_count,
            "waspada_outlets": waspada_outlets_count,
            "aman_outlets": aman_outlets_count,
            "total_items_to_ship": total_items_to_ship,
            "total_unique_materials": len(all_shipment_items_map)
        },
        "all_materials_rekap": sorted([
            {"name": k, "total_qty": round(v, 1) if not v.is_integer() else int(v)}
            for k, v in all_shipment_items_map.items()
        ], key=lambda x: x["total_qty"], reverse=True),
        "outlets": results_outlets
    }


def export_push_recommendation_excel(analysis: Dict[str, Any], output_path: str) -> str:
    """
    Ekspor hasil analisis ke file Excel siap cetak:
    - Sheet 1: Rekap Gudang (Semua bahan yang perlu dimuat)
    - Sheet 2+: Surat Jalan per outlet yang butuh kiriman
    """
    wb = openpyxl.Workbook()
    ws_rekap = wb.active
    ws_rekap.title = "Rekap Muatan Gudang"

    # Styling helpers
    font_title = Font(name="Segoe UI", size=14, bold=True, color="1B5E20")
    font_subtitle = Font(name="Segoe UI", size=10, italic=True, color="555555")
    font_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    font_bold = Font(name="Segoe UI", size=10, bold=True)
    font_regular = Font(name="Segoe UI", size=10)
    font_kritis = Font(name="Segoe UI", size=10, bold=True, color="B71C1C")

    fill_header_green = PatternFill("solid", fgColor="2E7D32")
    fill_header_blue = PatternFill("solid", fgColor="1565C0")
    fill_zebra = PatternFill("solid", fgColor="F5F7FA")
    fill_kritis = PatternFill("solid", fgColor="FFEBEE")

    thin_border = Border(
        left=Side(style='thin', color='BDBDBD'),
        right=Side(style='thin', color='BDBDBD'),
        top=Side(style='thin', color='BDBDBD'),
        bottom=Side(style='thin', color='BDBDBD')
    )

    align_center = Alignment(horizontal='center', vertical='center')
    align_left = Alignment(horizontal='left', vertical='center')
    align_right = Alignment(horizontal='right', vertical='center')

    # ── SHEET 1: REKAP MUATAN GUDANG ──
    t_date = analysis.get("target_date", "")
    t_day = analysis.get("target_day_name", "")

    ws_rekap["A1"] = f"REKAP MUATAN GUDANG — PUSH DELIVERY"
    ws_rekap["A1"].font = font_title
    ws_rekap["A2"] = f"Pengiriman: {t_day}, {t_date} | Total Item Dimuat: {analysis['kpi']['total_items_to_ship']} item"
    ws_rekap["A2"].font = font_subtitle

    headers_rekap = ["No", "Nama Bahan Baku", "Total Qty Dimuat", "Satuan", "Keterangan Outlet Penerima"]
    for col_idx, h in enumerate(headers_rekap, start=1):
        c = ws_rekap.cell(row=4, column=col_idx, value=h)
        c.font = font_header
        c.fill = fill_header_green
        c.alignment = align_center
        c.border = thin_border

    rekap_items = analysis.get("all_materials_rekap", [])
    outlets_data = analysis.get("outlets", [])

    for r_idx, item in enumerate(rekap_items, start=5):
        m_name = item["name"]
        qty = item["total_qty"]

        # Cari outlet mana saja yang minta barang ini
        receiving_outlets = []
        for o in outlets_data:
            for oi in o.get("items", []):
                if oi["name"] == m_name and oi["recommend_push"] > 0:
                    receiving_outlets.append(f"{o['name']} ({oi['recommend_push']})")

        outlets_str = ", ".join(receiving_outlets[:8])
        if len(receiving_outlets) > 8:
            outlets_str += f", +{len(receiving_outlets) - 8} outlet lain"

        ws_rekap.cell(row=r_idx, column=1, value=r_idx - 4).alignment = align_center
        ws_rekap.cell(row=r_idx, column=2, value=m_name).alignment = align_left
        ws_rekap.cell(row=r_idx, column=3, value=qty).alignment = align_right
        ws_rekap.cell(row=r_idx, column=4, value="").alignment = align_center
        ws_rekap.cell(row=r_idx, column=5, value=outlets_str).alignment = align_left

        for c_idx in range(1, 6):
            cell = ws_rekap.cell(row=r_idx, column=c_idx)
            cell.font = font_regular
            cell.border = thin_border
            if (r_idx % 2 == 0):
                cell.fill = fill_zebra

    # Auto-adjust lebar kolom
    for col in ws_rekap.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_rekap.column_dimensions[col_letter].width = max(max_len + 3, 12)
    ws_rekap.column_dimensions['E'].width = 50

    # ── SHEET 2+: SURAT JALAN PER OUTLET ──
    for o in outlets_data:
        # Hanya buat surat jalan untuk outlet yang memiliki rekomendasi kirim > 0
        items_to_ship = [i for i in o.get("items", []) if i["recommend_push"] > 0]
        if not items_to_ship:
            continue

        sheet_title = f"SJ-{o['code']} {o['name'][:12]}".strip()
        ws_sj = wb.create_sheet(title=sheet_title[:31])

        ws_sj["A1"] = f"SURAT JALAN PENGIRIMAN BARANG"
        ws_sj["A1"].font = font_title
        ws_sj["A2"] = f"Outlet: [{o['code']}] {o['name']} ({o['location']}) | Jadwal: {o['delivery_type']} | Tanggal: {t_day}, {t_date}"
        ws_sj["A2"].font = font_subtitle

        headers_sj = ["No", "Kategori", "Nama Barang", "Stok Terkini", "Est. Habis", "Jumlah Kirim", "Satuan", "Check (Gudang)", "Check (Outlet)"]
        for col_idx, h in enumerate(headers_sj, start=1):
            c = ws_sj.cell(row=4, column=col_idx, value=h)
            c.font = font_header
            c.fill = fill_header_blue
            c.alignment = align_center
            c.border = thin_border

        for r_idx, item in enumerate(items_to_ship, start=5):
            is_kritis = (item["urgency"] == "KRITIS")

            ws_sj.cell(row=r_idx, column=1, value=r_idx - 4).alignment = align_center
            ws_sj.cell(row=r_idx, column=2, value=item["category"]).alignment = align_left
            ws_sj.cell(row=r_idx, column=3, value=item["name"]).alignment = align_left
            ws_sj.cell(row=r_idx, column=4, value=item["curr_stock"]).alignment = align_right
            ws_sj.cell(row=r_idx, column=5, value=f"{item['days_left']} hari").alignment = align_center
            ws_sj.cell(row=r_idx, column=6, value=item["recommend_push"]).alignment = align_right
            ws_sj.cell(row=r_idx, column=7, value="").alignment = align_center
            ws_sj.cell(row=r_idx, column=8, value="[  ]").alignment = align_center
            ws_sj.cell(row=r_idx, column=9, value="[  ]").alignment = align_center

            for c_idx in range(1, 10):
                cell = ws_sj.cell(row=r_idx, column=c_idx)
                cell.border = thin_border
                if is_kritis:
                    cell.fill = fill_kritis
                    cell.font = font_kritis if c_idx in (3, 6) else font_regular
                else:
                    cell.font = font_bold if c_idx == 6 else font_regular
                    if r_idx % 2 == 0:
                        cell.fill = fill_zebra

        # Tanda Tangan
        sign_row = len(items_to_ship) + 7
        ws_sj.cell(row=sign_row, column=2, value="Disiapkan Oleh (Gudang):").font = font_bold
        ws_sj.cell(row=sign_row, column=6, value="Diterima Oleh (Outlet):").font = font_bold

        ws_sj.cell(row=sign_row + 4, column=2, value="( ..................................... )").font = font_regular
        ws_sj.cell(row=sign_row + 4, column=6, value="( ..................................... )").font = font_regular

        for col in ws_sj.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws_sj.column_dimensions[col_letter].width = max(max_len + 3, 11)

    wb.save(output_path)
    return output_path
