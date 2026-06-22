import os
import re
import glob

template_dir = r"d:\Goks!\GOKS! WEB APP - RUNNING\templates"
files = glob.glob(os.path.join(template_dir, "*.html"))

new_link = """          <a href="/mass-update" class="nav-item">
            <i class="fa-solid fa-wand-magic-sparkles"></i>
            <span>Update Rumus Massal</span>
          </a>
"""

for filepath in files:
    if "mass_update.html" in filepath:
        continue # we already added it there properly

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if "/mass-update" in content:
        print(f"Already updated {os.path.basename(filepath)}")
        continue

    # Regex to find </nav>
    # we replace </nav> with new_link + </nav>
    updated = re.sub(r'(</nav>)', r'  ' + new_link + r'        \1', content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(updated)
    print(f"Updated {os.path.basename(filepath)}")

