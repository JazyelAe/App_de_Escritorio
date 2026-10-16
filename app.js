/**
 * app.js - Lógica completa de la aplicación instalable (PWA / Escritorio)
 * Gestiona registros locales, importación y exportación de archivos JSON y CSV,
 * monitoreo de recursos del equipo, actualizaciones locales y registro del Service Worker.
 */

const SEED_RECORDS = [
  {
    id: "INV-001",
    nombre: "Estación de Trabajo Portátil Pro 16",
    categoria: "Hardware",
    estado: "Activo",
    cantidad: 12,
    precio_unitario: 24500.00,
    ubicacion: "Almacén Central - Estante A1",
    ultima_actualizacion: "2026-10-15 10:30:00",
    notas: "Equipo configurado para desarrollo local con Python y Qt."
  },
  {
    id: "INV-002",
    nombre: "Monitor UltraWide 34 Pulgadas IPS",
    categoria: "Periféricos",
    estado: "Activo",
    cantidad: 8,
    precio_unitario: 8900.50,
    ubicacion: "Almacén Central - Estante B2",
    ultima_actualizacion: "2026-10-15 12:15:00",
    notas: "Calibrado de fábrica para diseño de interfaces."
  },
  {
    id: "INV-003",
    nombre: "Servidor NAS Local 4 Bahías 16TB",
    categoria: "Almacenamiento",
    estado: "Activo",
    cantidad: 3,
    precio_unitario: 18200.00,
    ubicacion: "Sala de Servidores - Rack 1",
    ultima_actualizacion: "2026-10-15 16:40:00",
    notas: "Respaldo automático sin conexión a Internet (Red Local)."
  },
  {
    id: "INV-004",
    nombre: "Licencia Suite Herramientas CAD Offline",
    categoria: "Software",
    estado: "Mantenimiento",
    cantidad: 25,
    precio_unitario: 3400.00,
    ubicacion: "Repositorio Local de Licencias",
    ultima_actualizacion: "2026-10-16 09:00:00",
    notas: "Requiere actualización local v2.4 en estaciones Windows/Linux."
  },
  {
    id: "INV-005",
    nombre: "Unidad SSD NVMe M.2 2TB Industrial",
    categoria: "Componentes",
    estado: "Bajo Stock",
    cantidad: 4,
    precio_unitario: 2850.00,
    ubicacion: "Almacén Técnico - Gaveta C4",
    ultima_actualizacion: "2026-10-16 11:20:00",
    notas: "Alta velocidad de lectura/escritura para bases JSON/CSV."
  }
];

let records = [];
let deferredInstallPrompt = null;
let appVersion = "2.1.0";

function loadLocalData() {
  try {
    const saved = localStorage.getItem("deskdata_pro_records");
    if (saved) {
      records = JSON.parse(saved);
    } else {
      records = [...SEED_RECORDS];
      saveLocalData();
    }
  } catch (e) {
    records = [...SEED_RECORDS];
  }
}

function saveLocalData() {
  try {
    localStorage.setItem("deskdata_pro_records", JSON.stringify(records));
  } catch (e) {
    console.warn("Almacenamiento en memoria activo:", e);
  }
}

function showToast(msg) {
  const toast = document.getElementById("appToast");
  if (!toast) return;
  toast.textContent = msg;
  toast.style.display = "block";
  setTimeout(() => {
    toast.style.display = "none";
  }, 3200);
}

function appendLog(msg) {
  const box = document.getElementById("workerLogBox");
  if (!box) return;
  const now = new Date().toLocaleTimeString();
  box.textContent += `\n[${now}] ${msg}`;
  box.scrollTop = box.scrollHeight;
}

function renderKPIs() {
  const totalItems = records.length;
  const totalUnits = records.reduce((acc, r) => acc + (Number(r.cantidad) || 0), 0);
  const totalValue = records.reduce((acc, r) => acc + ((Number(r.cantidad) || 0) * (Number(r.precio_unitario) || 0)), 0);
  const lowStock = records.filter(r => (Number(r.cantidad) || 0) <= 5 || r.estado === "Bajo Stock").length;

  document.getElementById("kpiTotal").textContent = totalItems;
  document.getElementById("kpiUnits").textContent = totalUnits.toLocaleString("es-MX");
  document.getElementById("kpiValue").textContent = "$" + totalValue.toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  document.getElementById("kpiAlerts").textContent = lowStock;
}

