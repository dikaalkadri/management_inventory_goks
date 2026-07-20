import os
import re

sidebar_content = """<aside class="app-sidebar">
  <div class="sidebar-brand">
    <i class="fa-solid fa-chart-line-up brand-icon"></i>
    <div class="brand-info">
      <span class="brand-name">Goks!</span>
      <span class="brand-tag">F&B Automation</span>
    </div>
  </div>

  <nav class="sidebar-nav">
    <a href="/" class="nav-item {% if active_menu == 'stockin' %}active{% endif %}">
      <i class="fa-solid fa-truck-ramp-box"></i>
      <span>Stock-In Gudang</span>
    </a>
    <a href="/eresto" class="nav-item {% if active_menu == 'eresto' %}active{% endif %}">
      <i class="fa-solid fa-file-excel"></i>
      <span>eResto Analysis</span>
    </a>
    <a href="/eresto-mass" class="nav-item {% if active_menu == 'eresto_mass' %}active{% endif %}">
      <i class="fa-solid fa-layer-group"></i>
      <span>eResto Mass Analysis</span>
    </a>
    <a href="/sinkronisasi" class="nav-item {% if active_menu == 'sinkronisasi' %}active{% endif %}">
      <i class="fa-solid fa-arrows-rotate"></i>
      <span>Sinkronisasi Penjualan</span>
    </a>
    <a href="/mass-sinkronisasi" class="nav-item {% if active_menu == 'mass_sinkronisasi' %}active{% endif %}">
      <i class="fa-solid fa-bolt"></i>
      <span>Mass Sinkronisasi</span>
    </a>
    <a href="/update-kerugian" class="nav-item {% if active_menu == 'update_kerugian' %}active{% endif %}">
      <i class="fa-solid fa-calendar-check"></i>
      <span>Update Kerugian Harian</span>
    </a>
    <a href="/mass-update" class="nav-item {% if active_menu == 'mass_update' %}active{% endif %}">
      <i class="fa-solid fa-wand-magic-sparkles"></i>
      <span>Update Rumus Massal</span>
    </a>
    <a href="/mass-hide" class="nav-item {% if active_menu == 'mass_hide' %}active{% endif %}">
      <i class="fa-solid fa-eye-slash"></i>
      <span>Format Laporan</span>
    </a>
  </nav>

  <div class="sidebar-footer">
    <div class="user-profile">
      <i class="fa-solid fa-circle-user profile-icon"></i>
      <div>
        <div class="profile-name">Outlet Manager</div>
        <div class="profile-role">Administrator</div>
      </div>
    </div>
  </div>
</aside>
"""

with open('templates/sidebar.html', 'w', encoding='utf-8') as f:
    f.write(sidebar_content)
print("Created templates/sidebar.html")

file_menu_map = {
    'index.html': 'stockin',
    'stock_gudang.html': 'stockin',
    'settings.html': 'stockin',
    'eresto_analysis.html': 'eresto',
    'eresto_mass_analysis.html': 'eresto_mass',
    'sinkronisasi_penjualan.html': 'sinkronisasi',
    'mass_sinkronisasi_massal.html': 'mass_sinkronisasi',
    'update_kerugian.html': 'update_kerugian',
    'mass_update.html': 'mass_update',
    'mass_hide.html': 'mass_hide',
}

sidebar_pattern = re.compile(r'<aside class="app-sidebar">.*?</aside>', re.DOTALL)

for filename, active_menu in file_menu_map.items():
    filepath = os.path.join('templates', filename)
    if not os.path.exists(filepath):
        print(f"Skipping {filename} (not found)")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace the aside block with {% include 'sidebar.html' %}
    include_str = f"{{% set active_menu = '{active_menu}' %}}\n      {{% include 'sidebar.html' %}}"
    new_content = sidebar_pattern.sub(include_str, content)
    
    # 2. If it's one of the recently modified files, remove the embedded CSS
    if filename in ['index.html', 'stock_gudang.html', 'settings.html']:
        start_idx = new_content.find('.app-sidebar {')
        if start_idx != -1:
            start_idx = new_content.rfind('\n', 0, start_idx)
            end_idx = new_content.find('.profile-role {', start_idx)
            if end_idx != -1:
                end_idx = new_content.find('}', end_idx) + 1
                new_content = new_content[:start_idx] + new_content[end_idx:]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Updated {filename}")
