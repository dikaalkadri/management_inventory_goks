import os
import json

CATALOG_PATH = 'master_catalog.json'

def load_master_catalog():
    """Load data master_catalog.json secara aman."""
    if not os.path.exists(CATALOG_PATH):
        return []
    try:
        with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('catalog', []) if isinstance(data, dict) else data
    except Exception as e:
        print(f"[ERROR] Gagal memuat master catalog: {e}")
        return []

def save_master_catalog(catalog_data):
    """Menyimpan kembali data catalog ke master_catalog.json."""
    try:
        with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
            json.dump({"catalog": catalog_data}, f, ensure_ascii=False, indent=2)
        return True, "Katalog berhasil disimpan."
    except Exception as e:
        return False, f"Gagal menyimpan katalog: {str(e)}"

def update_product_price(product_name, new_price):
    """Update harga spesifik untuk satu produk."""
    catalog = load_master_catalog()
    updated = False
    for item in catalog:
        if item['product'].strip().lower() == product_name.strip().lower():
            item['price'] = float(new_price)
            updated = True
            break
    if updated:
        return save_master_catalog(catalog)
    return False, "Produk tidak ditemukan di katalog."

def get_catalog_maps():
    """Menghasilkan dictionary map untuk mempermudah pencarian O(1) saat sinkronisasi."""
    catalog = load_master_catalog()
    category_map = {}
    price_map = {}
    
    for item in catalog:
        prod_name = item['product'].strip()
        category_map[prod_name.upper()] = item.get('category', '')
        price_map[prod_name.upper()] = float(item.get('price', 0))
        
    return catalog, category_map, price_map