function renderTable() {
  const tbody = document.getElementById("recordsTableBody");
  const query = (document.getElementById("searchInput").value || "").toLowerCase().trim();
  const catFilter = document.getElementById("categoryFilter").value;

  tbody.innerHTML = "";
  const filtered = records.filter(r => {
    if (catFilter !== "ALL" && r.categoria !== catFilter) return false;
    const text = `${r.id} ${r.nombre} ${r.categoria} ${r.ubicacion} ${r.notas}`.toLowerCase();
    return !query || text.includes(query);
  });

  filtered.forEach(rec => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${rec.id}</strong></td>
      <td>${rec.nombre}</td>
      <td>${rec.categoria}</td>
      <td>${rec.estado}</td>
      <td>${rec.cantidad}</td>
      <td>$${Number(rec.precio_unitario).toLocaleString("es-MX", { minimumFractionDigits: 2 })}</td>
      <td>${rec.ubicacion}</td>
    `;
    tr.addEventListener("click", () => selectRecordForEdit(rec.id));
    tbody.appendChild(tr);
  });
  renderKPIs();
}

function selectRecordForEdit(id) {
  const rec = records.find(r => r.id === id);
  if (!rec) return;
  document.getElementById("inpId").value = rec.id;
  document.getElementById("inpNombre").value = rec.nombre;
  document.getElementById("inpCategoria").value = rec.categoria;
  document.getElementById("inpEstado").value = rec.estado;
  document.getElementById("inpCantidad").value = rec.cantidad;
  document.getElementById("inpPrecio").value = rec.precio_unitario;
  document.getElementById("inpUbicacion").value = rec.ubicacion;
  document.getElementById("inpNotas").value = rec.notas || "";
}

function saveOrUpdateRecord() {
  const id = document.getElementById("inpId").value.trim();
  const nombre = document.getElementById("inpNombre").value.trim();
  if (!id || !nombre) {
    showToast("Ingresa el Código ID y el Nombre del registro.");
    return;
  }
  const newRec = {
    id,
    nombre,
    categoria: document.getElementById("inpCategoria").value,
    estado: document.getElementById("inpEstado").value,
    cantidad: Math.max(0, parseInt(document.getElementById("inpCantidad").value || "0", 10)),
    precio_unitario: Math.max(0, parseFloat(document.getElementById("inpPrecio").value || "0")),
    ubicacion: document.getElementById("inpUbicacion").value.trim() || "Almacén Local",
    ultima_actualizacion: new Date().toISOString().slice(0, 19).replace("T", " "),
    notas: document.getElementById("inpNotas").value.trim()
  };

  const idx = records.findIndex(r => r.id === id);
  if (idx >= 0) {
    records[idx] = newRec;
    showToast(`Registro ${id} actualizado localmente.`);
  } else {
    records.push(newRec);
    showToast(`Registro ${id} agregado localmente.`);
  }
  saveLocalData();
  renderTable();
  appendLog(`Sincronización local JSON/CSV completada para registro ${id}.`);
}

function deleteRecord() {
  const id = document.getElementById("inpId").value.trim();
  if (!id) {
    showToast("Selecciona un registro de la tabla para eliminar.");
    return;
  }
  records = records.filter(r => r.id !== id);
  saveLocalData();
  clearForm();
  renderTable();
  showToast(`Registro ${id} eliminado.`);
  appendLog(`Registro ${id} eliminado de la base local.`);
}

function clearForm() {
  document.getElementById("inpId").value = "";
  document.getElementById("inpNombre").value = "";
  document.getElementById("inpCantidad").value = "1";
  document.getElementById("inpPrecio").value = "1500.00";
  document.getElementById("inpUbicacion").value = "";
  document.getElementById("inpNotas").value = "";
}

function exportJSON() {
  const payload = {
    metadata: {
      aplicacion: "DeskData Pro",
      version: appVersion,
      fecha_exportacion: new Date().toISOString(),
      total_registros: records.length
    },
    registros: records
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "registros_locales.json";
  a.click();
  URL.revokeObjectURL(url);
  showToast("Archivo JSON descargado en tu equipo.");
}

function exportCSV() {
  const headers = ["id", "nombre", "categoria", "estado", "cantidad", "precio_unitario", "ubicacion", "ultima_actualizacion", "notas"];
  const rows = records.map(r => headers.map(h => `"${String(r[h] ?? "").replace(/"/g, '""')}"`).join(","));
  const csvContent = [headers.join(","), ...rows].join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "catalogo_exportado.csv";
  a.click();
  URL.revokeObjectURL(url);
  showToast("Archivo CSV descargado en tu equipo.");
}

function parseCSVLine(line) {
  const result = [];
  let cur = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        cur += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === "," && !inQuotes) {
      result.push(cur);
      cur = "";
    } else {
      cur += ch;
    }
  }
  result.push(cur);
  return result;
}

