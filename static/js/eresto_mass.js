/**
 * eResto Mass Analysis — Frontend Logic
 *
 * Handles:
 * - File drag & drop / browse upload
 * - POST to /api/eresto-mass/upload → show outlet preview table
 * - POST to /api/eresto-mass/process → show download ZIP card
 * - Toast notification system (shared style with eresto.js)
 */

'use strict';

// ─── State ───────────────────────────────────────────────────────────────────
let currentFileId = null;
let currentFile = null;

// ─── DOM References ──────────────────────────────────────────────────────────
const dropZone         = document.getElementById('dropZone');
const fileInput        = document.getElementById('fileInput');
const activeFileBox    = document.getElementById('activeFileBox');
const uploadedFileName = document.getElementById('uploadedFileName');
const uploadedFileSize = document.getElementById('uploadedFileSize');
const removeFileBtn    = document.getElementById('removeFileBtn');

const previewCard      = document.getElementById('previewCard');
const statRawRows      = document.getElementById('statRawRows');
const statCleanRows    = document.getElementById('statCleanRows');
const statOutletCount  = document.getElementById('statOutletCount');
const statDateRange    = document.getElementById('statDateRange');
const outletCountBadge = document.getElementById('outletCountBadge');
const outletTableBody  = document.getElementById('outletTableBody');

const processCard      = document.getElementById('processCard');
const processBtn       = document.getElementById('processBtn');
const progressBox      = document.getElementById('progressBox');
const progressText     = document.getElementById('progressText');

const downloadCard     = document.getElementById('downloadCard');
const downloadDesc     = document.getElementById('downloadDesc');
const downloadLink     = document.getElementById('downloadLink');
const resultMetaRow    = document.getElementById('resultMetaRow');
const processedList    = document.getElementById('processedList');
const skippedListWrap  = document.getElementById('skippedListWrap');
const skippedList      = document.getElementById('skippedList');
const resetBtn         = document.getElementById('resetBtn');

// ─── Master Product DOM References ──────────────────────────────────────────
const masterProductsList = document.getElementById('masterProductsList');
const newProdName        = document.getElementById('newProdName');
const addProdBtn         = document.getElementById('addProdBtn');
const saveOrderBtn       = document.getElementById('saveOrderBtn');
const masterProductCount = document.getElementById('masterProductCount');
const searchMasterProd   = document.getElementById('searchMasterProd');
let allMasterProducts    = [];

// ─── Upload Handlers ─────────────────────────────────────────────────────────
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const files = e.dataTransfer.files;
  if (files.length > 0) handleFileSelected(files[0]);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files.length > 0) handleFileSelected(fileInput.files[0]);
});

removeFileBtn.addEventListener('click', () => resetAll());

// ─── File Selected → Show active state, auto-upload ──────────────────────────
function handleFileSelected(file) {
  const allowed = ['xlsx', 'xls'];
  const ext = file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showToast('error', 'Format file tidak didukung. Gunakan .xlsx atau .xls');
    return;
  }

  currentFile = file;
  uploadedFileName.textContent = file.name;
  uploadedFileSize.textContent = formatBytes(file.size);

  dropZone.style.display = 'none';
  activeFileBox.style.display = 'flex';

  uploadFile(file);
}

