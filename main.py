#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - Aplicación de Escritorio Nativa en Python + PySide6 (Qt6).
Características implementadas:
- Ejecución 100% local y sin necesidad de conexión a Internet (Offline-First).
- Lectura, edición, filtrado, importación y exportación de archivos JSON y CSV almacenados en la computadora.
- Uso de recursos del equipo monitoreados en tiempo real mediante Worker Service (QThread).
- Gestor de respaldos y actualizaciones locales integrado con manifest.json.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from models import LocalDataManager
from worker_service import DesktopWorkerService, SystemResourceCollector, PYSIDE6_AVAILABLE

if PYSIDE6_AVAILABLE:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QAction, QColor, QFont, QIcon
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPlainTextEdit,
        QProgressBar,
        QPushButton,
        QSpinBox,
        QSplitter,
        QStatusBar,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )


APP_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: 'Segoe UI', 'Noto Sans', sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #1e293b;
    background-color: #0f172a;
    border-radius: 8px;
}
QTabBar::tab {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 10px 18px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background-color: #2563eb;
    color: #ffffff;
}
QGroupBox {
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 14px;
    background-color: #1e293b;
    font-weight: bold;
    color: #38bdf8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {
    background-color: #0f172a;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f8fafc;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus {
    border: 1px solid #38bdf8;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton#btnSuccess {
    background-color: #16a34a;
}
QPushButton#btnSuccess:hover {
    background-color: #15803d;
}
QPushButton#btnDanger {
    background-color: #dc2626;
}
QPushButton#btnDanger:hover {
    background-color: #b91c1c;
}
QPushButton#btnSecondary {
    background-color: #475569;
}
QPushButton#btnSecondary:hover {
    background-color: #334155;
}
QTableWidget {
    background-color: #1e293b;
    alternate-background-color: #0f172a;
    gridline-color: #334155;
    border: 1px solid #334155;
    border-radius: 8px;
    color: #f8fafc;
}
QHeaderView::section {
    background-color: #0f172a;
    color: #38bdf8;
    font-weight: bold;
    padding: 8px;
    border: 1px solid #334155;
}
QProgressBar {
    border: 1px solid #334155;
    border-radius: 6px;
    text-align: center;
    background-color: #0f172a;
    color: #ffffff;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #0284c7;
    border-radius: 5px;
}
"""


if PYSIDE6_AVAILABLE:
    class DesktopMainWindow(QMainWindow):
        """Ventana principal de la aplicación de escritorio en PySide6."""

        def __init__(self, data_manager: LocalDataManager):
            super().__init__()
            self.data_manager = data_manager
            self.manifest = self.data_manager.load_manifest()
            self.records: List[Dict] = self.data_manager.load_from_json()
            self.filtered_records: List[Dict] = list(self.records)

            app_title = self.manifest.get("name", "DeskData Pro - App de Escritorio")
            version = self.manifest.get("version", "2.1.0")
            self.setWindowTitle(f"{app_title} v{version} [Modo Local Offline]")
            self.resize(1220, 760)

            icon_path = self.data_manager.base_dir / "icons" / "app_icon.png"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))

            self.setStyleSheet(APP_STYLESHEET)
            self._build_ui()
            self._refresh_table()
            self._update_kpi_cards()

            # Iniciar el Worker Service en segundo plano
            self.worker = DesktopWorkerService(self.data_manager, interval_sec=2.0, parent=self)
            self.worker.metrics_updated.connect(self._on_metrics_updated)
            self.worker.service_log.connect(self._append_service_log)
            self.worker.backup_completed.connect(
                lambda name: self.statusBar().showMessage(f"Respaldo automático creado: {name}", 5000)
            )
            self.worker.start()

        def _build_ui(self) -> None:
            central = QWidget()
            self.setCentralWidget(central)
            main_layout = QVBoxLayout(central)
            main_layout.setContentsMargins(14, 14, 14, 14)
            main_layout.setSpacing(10)

            # Encabezado superior con estado del sistema y modo sin Internet
            header_frame = QFrame()
            header_frame.setStyleSheet(
                "background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 8px;"
            )
            header_layout = QHBoxLayout(header_frame)

            title_box = QVBoxLayout()
            self.lbl_app_title = QLabel(
                f"🖥️ {self.manifest.get('name', 'DeskData Pro')} — Ejecución Local"
            )
            self.lbl_app_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #38bdf8;")
            self.lbl_subtitle = QLabel(
                "Python + PySide6 (Qt) | Almacenamiento Local JSON y CSV | Funciona 100% sin Internet"
            )
            self.lbl_subtitle.setStyleSheet("color: #94a3b8; font-size: 12px;")
            title_box.addWidget(self.lbl_app_title)
            title_box.addWidget(self.lbl_subtitle)
            header_layout.addLayout(title_box)
            header_layout.addStretch()

            self.lbl_version_badge = QLabel(f"Versión Local: v{self.manifest.get('version', '2.1.0')} | OFFLINE ACTIVO")
            self.lbl_version_badge.setStyleSheet(
                "background-color: #065f46; color: #a7f3d0; padding: 6px 12px; border-radius: 6px; font-weight: bold;"
            )
            header_layout.addWidget(self.lbl_version_badge)
            main_layout.addWidget(header_frame)

            # Tarjetas de resumen (KPIs)
            kpi_layout = QHBoxLayout()
            self.lbl_kpi_total = self._create_kpi_card(kpi_layout, "Registros Locales", "0")
            self.lbl_kpi_units = self._create_kpi_card(kpi_layout, "Unidades Totales", "0")
            self.lbl_kpi_value = self._create_kpi_card(kpi_layout, "Valor Estimado (MXN)", "$0.00")
            self.lbl_kpi_alerts = self._create_kpi_card(kpi_layout, "Alertas Bajo Stock", "0")
            main_layout.addLayout(kpi_layout)

            # Pestañas principales
            self.tabs = QTabWidget()
            main_layout.addWidget(self.tabs)

            self._build_tab_crud()
            self._build_tab_resources()
            self._build_tab_manifest_updater()

            self.setStatusBar(QStatusBar())
            self.statusBar().showMessage(
                f"Base de datos local activa: {self.data_manager.json_path}"
            )

        def _create_kpi_card(self, parent_layout: QHBoxLayout, title: str, initial_val: str) -> QLabel:
            card = QFrame()
            card.setStyleSheet(
                "background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 8px;"
            )
            v_layout = QVBoxLayout(card)
            lbl_t = QLabel(title)
            lbl_t.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
            lbl_v = QLabel(initial_val)
            lbl_v.setStyleSheet("color: #f8fafc; font-size: 18px; font-weight: bold;")
            v_layout.addWidget(lbl_t)
            v_layout.addWidget(lbl_v)
            parent_layout.addWidget(card)
            return lbl_v

        def _build_tab_crud(self) -> None:
            tab = QWidget()
            layout = QHBoxLayout(tab)

            # Panel izquierdo: Formulario de edición/registro
            form_group = QGroupBox("Formulario de Registro Local (JSON / CSV)")
            form_group.setFixedWidth(360)
            form_layout = QFormLayout(form_group)

            self.inp_id = QLineEdit()
            self.inp_id.setPlaceholderText("Ej. INV-006")
            self.inp_nombre = QLineEdit()
            self.inp_nombre.setPlaceholderText("Nombre del recurso o herramienta")
            self.inp_categoria = QComboBox()
            self.inp_categoria.addItems(["Hardware", "Software", "Periféricos", "Almacenamiento", "Componentes", "Redes"])
            self.inp_estado = QComboBox()
            self.inp_estado.addItems(["Activo", "Mantenimiento", "Bajo Stock", "Archivado"])
            self.inp_cantidad = QSpinBox()
            self.inp_cantidad.setRange(0, 999999)
            self.inp_cantidad.setValue(1)
            self.inp_precio = QDoubleSpinBox()
            self.inp_precio.setRange(0.0, 99999999.99)
            self.inp_precio.setDecimals(2)
            self.inp_precio.setValue(1500.00)
            self.inp_ubicacion = QLineEdit()
            self.inp_ubicacion.setPlaceholderText("Ubicación física o carpeta local")
            self.inp_notas = QPlainTextEdit()
            self.inp_notas.setFixedHeight(70)
            self.inp_notas.setPlaceholderText("Notas técnicas o especificaciones...")

            form_layout.addRow("Código ID:", self.inp_id)
            form_layout.addRow("Nombre:", self.inp_nombre)
            form_layout.addRow("Categoría:", self.inp_categoria)
            form_layout.addRow("Estado:", self.inp_estado)
            form_layout.addRow("Cantidad:", self.inp_cantidad)
            form_layout.addRow("Precio Unit. ($):", self.inp_precio)
            form_layout.addRow("Ubicación:", self.inp_ubicacion)
            form_layout.addRow("Notas:", self.inp_notas)

            btn_save = QPushButton("💾 Guardar / Actualizar Registro")
            btn_save.setObjectName("btnSuccess")
            btn_save.clicked.connect(self._save_or_update_record)

            btn_clear = QPushButton("🧹 Limpiar Formulario")
            btn_clear.setObjectName("btnSecondary")
            btn_clear.clicked.connect(self._clear_form)

            btn_delete = QPushButton("🗑️ Eliminar Seleccionado")
            btn_delete.setObjectName("btnDanger")
            btn_delete.clicked.connect(self._delete_selected_record)

            form_layout.addRow(btn_save)
            form_layout.addRow(btn_clear)
            form_layout.addRow(btn_delete)
            layout.addWidget(form_group)

            # Panel derecho: Buscador, botones de archivos locales y tabla
            right_panel = QVBoxLayout()

            toolbar_layout = QHBoxLayout()
            self.inp_search = QLineEdit()
            self.inp_search.setPlaceholderText("🔍 Buscar por ID, nombre, categoría o ubicación...")
            self.inp_search.textChanged.connect(self._apply_filter)

            self.cmb_filter_cat = QComboBox()
            self.cmb_filter_cat.addItems(["Todas las categorías", "Hardware", "Software", "Periféricos", "Almacenamiento", "Componentes", "Redes"])
            self.cmb_filter_cat.currentTextChanged.connect(self._apply_filter)

            btn_import_csv = QPushButton("📂 Importar CSV")
            btn_import_csv.clicked.connect(self._import_csv_dialog)

            btn_export_csv = QPushButton("📊 Exportar CSV")
            btn_export_csv.clicked.connect(self._export_csv_dialog)

            btn_import_json = QPushButton("📥 Cargar JSON")
            btn_import_json.clicked.connect(self._import_json_dialog)

            btn_export_json = QPushButton("📤 Guardar JSON")
            btn_export_json.clicked.connect(self._export_json_dialog)

            toolbar_layout.addWidget(self.inp_search, stretch=2)
            toolbar_layout.addWidget(self.cmb_filter_cat, stretch=1)
            toolbar_layout.addWidget(btn_import_csv)
            toolbar_layout.addWidget(btn_export_csv)
            toolbar_layout.addWidget(btn_import_json)
            toolbar_layout.addWidget(btn_export_json)
            right_panel.addLayout(toolbar_layout)

            self.table = QTableWidget(0, 8)
            self.table.setHorizontalHeaderLabels([
                "ID", "Nombre", "Categoría", "Estado", "Cantidad", "Precio Unit.", "Ubicación", "Actualizado"
            ])
            self.table.setAlternatingRowColors(True)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.itemSelectionChanged.connect(self._on_table_selection)
            right_panel.addWidget(self.table)

            layout.addLayout(right_panel, stretch=1)
            self.tabs.addTab(tab, "📁 Gestión de Archivos JSON y CSV")

        def _build_tab_resources(self) -> None:
            tab = QWidget()
            layout = QVBoxLayout(tab)

            res_group = QGroupBox("Monitoreo en Tiempo Real de Recursos del Equipo (Worker Service Local)")
            grid = QGridLayout(res_group)

            self.lbl_os_info = QLabel("Sistema Operativo: Detectando...")
            self.lbl_host_info = QLabel("Equipo Local: Detectando...")
            self.lbl_cpu_cores = QLabel("Núcleos de Procesador: --")
            self.lbl_disk_details = QLabel("Almacenamiento en Disco: --")

            grid.addWidget(self.lbl_os_info, 0, 0)
            grid.addWidget(self.lbl_host_info, 0, 1)
            grid.addWidget(self.lbl_cpu_cores, 1, 0)
            grid.addWidget(self.lbl_disk_details, 1, 1)

            self.bar_cpu = QProgressBar()
            self.bar_ram = QProgressBar()
            self.bar_disk = QProgressBar()

            grid.addWidget(QLabel("Carga de CPU del Equipo:"), 2, 0)
            grid.addWidget(self.bar_cpu, 2, 1)
            grid.addWidget(QLabel("Uso de Memoria RAM Local:"), 3, 0)
            grid.addWidget(self.bar_ram, 3, 1)
            grid.addWidget(QLabel("Uso de Disco Local:"), 4, 0)
            grid.addWidget(self.bar_disk, 4, 1)

            layout.addWidget(res_group)

            log_group = QGroupBox("Bitácora del Servicio de Trabajo Local (worker_service.py)")
            log_layout = QVBoxLayout(log_group)
            self.txt_service_log = QPlainTextEdit()
            self.txt_service_log.setReadOnly(True)
            log_layout.addWidget(self.txt_service_log)

            btn_force_backup = QPushButton("🛡️ Crear Respaldo Local Inmediato (.json)")
            btn_force_backup.clicked.connect(self._manual_backup)
            log_layout.addWidget(btn_force_backup)

            layout.addWidget(log_group)
            self.tabs.addTab(tab, "⚙️ Recursos del Equipo y Worker Service")

        def _build_tab_manifest_updater(self) -> None:
            tab = QWidget()
            layout = QHBoxLayout(tab)

            manifest_group = QGroupBox("Manifiesto de la Aplicación (manifest.json)")
            m_layout = QVBoxLayout(manifest_group)
            self.txt_manifest = QPlainTextEdit()
            self.txt_manifest.setReadOnly(True)
            self.txt_manifest.setPlainText(json.dumps(self.manifest, ensure_ascii=False, indent=2))
            m_layout.addWidget(self.txt_manifest)
            layout.addWidget(manifest_group)

            updater_group = QGroupBox("Gestor de Instalación y Actualizaciones Locales")
            u_layout = QVBoxLayout(updater_group)
            info_lbl = QLabel(
                "Características de la Arquitectura de Escritorio:\n"
                "• Instalada directamente en la computadora para realizar funciones especializadas.\n"
                "• Se ejecuta localmente utilizando CPU, RAM y sistema de archivos del equipo.\n"
                "• Funciona 100% sin Internet y gestiona bases de datos en archivos JSON y CSV.\n"
                "• Soporta paquetes de actualización local sin depender de servidores externos."
            )
            info_lbl.setWordWrap(True)
            info_lbl.setStyleSheet("color: #cbd5e1; line-height: 1.5; padding: 6px;")
            u_layout.addWidget(info_lbl)

            btn_sim_update = QPushButton("🔄 Aplicar Paquete de Actualización Local (datos/actualizacion_local.json)")
            btn_sim_update.setObjectName("btnSuccess")
            btn_sim_update.clicked.connect(self._apply_local_update)
            u_layout.addWidget(btn_sim_update)

            self.txt_update_log = QPlainTextEdit()
            self.txt_update_log.setReadOnly(True)
            self.txt_update_log.setPlainText(
                "Estado del actualizador local: Listo para verificar paquetes en disco."
            )
            u_layout.addWidget(self.txt_update_log)

            layout.addWidget(updater_group)
            self.tabs.addTab(tab, "📦 Manifiesto y Actualizaciones Locales")

        def _refresh_table(self) -> None:
            self.table.setRowCount(0)
            for row_idx, rec in enumerate(self.filtered_records):
                self.table.insertRow(row_idx)
                values = [
                    rec.get("id", ""),
                    rec.get("nombre", ""),
                    rec.get("categoria", ""),
                    rec.get("estado", ""),
                    str(rec.get("cantidad", 0)),
                    f"${float(rec.get('precio_unitario', 0.0)):,.2f}",
                    rec.get("ubicacion", ""),
                    rec.get("ultima_actualizacion", ""),
                ]
                for col_idx, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    if col_idx in (4, 5):
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(row_idx, col_idx, item)

        def _update_kpi_cards(self) -> None:
            stats = self.data_manager.compute_statistics(self.records)
            self.lbl_kpi_total.setText(str(stats["total_registros"]))
            self.lbl_kpi_units.setText(f"{stats['total_unidades']:,}")
            self.lbl_kpi_value.setText(f"${stats['valor_inventario']:,.2f}")
            self.lbl_kpi_alerts.setText(str(stats["alertas_bajo_stock"]))

        def _apply_filter(self) -> None:
            query = self.inp_search.text().strip().lower()
            cat_filter = self.cmb_filter_cat.currentText()
            result = []
            for r in self.records:
                if cat_filter != "Todas las categorías" and r.get("categoria") != cat_filter:
                    continue
                searchable = f"{r.get('id','')} {r.get('nombre','')} {r.get('categoria','')} {r.get('ubicacion','')}".lower()
                if query and query not in searchable:
                    continue
                result.append(r)
            self.filtered_records = result
            self._refresh_table()

        def _on_table_selection(self) -> None:
            selected = self.table.selectedItems()
            if not selected:
                return
            row = selected[0].row()
            if 0 <= row < len(self.filtered_records):
                rec = self.filtered_records[row]
                self.inp_id.setText(rec.get("id", ""))
                self.inp_nombre.setText(rec.get("nombre", ""))
                self.inp_categoria.setCurrentText(rec.get("categoria", "Hardware"))
                self.inp_estado.setCurrentText(rec.get("estado", "Activo"))
                self.inp_cantidad.setValue(int(rec.get("cantidad", 0)))
                self.inp_precio.setValue(float(rec.get("precio_unitario", 0.0)))
                self.inp_ubicacion.setText(rec.get("ubicacion", ""))
                self.inp_notas.setPlainText(rec.get("notas", ""))

        def _save_or_update_record(self) -> None:
            rec_id = self.inp_id.text().strip()
            nombre = self.inp_nombre.text().strip()
            if not rec_id or not nombre:
                QMessageBox.warning(self, "Campos requeridos", "Por favor ingresa al menos el Código ID y el Nombre.")
                return

            new_rec = self.data_manager.normalize_record({
                "id": rec_id,
                "nombre": nombre,
                "categoria": self.inp_categoria.currentText(),
                "estado": self.inp_estado.currentText(),
                "cantidad": self.inp_cantidad.value(),
                "precio_unitario": self.inp_precio.value(),
                "ubicacion": self.inp_ubicacion.text().strip() or "Almacén Local",
                "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "notas": self.inp_notas.toPlainText().strip(),
            })

            updated = False
            for idx, existing in enumerate(self.records):
                if existing.get("id") == rec_id:
                    self.records[idx] = new_rec
                    updated = True
                    break
            if not updated:
                self.records.append(new_rec)

            self.data_manager.save_to_json(self.records)
            self.data_manager.export_to_csv(self.records)
            self._apply_filter()
            self._update_kpi_cards()
            action_msg = "actualizado" if updated else "agregado"
            self.statusBar().showMessage(f"Registro {rec_id} {action_msg} y sincronizado en JSON y CSV.", 5000)

        def _clear_form(self) -> None:
            self.inp_id.clear()
            self.inp_nombre.clear()
            self.inp_cantidad.setValue(1)
            self.inp_precio.setValue(1000.0)
            self.inp_ubicacion.clear()
            self.inp_notas.clear()
            self.table.clearSelection()

        def _delete_selected_record(self) -> None:
            rec_id = self.inp_id.text().strip()
            if not rec_id:
                QMessageBox.information(self, "Seleccionar registro", "Selecciona primero un registro de la tabla.")
                return
            before = len(self.records)
            self.records = [r for r in self.records if r.get("id") != rec_id]
            if len(self.records) < before:
                self.data_manager.save_to_json(self.records)
                self.data_manager.export_to_csv(self.records)
                self._clear_form()
                self._apply_filter()
                self._update_kpi_cards()
                self.statusBar().showMessage(f"Registro {rec_id} eliminado de los archivos locales.", 5000)

        def _import_csv_dialog(self) -> None:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Importar archivo CSV local", str(self.data_manager.data_dir), "Archivos CSV (*.csv)"
            )
            if file_path:
                imported = self.data_manager.import_from_csv(Path(file_path))
                if imported:
                    self.records = imported
                    self.data_manager.save_to_json(self.records)
                    self._apply_filter()
                    self._update_kpi_cards()
                    QMessageBox.information(
                        self, "Importación exitosa", f"Se importaron {len(imported)} registros desde el archivo CSV."
                    )

        def _export_csv_dialog(self) -> None:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exportar a archivo CSV local", str(self.data_manager.csv_path), "Archivos CSV (*.csv)"
            )
            if file_path:
                out = self.data_manager.export_to_csv(self.records, Path(file_path))
                QMessageBox.information(self, "Exportación CSV", f"Catálogo exportado correctamente en:\n{out}")

        def _import_json_dialog(self) -> None:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Cargar archivo JSON local", str(self.data_manager.data_dir), "Archivos JSON (*.json)"
            )
            if file_path:
                loaded = self.data_manager.load_from_json(Path(file_path))
                if loaded:
                    self.records = loaded
                    self.data_manager.save_to_json(self.records)
                    self._apply_filter()
                    self._update_kpi_cards()
                    QMessageBox.information(
                        self, "Carga JSON exitosa", f"Se cargaron {len(loaded)} registros desde el archivo JSON."
                    )

        def _export_json_dialog(self) -> None:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar archivo JSON local", str(self.data_manager.json_path), "Archivos JSON (*.json)"
            )
            if file_path:
                out = self.data_manager.save_to_json(self.records, Path(file_path))
                QMessageBox.information(self, "Guardado JSON", f"Base de datos guardada en:\n{out}")

        def _on_metrics_updated(self, snap: Dict) -> None:
            self.lbl_os_info.setText(f"Sistema Operativo: {snap['os_name']} ({snap['architecture']})")
            self.lbl_host_info.setText(f"Equipo: {snap['hostname']} | Python {snap['python_version']}")
            self.lbl_cpu_cores.setText(f"Núcleos Lógicos: {snap['cpu_cores']} | Hora Local: {snap['timestamp']}")
            self.lbl_disk_details.setText(
                f"Disco Local: {snap['disk_used_gb']} GB usados de {snap['disk_total_gb']} GB ({snap['disk_free_gb']} GB libres)"
            )
            self.bar_cpu.setValue(int(snap["cpu_percent"]))
            self.bar_ram.setValue(int(snap["ram_percent"]))
            self.bar_disk.setValue(int(snap["disk_percent"]))

        def _append_service_log(self, msg: str) -> None:
            self.txt_service_log.appendPlainText(msg)

        def _manual_backup(self) -> None:
            backup_path = self.data_manager.create_local_backup(self.records)
            self._append_service_log(
                f"[{datetime.now().strftime('%H:%M:%S')}] Respaldo manual guardado en: {backup_path}"
            )
            QMessageBox.information(self, "Respaldo Local", f"Copia de seguridad creada en:\n{backup_path}")

        def _apply_local_update(self) -> None:
            patch_path = self.data_manager.data_dir / "actualizacion_local.json"
            if not patch_path.exists():
                with open(patch_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "version": "2.2.0",
                            "release_notes": "Optimización del motor local JSON/CSV y mejoras en el Worker Service.",
                        },
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )
            res = self.worker.apply_local_update_package(patch_path)
            self.manifest = self.data_manager.load_manifest()
            self.txt_manifest.setPlainText(json.dumps(self.manifest, ensure_ascii=False, indent=2))
            self.lbl_version_badge.setText(f"Versión Local: v{res['version']} | OFFLINE ACTIVO")
            self.txt_update_log.appendPlainText(
                f"[{res['applied_at']}] Actualizado localmente a v{res['version']}: {res['release_notes']}"
            )
            QMessageBox.information(
                self,
                "Actualización Local Aplicada",
                f"La aplicación se actualizó localmente a la versión v{res['version']}.",
            )

        def closeEvent(self, event) -> None:
            if hasattr(self, "worker") and self.worker:
                self.worker.stop()
                self.worker.wait(1500)
            super().closeEvent(event)


def run_self_test() -> int:
    """Ejecuta una verificación completa de la lógica local (JSON, CSV, Worker Service y Manifiesto)."""
    print("=== Ejecutando verificación de lógica de DeskData Pro ===")
    manager = LocalDataManager()
    records = manager.load_from_json()
    assert len(records) >= 3, "Deben cargarse los registros iniciales desde JSON"
    csv_file = manager.export_to_csv(records)
    imported_csv = manager.import_from_csv(csv_file)
    assert len(imported_csv) == len(records), "La importación/exportación CSV debe preservar todos los registros"
    backup = manager.create_local_backup(records)
    assert backup.exists(), "Debe crearse el respaldo local JSON"
    stats = manager.compute_statistics(records)
    snap = SystemResourceCollector.get_system_snapshot(manager.base_dir)
    print(f"Registros cargados (JSON/CSV): {stats['total_registros']} | Valor total: ${stats['valor_inventario']:,.2f}")
    print(f"Recursos detectados: SO={snap['os_name']} | CPU={snap['cpu_cores']} núcleos | Disco libre={snap['disk_free_gb']} GB")
    print("=== Verificación completada exitosamente ===")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="DeskData Pro - Aplicación de Escritorio (Python + PySide6)")
    parser.add_argument("--self-test", action="store_true", help="Ejecuta pruebas diagnósticas de la lógica JSON/CSV y Worker")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    if not PYSIDE6_AVAILABLE:
        print("Aviso: PySide6 no está instalado en este entorno. Ejecutando verificación de lógica en consola...")
        print("Para instalar la interfaz gráfica ejecuta: pip install -r requirements.txt")
        return run_self_test()

    app = QApplication(sys.argv)
    manager = LocalDataManager()
    window = DesktopMainWindow(manager)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
