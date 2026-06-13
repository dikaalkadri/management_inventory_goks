/* Front-end Logic for eResto Sales Analysis Automation V1 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const activeFileBox = document.getElementById("activeFileBox");
  const uploadedFileName = document.getElementById("uploadedFileName");
  const uploadedFileSize = document.getElementById("uploadedFileSize");
  const removeFileBtn = document.getElementById("removeFileBtn");

  const previewCard = document.getElementById("previewCard");
  const previewTableBody = document.getElementById("previewTableBody");
  const statRawRows = document.getElementById("statRawRows");
  const statCleanRows = document.getElementById("statCleanRows");
  const statUniqueProds = document.getElementById("statUniqueProds");
  const statDateRange = document.getElementById("statDateRange");

  const processCard = document.getElementById("processCard");
  const processBtn = document.getElementById("processBtn");
  const selectOutlet = document.getElementById("selectOutlet");
  const selectMonth = document.getElementById("selectMonth");
  const selectYear = document.getElementById("selectYear");

  const downloadCard = document.getElementById("downloadCard");
  const downloadLink = document.getElementById("downloadLink");
  const resetBtn = document.getElementById("resetBtn");

  const masterProductsList = document.getElementById("masterProductsList");
  const newProdName = document.getElementById("newProdName");
  const addProdBtn = document.getElementById("addProdBtn");
  const saveOrderBtn = document.getElementById("saveOrderBtn");

  // App state
  let activeFileId = null;
  let outletsList = [];

  // Toast Alert Helper
  function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    let icon = '<i class="fa-solid fa-circle-info"></i>';
    if (type === "success") icon = '<i class="fa-solid fa-circle-check"></i>';
    if (type === "danger")
      icon = '<i class="fa-solid fa-triangle-exclamation"></i>';

    toast.innerHTML = `${icon}<span>${message}</span>`;
    container.appendChild(toast);

    // Trigger reflow
    toast.offsetHeight;
    toast.classList.add("show");

    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // ─── FILE DRAG & DROP & UPLOAD ──────────────────────────────────────────

  // Trigger click on click dropzone
  dropZone.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  });

  // Drag events
  ["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(
      eventName,
      (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
      },
      false,
    );
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(
      eventName,
      (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
      },
      false,
    );
  });

  dropZone.addEventListener("drop", (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      fileInput.files = files;
      handleFileUpload(files[0]);
    }
  });

  // Reset all stages
  function resetUploadState() {
    activeFileId = null;
    fileInput.value = "";
    activeFileBox.style.display = "none";
    dropZone.style.display = "block";
    previewCard.style.display = "none";
    processCard.style.display = "none";
    downloadCard.style.display = "none";
    previewTableBody.innerHTML = "";
  }

  removeFileBtn.addEventListener("click", resetUploadState);
  resetBtn.addEventListener("click", resetUploadState);

  // Ajax upload file to backend
  function handleFileUpload(file) {
    // Simple client-side size check (50MB)
    if (file.size > 50 * 1024 * 1024) {
      showToast("Ukuran file terlalu besar! Maksimal 50MB.", "danger");
      return;
    }

    // Show loading toast
    showToast("Mengunggah dan merapikan data eResto...", "info");

    // Form data packaging
    const formData = new FormData();
    formData.append("file", file);

    // UI upload visual transition
    dropZone.style.display = "none";
    activeFileBox.style.display = "flex";
    uploadedFileName.textContent = file.name;
    uploadedFileSize.textContent = (file.size / 1024).toFixed(1) + " KB";

    fetch("/api/eresto/upload", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "ok") {
          activeFileId = data.file_id;
          showToast("Data berhasil dibersihkan & divalidasi!", "success");
          renderPreview(data);
        } else {
          showToast(data.message || "Gagal membersihkan data", "danger");
          resetUploadState();
        }
      })
      .catch((error) => {
        console.error("Error uploading:", error);
        showToast("Kesalahan koneksi ke server saat memproses file.", "danger");
        resetUploadState();
      });
  }

  // Dynamic render of preview records
  function renderPreview(data) {
    statRawRows.textContent = data.total_rows_raw;
    statCleanRows.textContent = data.total_rows_clean;
    statUniqueProds.textContent = data.unique_products_count;
    statDateRange.textContent = data.date_range[0]
      ? `${data.date_range[0]} s/d ${data.date_range[1]}`
      : "-";

    // Auto select Month & Year based on date range if available
    if (data.date_range[0]) {
      // Get Month number from first clean date e.g. "01/05/2026"
      const parts = data.date_range[0].split("/");
      if (parts.length === 3) {
        const rawMonth = parseInt(parts[1], 10);
        const rawYear = parts[2];

        selectMonth.value = rawMonth;
        selectYear.value = rawYear;
      }
    }

    // Auto select Outlet based on uploaded filename if possible
    if (data.filename && outletsList.length > 0) {
      const fnLower = data.filename.toLowerCase();
      const matchedOutlet = outletsList.find((outlet) => {
        const cleanName = outlet.includes(".")
          ? outlet.split(".").pop().trim().toLowerCase()
          : outlet.trim().toLowerCase();
        return fnLower.includes(cleanName);
      });
      if (matchedOutlet) {
        selectOutlet.value = matchedOutlet;
        showToast(
          `Outlet "${matchedOutlet}" otomatis terdeteksi dari nama file!`,
          "success",
        );
      } else {
        selectOutlet.value = "";
      }
    } else {
      selectOutlet.value = "";
    }

    previewTableBody.innerHTML = "";
    data.preview_rows.forEach((row) => {
      const tr = document.createElement("tr");

      // Format order date
      const dateCell = document.createElement("td");
      dateCell.textContent = row[data.preview_cols[0]] || "";

      const prodCell = document.createElement("td");
      prodCell.textContent = row[data.preview_cols[1]] || "";
      prodCell.style.fontWeight = "600";

      const qtyCell = document.createElement("td");
      qtyCell.textContent = row[data.preview_cols[2]] || "0";
      qtyCell.style.textAlign = "center";
      qtyCell.style.color = "var(--color-emerald-light)";

      tr.appendChild(dateCell);
      tr.appendChild(prodCell);
      tr.appendChild(qtyCell);
      previewTableBody.appendChild(tr);
    });

    // Show steps cards
    previewCard.style.display = "block";
    processCard.style.display = "block";
    previewCard.scrollIntoView({ behavior: "smooth" });
  }

  // ─── EXCEL MATRIX GENERATOR ──────────────────────────────────────────────

  processBtn.addEventListener("click", () => {
    if (!activeFileId) {
      showToast("Unggah file excel terlebih dahulu!", "danger");
      return;
    }

    const outlet = selectOutlet.value;
    if (!outlet) {
      showToast("Pilih outlet terlebih dahulu!", "danger");
      selectOutlet.focus();
      return;
    }

    const month = selectMonth.value;
    const year = selectYear.value;

    showToast("Sedang membuat formula SUMIFS dan menata styling...", "info");
    processBtn.disabled = true;
    processBtn.querySelector("span").textContent = "Memproses data...";

    fetch("/api/eresto/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_id: activeFileId,
        month: month,
        year: year,
        outlet: outlet,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        processBtn.disabled = false;
        processBtn.querySelector("span").textContent =
          "Proses & Generate Analisa Penjualan";

        if (data.status === "ok") {
          showToast(data.message, "success");

          // Show download link
          downloadLink.href = data.download_url;

          previewCard.style.display = "none";
          processCard.style.display = "none";
          downloadCard.style.display = "block";
          downloadCard.scrollIntoView({ behavior: "smooth" });
        } else {
          showToast(data.message || "Gagal memproses excel", "danger");
        }
      })
      .catch((error) => {
        console.error("Error processing:", error);
        processBtn.disabled = false;
        processBtn.querySelector("span").textContent =
          "Proses & Generate Analisa Penjualan";
        showToast("Koneksi server terputus saat generate excel.", "danger");
      });
  });

  // ─── MASTER PRODUCT MANAGER (DRAG AND DROP REORDER) ──────────────────────

  // Fetch and load products
  function loadMasterProductsList() {
    fetch("/api/eresto/master-product")
      .then((res) => res.json())
      .then((data) => {
        renderMasterProducts(data.products);
      })
      .catch((err) => console.error("Failed to load master products:", err));
  }

  function renderMasterProducts(products) {
    masterProductsList.innerHTML = "";
    products.forEach((prod) => {
      const li = document.createElement("li");
      li.className = "master-item";
      li.draggable = true;
      li.dataset.name = prod;

      li.innerHTML = `
                <div class="item-left">
                    <i class="fa-solid fa-grip-vertical drag-handle"></i>
                    <span>${prod}</span>
                </div>
                <button class="btn-remove-prod" title="Hapus Product">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            `;

      // Drag and drop listeners
      setupDragAndDropItem(li);

      // Delete button listener
      li.querySelector(".btn-remove-prod").addEventListener("click", () => {
        removeProductItem(prod);
      });

      masterProductsList.appendChild(li);
    });
  }

  // Drag items listeners setup
  function setupDragAndDropItem(item) {
    item.addEventListener("dragstart", () => {
      item.classList.add("dragging");
    });

    item.addEventListener("dragend", () => {
      item.classList.remove("dragging");
    });
  }

  // Handle dragover container reordering logic
  masterProductsList.addEventListener("dragover", (e) => {
    e.preventDefault();
    const afterElement = getDragAfterElement(masterProductsList, e.clientY);
    const dragging = document.querySelector(".dragging");
    if (afterElement == null) {
      masterProductsList.appendChild(dragging);
    } else {
      masterProductsList.insertBefore(dragging, afterElement);
    }
  });

  function getDragAfterElement(container, y) {
    const draggableElements = [
      ...container.querySelectorAll(".master-item:not(.dragging)"),
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

  // Add product
  addProdBtn.addEventListener("click", () => {
    const name = newProdName.value.trim();
    if (!name) return;

    fetch("/api/eresto/master-product/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "ok") {
          showToast(`Product "${name}" berhasil ditambahkan!`, "success");
          newProdName.value = "";
          renderMasterProducts(data.products);
        } else {
          showToast(data.message || "Gagal menambahkan product", "danger");
        }
      })
      .catch((err) => {
        console.error(err);
        showToast("Gagal terhubung dengan database product.", "danger");
      });
  });

  newProdName.addEventListener("keydown", (e) => {
    if (e.key === "Enter") addProdBtn.click();
  });

  // Remove product
  function removeProductItem(name) {
    fetch("/api/eresto/master-product/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "ok") {
          showToast(`Product "${name}" dihapus dari master list.`, "info");
          renderMasterProducts(data.products);
        }
      })
      .catch((err) => console.error(err));
  }

  // Save ordering
  saveOrderBtn.addEventListener("click", () => {
    const listItems = [...masterProductsList.querySelectorAll(".master-item")];
    const products = listItems.map((item) => item.dataset.name);

    fetch("/api/eresto/master-product", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ products: products }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "ok") {
          showToast("Urutan Master Product berhasil disimpan!", "success");
          renderMasterProducts(data.products);
        }
      })
      .catch((err) => {
        console.error(err);
        showToast("Gagal menyimpan urutan product.", "danger");
      });
  });

  // Load outlets list for the dropdown
  function loadOutletsList() {
    fetch("/api/config")
      .then((res) => res.json())
      .then((data) => {
        if (data.outlets && data.outlets.length > 0) {
          outletsList = data.outlets;
          selectOutlet.innerHTML =
            '<option value="">-- Pilih Outlet --</option>';
          outletsList.forEach((outlet) => {
            const opt = document.createElement("option");
            opt.value = outlet;
            opt.textContent = outlet;
            selectOutlet.appendChild(opt);
          });
        }
      })
      .catch((err) => console.error("Failed to load outlets:", err));
  }
  loadOutletsList();

  // Initial Load of master products
  loadMasterProductsList();
});
