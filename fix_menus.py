import os

template_dir = 'd:/Goks!/GOKS! WEB APP - RUNNING/templates'

menu_to_insert = '''          <a href="/agentic-dashboard" class="nav-item">
            <i class="fa-solid fa-robot"></i>
            <span>Agentic Control Room</span>
          </a>'''

for filename in os.listdir(template_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(template_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already has agentic-dashboard
        if '/agentic-dashboard' in content:
            print(f"Skipping {filename}, already has menu")
            continue
            
        # Find the mass-hide menu item
        search_str = '          <a href="/mass-hide" class="nav-item">\n            <i class="fa-solid fa-eye-slash"></i><span>Format Laporan</span>\n          </a>'
        search_str2 = '          <a href="/mass-hide" class="nav-item active">\n            <i class="fa-solid fa-eye-slash"></i><span>Format Laporan</span>\n          </a>'
        
        replaced = False
        if search_str in content:
            content = content.replace(search_str, search_str + '\n' + menu_to_insert)
            replaced = True
        elif search_str2 in content:
            content = content.replace(search_str2, search_str2 + '\n' + menu_to_insert)
            replaced = True
            
        if replaced:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {filename}")
        else:
            print(f"Could not find anchor in {filename}")