// ─── Upload API Call ──────────────────────────────────────────────────────────
async function uploadFile(file) {
  showToast('info', 'Mengunggah dan menganalisa file...');

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/eresto-mass/upload', { method: 'POST', body: formData });
    const data = await res.json();

    if (data.status !== 'ok') {
      showToast('error', data.message || 'Gagal mengunggah file');
      resetAll();
      return;
    }

    currentFileId = data.file_id;

    // Populate stat boxes
    statRawRows.textContent    = data.total_rows_raw.toLocaleString('id-ID');
    statCleanRows.textContent  = data.total_rows_clean.toLocaleString('id-ID');
    statOutletCount.textContent = data.outlet_count;
    statDateRange.textContent  = data.date_range
      ? `${data.date_range[0]} – ${data.date_range[1]}`
      : '-';
    outletCountBadge.textContent = `${data.outlet_count} Outlet`;

    // Populate outlet table
    outletTableBody.innerHTML = '';
    (data.outlet_summaries || []).forEach((o, idx) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td>${escapeHtml(o.outlet)}</td>
        <td>${o.rows.toLocaleString('id-ID')}</td>
        <td>${escapeHtml(o.date_range)}</td>
      `;
      outletTableBody.appendChild(tr);
    });

    // Show cards
    previewCard.style.display = 'block';
    processCard.style.display = 'block';

    showToast('success', `${data.outlet_count} outlet terdeteksi — siap diproses!`);

  } catch (err) {
    showToast('error', 'Koneksi gagal. Coba lagi.');
    resetAll();
  }
}

// ─── Process API Call ─────────────────────────────────────────────────────────
processBtn.addEventListener('click', async () => {
  if (!currentFileId) {
    showToast('error', 'Tidak ada file yang siap diproses');
    return;
  }

  processBtn.disabled = true;
  progressBox.style.display = 'block';
  progressText.textContent = 'Sedang memproses dan generate Excel per outlet... Harap tunggu';

  try {
    const res = await fetch('/api/eresto-mass/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_id: currentFileId }),
    });
    const data = await res.json();

    progressBox.style.display = 'none';
    processBtn.disabled = false;

    if (data.status !== 'ok') {
      showToast('error', data.message || 'Gagal memproses data');
      return;
    }

    // Build result meta boxes
    resultMetaRow.innerHTML = `
      <div class="result-meta-box">
        <span class="meta-val">${data.file_count}</span>
        <span class="meta-lbl">File Excel</span>
      </div>
      <div class="result-meta-box">
        <span class="meta-val">${(data.outlets_skipped || []).length}</span>
        <span class="meta-lbl">Dilewati</span>
      </div>
    `;

    downloadDesc.textContent = data.message;

    // Processed outlets list
    processedList.innerHTML = '';
    (data.outlets_processed || []).forEach(name => {
      const div = document.createElement('div');
      div.className = 'processed-item';
      div.innerHTML = `<i class="fa-solid fa-circle-check"></i> <span>${escapeHtml(name)}</span>`;
      processedList.appendChild(div);
    });

    // Skipped outlets
    if ((data.outlets_skipped || []).length > 0) {
      skippedList.innerHTML = data.outlets_skipped.map(n => `<div>• ${escapeHtml(n)}</div>`).join('');
      skippedListWrap.style.display = 'block';
    } else {
      skippedListWrap.style.display = 'none';
    }

    downloadLink.href = data.download_url;
    downloadLink.setAttribute('download', data.filename);

    processCard.style.display = 'none';
    downloadCard.style.display = 'block';

    showToast('success', `ZIP berhasil dibuat dengan ${data.file_count} file Excel!`);

  } catch (err) {
    progressBox.style.display = 'none';
    processBtn.disabled = false;
    showToast('error', 'Koneksi gagal. Coba lagi.');
  }
});

// ─── Reset ────────────────────────────────────────────────────────────────────
resetBtn.addEventListener('click', resetAll);

function resetAll() {
  currentFileId = null;
  currentFile = null;

  fileInput.value = '';
  dropZone.style.display = 'flex';
  activeFileBox.style.display = 'none';

  previewCard.style.display = 'none';
  processCard.style.display = 'none';
  downloadCard.style.display = 'none';
  progressBox.style.display = 'none';
  processBtn.disabled = false;

  outletTableBody.innerHTML = '';
  processedList.innerHTML = '';
  skippedList.innerHTML = '';
  skippedListWrap.style.display = 'none';
  resultMetaRow.innerHTML = '';
}

// ─── Toast System ─────────────────────────────────────────────────────────────
function showToast(type, message) {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `alert-toast alert-${type}`;

  const icons = { success: 'circle-check', error: 'circle-xmark', info: 'circle-info', warning: 'triangle-exclamation' };
  toast.innerHTML = `
    <i class="fa-solid fa-${icons[type] || 'circle-info'}"></i>
    <span>${escapeHtml(message)}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">
      <i class="fa-solid fa-xmark"></i>
    </button>
  `;

  container.appendChild(toast);
  setTimeout(() => toast.classList.add('show'), 10);
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 400);
  }, 5000);
}

// ─── Utilities ────────────────────────────────────────────────────────────────
function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function escapeHtml(str) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(str).replace(/[&<>"']/g, m => map[m]);
}

// ─── Master Product Management (Shared with eResto Analysis) ─────────────────

async function loadMasterProductsList() {
  if (!masterProductsList) return;
  try {
    const res = await fetch('/api/eresto/master-product');
    const data = await res.json();
    allMasterProducts = data.products || [];
    renderMasterProducts(allMasterProducts);
  } catch (err) {
    console.error('Failed to load master products:', err);
  }
}

function renderMasterProducts(productsToRender) {
  if (!masterProductsList) return;
  masterProductsList.innerHTML = '';

  if (masterProductCount) {
    const total = allMasterProducts.length;
    if (productsToRender.length !== total) {
      masterProductCount.textContent = `${productsToRender.length} / ${total} Produk`;
    } else {
      masterProductCount.textContent = `${total} Produk`;
    }
  }

  if (productsToRender.length === 0) {
    const emptyLi = document.createElement('li');
    emptyLi.style.cssText = 'padding: 20px; text-align: center; color: rgba(255,255,255,0.4); font-size: 13px; list-style: none;';
    emptyLi.textContent = searchMasterProd && searchMasterProd.value.trim()
      ? 'Tidak ada produk yang cocok dengan pencarian'
      : 'Belum ada master product';
    masterProductsList.appendChild(emptyLi);
    return;
  }

  const isFiltered = searchMasterProd && searchMasterProd.value.trim().length > 0;

  productsToRender.forEach((prod) => {
    const li = document.createElement('li');
    li.className = 'master-item';
    li.draggable = !isFiltered;
    li.dataset.name = prod;

    li.innerHTML = `
      <div class="item-left">
        <i class="fa-solid fa-grip-vertical drag-handle" style="${isFiltered ? 'opacity: 0.3; cursor: not-allowed;' : ''}"></i>
        <span>${escapeHtml(prod)}</span>
      </div>
      <button class="btn-remove-prod" title="Hapus Product">
        <i class="fa-solid fa-xmark"></i>
      </button>
    `;

    if (!isFiltered) {
      setupDragAndDropItem(li);
    }

    li.querySelector('.btn-remove-prod').addEventListener('click', (e) => {
      e.stopPropagation();
      removeProductItem(prod);
    });

    masterProductsList.appendChild(li);
  });
}

function setupDragAndDropItem(item) {
  item.addEventListener('dragstart', () => {
    item.classList.add('dragging');
  });

  item.addEventListener('dragend', () => {
    item.classList.remove('dragging');
    const currentOrder = [...masterProductsList.querySelectorAll('.master-item')].map(el => el.dataset.name);
    allMasterProducts = currentOrder;
  });
}

if (masterProductsList) {
  masterProductsList.addEventListener('dragover', (e) => {
    e.preventDefault();
    const afterElement = getDragAfterElement(masterProductsList, e.clientY);
    const dragging = document.querySelector('.dragging');
    if (!dragging) return;
    if (afterElement == null) {
      masterProductsList.appendChild(dragging);
    } else {
      masterProductsList.insertBefore(dragging, afterElement);
    }
  });
}

function getDragAfterElement(container, y) {
  const draggableElements = [
    ...container.querySelectorAll('.master-item:not(.dragging)'),
  ];

  return draggableElements.reduce(
    (closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;
      if (offset < 0 && offset > closest.offset) {
        return { offset: offset, element: child };
      } else {
        return closest;
      }
    },
    { offset: -Infinity },
  ).element;
}

// Add Product
if (addProdBtn && newProdName) {
  addProdBtn.addEventListener('click', async () => {
    const name = newProdName.value.trim();
    if (!name) return;

    try {
      const res = await fetch('/api/eresto/master-product/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        showToast('success', `Product "${name}" berhasil ditambahkan!`);
        newProdName.value = '';
        if (searchMasterProd) searchMasterProd.value = '';
        allMasterProducts = data.products || [];
        renderMasterProducts(allMasterProducts);
        setTimeout(() => {
          if (masterProductsList.lastElementChild) {
            masterProductsList.lastElementChild.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          }
        }, 100);
      } else {
        showToast('error', data.message || 'Gagal menambahkan product');
      }
    } catch (err) {
      console.error(err);
      showToast('error', 'Gagal terhubung dengan database product.');
    }
  });

  newProdName.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') addProdBtn.click();
  });
}

// Search Filter
if (searchMasterProd) {
  searchMasterProd.addEventListener('input', (e) => {
    const query = e.target.value.trim().toLowerCase();
    if (!query) {
      renderMasterProducts(allMasterProducts);
    } else {
      const filtered = allMasterProducts.filter(p => p.toLowerCase().includes(query));
      renderMasterProducts(filtered);
    }
  });
}

// Remove Product
async function removeProductItem(name) {
  if (!confirm(`Hapus "${name}" dari Master Product?`)) return;

  try {
    const res = await fetch('/api/eresto/master-product/remove', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      showToast('info', `Product "${name}" dihapus dari master list.`);
      allMasterProducts = data.products || [];
      const query = searchMasterProd ? searchMasterProd.value.trim().toLowerCase() : '';
      if (query) {
        renderMasterProducts(allMasterProducts.filter(p => p.toLowerCase().includes(query)));
      } else {
        renderMasterProducts(allMasterProducts);
      }
    } else {
      showToast('error', data.message || 'Gagal menghapus product');
    }
  } catch (err) {
    console.error(err);
    showToast('error', 'Gagal menghapus product.');
  }
}

// Save Order
if (saveOrderBtn) {
  saveOrderBtn.addEventListener('click', async () => {
    if (searchMasterProd && searchMasterProd.value.trim()) {
      showToast('warning', 'Bersihkan kolom pencarian sebelum menyimpan urutan.');
      return;
    }
    const listItems = [...masterProductsList.querySelectorAll('.master-item')];
    const products = listItems.map((item) => item.dataset.name);

    try {
      const res = await fetch('/api/eresto/master-product', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ products }),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        showToast('success', 'Urutan Master Product berhasil disimpan!');
        allMasterProducts = data.products || [];
        renderMasterProducts(allMasterProducts);
      } else {
        showToast('error', data.message || 'Gagal menyimpan urutan');
      }
    } catch (err) {
      console.error(err);
      showToast('error', 'Gagal menyimpan urutan product.');
    }
  });
}

// Initialize on page load
loadMasterProductsList();
