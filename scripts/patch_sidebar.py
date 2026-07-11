import os

template_dir = 'templates'
target_files = ['index.html', 'mass_update.html', 'settings.html', 'eresto_analysis.html', 'sinkronisasi_penjualan.html', 'stock_gudang.html']

new_menu_item = """          <a href="/mass-hide" class="nav-item">
            <i class="fa-solid fa-eye-slash"></i><span>Format Laporan</span>
          </a>
"""

for fname in target_files:
    fpath = os.path.join(template_dir, fname)
    if not os.path.exists(fpath):
        continue
    
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We look for the closing </a> of the mass-update link
    # Let's use string replace.
    # The mass update link could be active or not active.
    
    # In mass_update.html:
    # <a href="/mass-update" class="nav-item active">
    #   <i class="fa-solid fa-wand-magic-sparkles"></i><span>Update Rumus Massal</span>
    # </a>
    
    # In others:
    # <a href="/mass-update" class="nav-item">
    #   ...
    
    # To be safe, we'll split by "<span>Update Rumus Massal</span>\n          </a>\n"
    # Wait, the spacing might vary. Let's do a regex or just simple string find.
    
    import re
    # Find: <a href="/mass-update" ...> ... </a>
    pattern = re.compile(r'(<a href="/mass-update".*?</a>\s*)', re.DOTALL)
    
    if pattern.search(content):
        # Insert after the match
        new_content = pattern.sub(r'\1' + new_menu_item, content, count=1)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {fname}")
    else:
        print(f"Failed to find mass-update menu in {fname}")
