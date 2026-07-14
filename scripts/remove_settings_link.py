import os
import re

template_dir = 'templates'
target_files = [f for f in os.listdir(template_dir) if f.endswith('.html')]

# We want to remove the block:
# <a href="/settings" class="nav-item">
#   <i class="fa-solid fa-gears"></i>
#   <span>Konfigurasi SO</span>
# </a>

pattern_dark_sidebar = re.compile(r'<a href="/settings"[^>]*>.*?<span>Konfigurasi SO</span>.*?</a>\s*', re.DOTALL)
pattern_top_nav = re.compile(r'<a href="/settings"[^>]*>.*?Konfigurasi SO.*?</a>\s*', re.DOTALL)

for fname in target_files:
    fpath = os.path.join(template_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    content = pattern_dark_sidebar.sub('', content)
    content = pattern_top_nav.sub('', content)
    
    if content != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Removed /settings link from {fname}")