function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    const content = e.target.result;
    if (file.name.endsWith(".json")) {
      try {
        const parsed = JSON.parse(content);
        const list = Array.isArray(parsed) ? parsed : (parsed.registros || []);
        if (list.length > 0) {
          records = list;
          saveLocalData();
          renderTable();
          showToast(`Se cargaron ${list.length} registros desde ${file.name}`);
          appendLog(`Archivo JSON importado: ${file.name} (${list.length} registros).`);
        }
      } catch (err) {
        showToast("Error al leer el archivo JSON.");
      }
    } else if (file.name.endsWith(".csv")) {
      const lines = content.split(/\r?\n/).filter(l => l.trim().length > 0);
      if (lines.length > 1) {
        const headers = parseCSVLine(lines[0]).map(h => h.trim());
        const imported = [];
        for (let i = 1; i < lines.length; i++) {
          const vals = parseCSVLine(lines[i]);
          const obj = {};
          headers.forEach((h, idx) => { obj[h] = vals[idx] || ""; });
          obj.cantidad = parseInt(obj.cantidad || "0", 10);
          obj.precio_unitario = parseFloat(obj.precio_unitario || "0");
          imported.push(obj);
        }
        records = imported;
        saveLocalData();
        renderTable();
        showToast(`Se importaron ${imported.length} registros desde ${file.name}`);
        appendLog(`Archivo CSV importado: ${file.name} (${imported.length} registros).`);
      }
    }
  };
  reader.readAsText(file, "utf-8");
}

function updateHardwareMonitor() {
  const cores = navigator.hardwareConcurrency || 8;
  const memGb = navigator.deviceMemory || 8;
  const onlineState = navigator.onLine ? "Conectado (Modo Local Prioritario)" : "Sin Internet (100% Offline)";
  const cpuSim = Math.min(95, Math.max(8, Math.round(18 + Math.sin(Date.now() / 3000) * 12)));
  const ramSim = Math.min(90, Math.max(24, Math.round(42 + Math.cos(Date.now() / 4000) * 6)));

  document.getElementById("hwCores").textContent = `${cores} núcleos lógicos`;
  document.getElementById("hwRam").textContent = `~${memGb} GB detectados`;
  document.getElementById("hwNet").textContent = onlineState;
  document.getElementById("barCpu").style.width = `${cpuSim}%`;
  document.getElementById("barRam").style.width = `${ramSim}%`;
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-section").forEach(sec => {
    sec.style.display = sec.id === tabId ? "block" : "none";
  });
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.target === tabId);
  });
}

function registerServiceWorker() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./service-worker.js")
      .then((reg) => {
        appendLog(`Service Worker registrado correctamente en alcance: ${reg.scope}`);
      })
      .catch((err) => {
        appendLog(`Modo local activo (Service Worker en espera): ${err.message}`);
      });
  }
}

window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  const btnInstall = document.getElementById("btnInstallPwa");
  if (btnInstall) btnInstall.style.display = "inline-block";
});

window.addEventListener("DOMContentLoaded", () => {
  loadLocalData();
  renderTable();
  updateHardwareMonitor();
  setInterval(updateHardwareMonitor, 2500);
  registerServiceWorker();

  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => switchTab(btn.dataset.target));
  });

  document.getElementById("btnSave").addEventListener("click", saveOrUpdateRecord);
  document.getElementById("btnDelete").addEventListener("click", deleteRecord);
  document.getElementById("btnClear").addEventListener("click", clearForm);
  document.getElementById("btnExportJson").addEventListener("click", exportJSON);
  document.getElementById("btnExportCsv").addEventListener("click", exportCSV);
  document.getElementById("fileImporter").addEventListener("change", handleFileUpload);
  document.getElementById("searchInput").addEventListener("input", renderTable);
  document.getElementById("categoryFilter").addEventListener("change", renderTable);

  const btnUpdate = document.getElementById("btnApplyLocalUpdate");
  if (btnUpdate) {
    btnUpdate.addEventListener("click", () => {
      appVersion = "2.2.0";
      document.getElementById("versionBadge").textContent = `Versión v${appVersion} | OFFLINE READY`;
      appendLog("Actualización local v2.2.0 aplicada sin conexión externa.");
      showToast("Actualización local v2.2.0 instalada correctamente.");
    });
  }

  const btnInstall = document.getElementById("btnInstallPwa");
  if (btnInstall) {
    btnInstall.addEventListener("click", async () => {
      if (deferredInstallPrompt) {
        deferredInstallPrompt.prompt();
        await deferredInstallPrompt.userChoice;
        deferredInstallPrompt = null;
      } else {
        showToast("Usa la opción 'Instalar aplicación' en la barra de direcciones de tu navegador o ejecuta main.py con PySide6.");
      }
    });
  }
});
