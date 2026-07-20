import re

with open('templates/stock_gudang.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace <head> ... </head>
head_start = content.find('<head>')
head_end = content.find('</head>') + len('</head>')
new_head = '''<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Stock Gudang — Goks! Stock-In</title>
    <link
      href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap"
      rel="stylesheet"
    />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
    <link rel="stylesheet" href="/static/css/eresto.css" />
    <style>
      .page-title {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 24px;
      }
      .page-title h1 {
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(135deg, #ffffff 30%, var(--text-secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }
      .subtitle {
        color: var(--text-secondary);
        font-size: 0.9rem;
      }
      .btn-primary {
        background: var(--color-emerald);
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        font-weight: 600;
        transition: 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 8px;
      }
      .btn-primary:hover {
        background: var(--color-emerald-light);
      }
      .section-card {
        background: rgba(18, 18, 29, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        margin-bottom: 24px;
        overflow: hidden;
      }
      .section-head {
        background: rgba(255, 255, 255, 0.03);
        padding: 16px 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .section-head h2 {
        font-size: 1.1rem;
        font-weight: 700;
        margin: 0;
      }
      .section-body {
        padding: 20px;
      }
      .info-box {
        background: rgba(249, 168, 38, 0.1);
        border: 1px solid rgba(249, 168, 38, 0.2);
        color: #fcd34d;
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 0.85rem;
        margin-bottom: 20px;
      }
      .stok-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 16px;
        margin-bottom: 20px;
      }
      .stok-item {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 12px 16px;
        border-radius: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
      }
      .stok-item label {
        font-weight: 500;
        font-size: 0.9rem;
      }
      .stok-item input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        padding: 6px 12px;
        border-radius: 6px;
        width: 100px;
        text-align: right;
        font-family: "DM Mono", monospace;
      }
      .stok-item input:focus {
        outline: none;
        border-color: var(--color-emerald);
      }
      
      .sisa-table {
        width: 100%;
        border-collapse: collapse;
      }
      .sisa-table th {
        background: rgba(255, 255, 255, 0.02);
        color: var(--text-secondary);
        font-weight: 600;
        padding: 12px 20px;
        text-align: left;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      }
      .sisa-table td {
        padding: 12px 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      }
      .sisa-table tr:hover td {
        background: rgba(255, 255, 255, 0.02);
      }
      .badge-sheet {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
      }
      .badge-utama { background: rgba(249, 168, 38, 0.2); color: #f9a826; }
      .badge-topping { background: rgba(230, 57, 70, 0.2); color: #e63946; }
      .badge-powder { background: rgba(139, 92, 246, 0.2); color: #a78bfa; }
      .badge-lainnya { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
      
      .sisa-val {
        font-family: "DM Mono", monospace;
        font-weight: 600;
      }
      
      /* Toast */
      #toast { position: fixed; top: 20px; right: 20px; padding: 12px 20px; border-radius: 8px; background: rgba(18, 18, 29, 0.9); border-left: 4px solid var(--color-emerald); transform: translateX(120%); transition: 0.3s; z-index: 1000; }
      #toast.show { transform: translateX(0); }
      #toast.error { border-left-color: #ef4444; }
    </style>
  </head>'''
content = content[:head_start] + new_head + content[head_end:]

# Replace <body> structure
body_start = content.find('<body>')
main_start = content.find('<main>') + len('<main>')

new_body = r'''<body>
    <div class="glow-blob blob-1"></div>
    <div class="glow-blob blob-2"></div>
    <div class="glow-blob blob-3"></div>

    <div class="app-container">
      <aside class="app-sidebar">
        <div class="sidebar-brand">
          <i class="fa-solid fa-chart-line-up brand-icon"></i>
          <div class="brand-info">
            <span class="brand-name">Goks!</span>
            <span class="brand-tag">F&B Automation</span>
          </div>
        </div>

        <nav class="sidebar-nav">
          <a href="/" class="nav-item">
            <i class="fa-solid fa-truck-ramp-box"></i>
            <span>Stock-In Gudang</span>
          </a>
          <a href="/eresto" class="nav-item">
            <i class="fa-solid fa-file-excel"></i>
            <span>eResto Analysis</span>
          </a>
          <a href="/eresto-mass" class="nav-item">
            <i class="fa-solid fa-layer-group"></i>
            <span>eResto Mass Analysis</span>
          </a>
          <a href="/sinkronisasi" class="nav-item">
            <i class="fa-solid fa-arrows-rotate"></i>
            <span>Sinkronisasi Penjualan</span>
          </a>
          <a href="/mass-sinkronisasi" class="nav-item">
            <i class="fa-solid fa-bolt"></i>
            <span>Mass Sinkronisasi</span>
          </a>
          <a href="/update-kerugian" class="nav-item">
            <i class="fa-solid fa-calendar-check"></i>
            <span>Update Kerugian Harian</span>
          </a>
          <a href="/mass-update" class="nav-item">
            <i class="fa-solid fa-wand-magic-sparkles"></i>
            <span>Update Rumus Massal</span>
          </a>
          <a href="/mass-hide" class="nav-item">
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

      <main class="app-main">
'''
content = content[:body_start] + new_body + content[main_start:]

# Add closing div for app-container at the end of body
content = content.replace('</body>', '    </div>\n  </body>')

with open('templates/stock_gudang.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated templates/stock_gudang.html')
