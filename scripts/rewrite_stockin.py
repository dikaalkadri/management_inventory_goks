import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace <head> ... </head>
head_start = content.find('<head>')
head_end = content.find('</head>') + len('</head>')
new_head = '''<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Goks! Stock-In Manager</title>
    <link
      href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap"
      rel="stylesheet"
    />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
    <link rel="stylesheet" href="/static/css/eresto.css" />
    <style>
      /* Component specific styles adapted for dark mode */
      .config-bar {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 24px;
      }
      .config-bar label {
        color: var(--text-secondary);
        font-size: 0.85rem;
        font-weight: 500;
      }
      .config-bar input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 0.85rem;
        transition: all 0.2s;
        font-family: "DM Mono", monospace;
      }
      .config-bar input:focus {
        outline: none;
        border-color: var(--color-emerald);
        background: rgba(255, 255, 255, 0.1);
      }
      .btn-ghost {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        padding: 8px 16px;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        transition: 0.2s;
        font-weight: 600;
      }
      .btn-ghost:hover {
        background: rgba(255, 255, 255, 0.2);
      }
      .file-status {
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-family: "DM Mono", monospace;
      }
      .file-status.found {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
      }
      .file-status.notfound {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
      }
      
      .dashboard-grid {
        display: grid;
        grid-template-columns: 1.25fr 0.75fr;
        gap: 24px;
        align-items: start;
      }
      .left-column, .right-column {
        display: flex;
        flex-direction: column;
        gap: 20px;
      }
      
      .upload-card-wrapper {
        background: rgba(18, 18, 29, 0.45);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        overflow: hidden;
      }
      .upload-card-header {
        background: rgba(255, 255, 255, 0.03);
        padding: 16px 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        display: flex;
        align-items: center;
        gap: 10px;
      }
      .upload-card-header h2 {
        font-size: 1rem;
        font-weight: 700;
        margin: 0;
      }
      .upload-zone {
        border: 2px dashed rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 40px 20px;
        text-align: center;
        cursor: pointer;
        margin: 20px;
        background: rgba(255, 255, 255, 0.02);
        transition: 0.2s;
        position: relative;
      }
      .upload-zone:hover, .upload-zone.drag-over {
        border-color: var(--color-emerald);
        background: rgba(123, 44, 191, 0.05);
      }
      .upload-zone input[type="file"] {
        position: absolute;
        inset: 0;
        opacity: 0;
        cursor: pointer;
        width: 100%;
        height: 100%;
      }
      .upload-icon {
        font-size: 2.5rem;
        margin-bottom: 10px;
        display: block;
      }
      
      .card {
        background: rgba(18, 18, 29, 0.45);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        overflow: hidden;
      }
      .card-header {
        background: rgba(255, 255, 255, 0.03);
        padding: 16px 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        display: flex;
        align-items: center;
        gap: 12px;
      }
      .card-header h2 {
        font-size: 1rem;
        font-weight: 700;
        margin: 0;
      }
      .card-body {
        padding: 20px;
      }
      .card-footer {
        padding: 16px 20px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        display: flex;
        justify-content: space-between;
      }
      
      .items-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
      }
      .items-table th {
        color: var(--text-secondary);
        font-weight: 600;
        padding: 10px;
        text-align: left;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      }
      .items-table td {
        padding: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      }
      .items-table select, .items-table input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        padding: 6px 10px;
        border-radius: 6px;
        width: 100%;
      }
      .items-table select option {
        background: var(--bg-dark);
      }
      
      .stok-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
      }
      .stok-item {
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(255, 255, 255, 0.03);
        padding: 8px 12px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
      }
      .stok-item input {
        width: 80px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        padding: 4px 8px;
        border-radius: 6px;
        text-align: right;
      }
      
      .sisa-stock-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 16px;
      }
      .sisa-stok-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
      }
      .sisa-stok-card-title {
        font-weight: 600;
        margin-bottom: 8px;
      }
      .sisa-stok-card-values {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        background: rgba(0, 0, 0, 0.2);
        padding: 10px;
        border-radius: 8px;
      }
      .sisa-stok-val-box {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .sisa-stok-val-label {
        font-size: 0.7rem;
        color: var(--text-secondary);
        font-weight: 600;
      }
      .sisa-stok-val-num {
        font-size: 0.95rem;
        font-weight: 700;
      }
      
      .bottom-bar {
        position: fixed;
        bottom: 0;
        left: 280px; /* offset sidebar */
        right: 0;
        background: rgba(10, 10, 15, 0.9);
        backdrop-filter: blur(10px);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding: 16px 40px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 100;
      }
      
      .btn-submit-all {
        background: var(--color-emerald);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: 0.2s;
      }
      .btn-submit-all:hover {
        background: var(--color-emerald-light);
      }
      
      /* Utilities */
      .badge-sheet { padding: 4px 8px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; }
      .badge-bahan-utama { background: rgba(249, 168, 38, 0.2); color: #f9a826; }
      .badge-topping { background: rgba(230, 57, 70, 0.2); color: #e63946; }
      .badge-powder { background: rgba(139, 92, 246, 0.2); color: #a78bfa; }
      .badge-bahan-lainnya { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
      
      .btn-manual { background: rgba(123, 44, 191, 0.15); color: #a78bfa; border: 1px solid rgba(123, 44, 191, 0.3); padding: 8px 16px; border-radius: 8px; cursor: pointer; }
      .btn-manual:hover { background: rgba(123, 44, 191, 0.3); }
      .btn-remove-card { background: rgba(239, 68, 68, 0.1); color: #f87171; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; }
      .btn-del-row { background: none; border: none; color: #f87171; cursor: pointer; }
      .btn-add-row { background: none; border: 1px dashed rgba(255, 255, 255, 0.2); color: var(--text-primary); padding: 8px 16px; border-radius: 8px; cursor: pointer; }
      .btn-submit-card { background: rgba(255, 255, 255, 0.1); color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; }
      .btn-submit-card:hover { background: rgba(255, 255, 255, 0.2); }
      
      /* Toast */
      #toast { position: fixed; top: 20px; right: 20px; padding: 12px 20px; border-radius: 8px; background: rgba(18, 18, 29, 0.9); border-left: 4px solid var(--color-emerald); transform: translateX(120%); transition: 0.3s; z-index: 1000; }
      #toast.show { transform: translateX(0); }
      #toast.error { border-left-color: #ef4444; }
      
      .info-box { background: rgba(249, 168, 38, 0.1); border: 1px solid rgba(249, 168, 38, 0.2); color: #fcd34d; padding: 12px; border-radius: 8px; font-size: 0.85rem; }
      
      .section-divider {
        display: flex;
        align-items: center;
        gap: 14px;
        margin: 28px 0 18px;
      }
      .section-divider::before, .section-divider::after {
        content: ""; flex: 1; height: 1px; background: rgba(255, 255, 255, 0.1);
      }
      .section-divider-label {
        font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; font-size: 0.8rem;
      }
      
      .empty-state { text-align: center; padding: 40px; color: var(--text-secondary); }
      .empty-state .icon { font-size: 3rem; display: block; margin-bottom: 10px; }
      
      /* Row Masuk */
      tr.row-masuk td {
        background: rgba(16, 185, 129, 0.1) !important;
      }
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
          <a href="/" class="nav-item active">
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
        <header class="main-header">
          <div class="header-title">
            <h1>Stock-In Gudang</h1>
            <p class="header-subtitle">
              Kelola stok awal bulan dan pantau sisa stok terkini
            </p>
          </div>
          <div class="header-status">
            <span class="status-indicator online"></span>
            <span class="status-text">System Active</span>
          </div>
        </header>

        <div class="config-bar">
          <label>📄 File:</label>
          <input type="text" id="cfg-filename" placeholder="05__SO_MEI_2026.xlsx" style="width: 200px" />
          <label>📁 Folder:</label>
          <input type="text" id="cfg-folder" placeholder="C:\\Users\\...\\data" style="width: 220px" />
          <button class="btn-ghost" onclick="saveConfig()">Simpan</button>
          <button class="btn-ghost" onclick="checkFile()">Cek File</button>
          <div class="file-status" id="file-status">—</div>
          <a href="/settings" class="btn-ghost" style="margin-left: auto; text-decoration: none; display: flex; align-items: center; gap: 6px;">
            <i class="fa-solid fa-gears"></i> Konfigurasi SO
          </a>
        </div>

        <!-- ═══ TOP ROW: 2-Column Dashboard Grid ═══ -->
        <div class="dashboard-grid">
'''
content = content[:body_start] + new_body + content[main_start:]

# Add closing div for app-container at the end of body
content = content.replace('</body>', '    </div>\n  </body>')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated templates/index.html')
