import re

with open('templates/settings.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace <head> ... </head>
head_start = content.find('<head>')
head_end = content.find('</head>') + len('</head>')
new_head = '''<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Settings — Goks! Stock-In</title>
    <link
      href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap"
      rel="stylesheet"
    />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
    <link rel="stylesheet" href="/static/css/eresto.css" />
    <style>
      .section-card {
        background: rgba(18, 18, 29, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        margin-bottom: 28px;
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

      .inv-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
        margin-bottom: 16px;
      }
      .inv-table th {
        background: rgba(255, 255, 255, 0.02);
        color: var(--text-secondary);
        font-weight: 600;
        padding: 12px 10px;
        text-align: left;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      }
      .inv-table td {
        padding: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      }
      .inv-table tr:hover td {
        background: rgba(255, 255, 255, 0.02);
      }
      .inv-table input, .inv-table select {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        padding: 6px 10px;
        border-radius: 6px;
        width: 100%;
      }
      .inv-table select option {
        background: var(--bg-dark);
      }

      .btn {
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        border: none;
        cursor: pointer;
        transition: 0.2s;
      }
      .btn-primary { background: var(--color-emerald); color: white; }
      .btn-primary:hover { background: var(--color-emerald-light); }
      .btn-accent { background: rgba(249, 168, 38, 0.2); color: #f9a826; border: 1px solid rgba(249, 168, 38, 0.3); }
      .btn-accent:hover { background: rgba(249, 168, 38, 0.3); }
      .btn-danger { background: rgba(239, 68, 68, 0.15); color: #f87171; padding: 6px 12px; }
      .btn-danger:hover { background: rgba(239, 68, 68, 0.3); }
      .btn-ghost { background: rgba(255, 255, 255, 0.1); color: white; }
      .btn-ghost:hover { background: rgba(255, 255, 255, 0.2); }

      .add-form {
        display: grid;
        grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr;
        gap: 12px;
        align-items: end;
        margin-top: 16px;
        padding-top: 20px;
        border-top: 1px dashed rgba(255, 255, 255, 0.1);
      }
      .add-form .form-group { display: flex; flex-direction: column; gap: 6px; }
      .add-form label { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; }
      .add-form input, .add-form select {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
      }
      .add-form select option { background: var(--bg-dark); }
      
      .kw-input { font-family: "DM Mono", monospace !important; }

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
        <header class="main-header">
          <div class="header-title">
            <h1>Konfigurasi Stock-In</h1>
            <p class="header-subtitle">
              Atur daftar item dan outlet untuk kebutuhan Stock-In
            </p>
          </div>
          <div class="header-status">
            <span class="status-indicator online"></span>
            <span class="status-text">System Active</span>
          </div>
        </header>
'''
content = content[:body_start] + new_body + content[main_start:]

# Change #outlets-textarea style inside body
content = content.replace(
'''            style="
              width: 100%;
              height: 260px;
              border: 1px solid var(--border);
              border-radius: 8px;
              padding: 12px;
              font-family: &quot;DM Mono&quot;, monospace;
              font-size: 0.78rem;
              resize: vertical;
              line-height: 1.6;
              color: var(--green-dark);
            "''',
'''            style="
              width: 100%;
              height: 260px;
              background: rgba(255, 255, 255, 0.02);
              border: 1px solid rgba(255, 255, 255, 0.1);
              border-radius: 8px;
              padding: 12px;
              font-family: &quot;DM Mono&quot;, monospace;
              font-size: 0.85rem;
              resize: vertical;
              line-height: 1.6;
              color: white;
            "'''
)

# Add closing div for app-container at the end of body
content = content.replace('</body>', '    </div>\n  </body>')

with open('templates/settings.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated templates/settings.html')
