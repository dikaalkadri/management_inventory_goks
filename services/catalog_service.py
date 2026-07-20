import os
import json

import config

POS_PATH = os.path.join(config.BASE_DIR, 'data', 'master_pos.json')
MATERIALS_PATH = os.path.join(config.BASE_DIR, 'data', 'master_materials.json')

# ── Cache in-memory ───────────────────────────────────────────────────────────
# Data catalog (POS & Bahan Baku) sangat jarang berubah saat proses batch
# berjalan. Cache ini menghindari ribuan disk-read yang tidak perlu.
_pos_cache = None
_materials_cache = None


def invalidate_catalog_cache():
    """Reset cache. Dipanggil otomatis setelah save_pos() / save_materials()."""
    global _pos_cache, _materials_cache
    _pos_cache = None
    _materials_cache = None


def load_pos():
    global _pos_cache
    if _pos_cache is not None:
        return _pos_cache
    if not os.path.exists(POS_PATH):
        return []
    try:
        with open(POS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _pos_cache = data.get('pos_items', []) if isinstance(data, dict) else data
            return _pos_cache
    except Exception as e:
        print(f"[ERROR] Gagal memuat pos: {e}")
        return []


def save_pos(items):
    try:
        with open(POS_PATH, 'w', encoding='utf-8') as f:
            json.dump({"pos_items": items}, f, ensure_ascii=False, indent=2)
        invalidate_catalog_cache()  # Reset cache setelah data berubah
        return True, "Daftar Menu POS berhasil disimpan."
    except Exception as e:
        return False, f"Gagal menyimpan POS: {str(e)}"


def load_materials():
    global _materials_cache
    if _materials_cache is not None:
        return _materials_cache
    if not os.path.exists(MATERIALS_PATH):
        return []
    try:
        with open(MATERIALS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _materials_cache = data.get('materials', []) if isinstance(data, dict) else data
            return _materials_cache
    except Exception as e:
        print(f"[ERROR] Gagal memuat materials: {e}")
        return []


def save_materials(items):
    try:
        with open(MATERIALS_PATH, 'w', encoding='utf-8') as f:
            json.dump({"materials": items}, f, ensure_ascii=False, indent=2)
        invalidate_catalog_cache()  # Reset cache setelah data berubah
        return True, "Daftar Bahan Baku berhasil disimpan."
    except Exception as e:
        return False, f"Gagal menyimpan Bahan Baku: {str(e)}"


def get_catalog_maps():
    """Menghasilkan dictionary map untuk mempermudah pencarian O(1) saat sinkronisasi."""
    pos_items = load_pos()
    materials = load_materials()
    
    category_map = {}
    for item in pos_items:
        prod_name = item.get('product', '').strip()
        if prod_name:
            category_map[prod_name.upper()] = item.get('category', '')
            
    price_map = {}
    for item in materials:
        mat_name = item.get('name', '').strip()
        if mat_name:
            price_map[mat_name.upper()] = float(item.get('price', 0))
            
    return pos_items, category_map, price_map