import os
import re

template_dir = 'templates'
target_files = [
    'eresto_analysis.html',
    'eresto_mass_analysis.html',
    'index.html',
    'mass_hide.html',
    'mass_sinkronisasi_massal.html',
    'mass_update.html',
    'settings.html',
    'sinkronisasi_penjualan.html',
    'stock_gudang.html'
]

new_menu_item = """          <a href="/update-kerugian" class="nav-item">
            <i class="fa-solid fa-calendar-check"></i>
            <span>Update Kerugian Harian</span>
          </a>
"""

# Regex to match the Mass Sinkronisasi anchor tag
# Something like:
# <a href="/mass-sinkronisasi" class="nav-item ...">
#   <i class="..."></i>
#   <span>Mass Sinkronisasi</span>
# </a>
pattern = re.compile(r'(<a href="/mass-sinkronisasi"[^>]*>.*?</a>\n)', re.DOTALL)

for fname in target_files:
    fpath = os.path.join(template_dir, fname)
    if not os.path.exists(fpath):
        print(f"Not found: {fname}")
        continue
    
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if pattern.search(content):
        # Insert after the match
        new_content = pattern.sub(r'\1' + new_menu_item, content, count=1)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {fname}")
    else:
        print(f"Failed to find mass-sinkronisasi menu in {fname}")
