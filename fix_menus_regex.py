import os
import re

template_dir = 'd:/Goks!/GOKS! WEB APP - RUNNING/templates'

menu_to_insert = '''          <a href="/agentic-dashboard" class="nav-item">
            <i class="fa-solid fa-robot"></i>
            <span>Agentic Control Room</span>
          </a>'''

for filename in ['eresto_analysis.html', 'mass_hide.html', 'mass_update.html', 'sinkronisasi_penjualan.html']:
    filepath = os.path.join(template_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '/agentic-dashboard' in content:
        continue
        
    # Match the </a> of the mass-hide menu item
    # It might look like: <a href="/mass-hide" ...> ... </a>
    pattern = r'(<a href="/mass-hide".*?</a>)'
    
    # We replace the FIRST match of this pattern with the match itself + our new menu
    new_content = re.sub(pattern, r'\1\n' + menu_to_insert, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filename}")
    else:
        print(f"Still failed {filename}")
