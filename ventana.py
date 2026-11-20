"""ventana.py — Ventana principal de DeskData Pro (PySide6 / Qt).

Pestañas: Inventario (alta, edición, eliminación, búsqueda e importar/exportar), Resumen (gráfica) y Equipo (recursos locales).
"""
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

import models
from grafica import GraficaBarras
from worker_service import MonitorEquipo, leer_equipo

VERSION = "1.0.0"
ESTILO = """
QMainWindow, QWidget { background:#0f172a; color:#f8fafc; font-family:'Segoe UI'; font-size:13px; }
QTabWidget::pane { border:1px solid #1e293b; border-radius:8px; }
QTabBar::tab { background:#1e293b; color:#94a3b8; padding:9px 20px; margin-right:4px; border-top-left-radius:6px;
               border-top-right-radius:6px; font-weight:bold; }
QTabBar::tab:selected { background:#2563eb; color:white; }
QGroupBox { border:1px solid #334155; border-radius:8px; margin-top:12px; padding-top:14px; background:#1e293b;
            font-weight:bold; color:#38bdf8; }
QGroupBox::title { subcontrol-origin:margin; left:12px; padding:0 6px; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit { background:#0f172a; border:1px solid #475569;
            border-radius:6px; padding:5px 8px; color:#f8fafc; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus { border:1px solid #38bdf8; }
QPushButton { background:#2563eb; color:white; border:none; border-radius:6px; padding:7px 12px; font-weight:bold; }
QPushButton:hover { background:#1d4ed8; }
QPushButton#verde { background:#16a34a; } QPushButton#rojo { background:#dc2626; } QPushButton#gris { background:#475569; }
QTableWidget { background:#1e293b; alternate-background-color:#172033; gridline-color:#334155; border:1px solid #334155;
               border-radius:6px; selection-background-color:#2563eb; }
QHeaderView::section { background:#0b1222; color:#38bdf8; padding:6px; border:none; font-weight:bold; }
QProgressBar { background:#0f172a; border:1px solid #334155; border-radius:6px; text-align:center; height:22px; }
QProgressBar::chunk { background:#0284c7; border-radius:5px; }
QStatusBar { color:#94a3b8; }
"""


class VentanaPrincipal(QMainWindow):
    def __init__(self, almacen: models.Almacen):
        super().__init__()
        self.almacen = almacen
        self.registros = almacen.cargar()
        self.editando_id: str | None = None   # None = modo "alta"; con un ID = modo "edición"

        self.setWindowTitle(f"DeskData Pro v{VERSION} · Inventario local")
        self.setWindowIcon(QIcon(str(models.ruta_recurso("icons/app_icon.png"))))
        self.resize(1280, 780)
        self.setStyleSheet(ESTILO)

        central = QWidget()
        self.setCentralWidget(central)
        diseno = QVBoxLayout(central)
        diseno.addWidget(self._encabezado())
        diseno.addLayout(self._tarjetas())
        self.pestanas = QTabWidget()
        self.pestanas.addTab(self._pestana_inventario(), "📦 Inventario")
        self.pestanas.addTab(self._pestana_resumen(), "📊 Resumen")
        self.pestanas.addTab(self._pestana_equipo(), "🖥️ Equipo")
        diseno.addWidget(self.pestanas)
        self.statusBar().showMessage(f"Datos guardados en {self.almacen.archivo}")

        self.refrescar()
        # Hilo en segundo plano para medir CPU, RAM y disco sin congelar la ventana.
        self.monitor = MonitorEquipo(str(Path(self.almacen.carpeta).anchor or "/"), parent=self)
        self.monitor.lectura.connect(self.mostrar_equipo)
        self.monitor.start()
        self.mostrar_equipo(leer_equipo(str(Path(self.almacen.carpeta).anchor or "/")))

    # ================== Construcción de la interfaz ==================
    def _encabezado(self) -> QFrame:
        marco = QFrame()
        marco.setStyleSheet("background:#1e293b; border:1px solid #334155; border-radius:8px;")
        fila = QHBoxLayout(marco)
        titulo = QLabel("🖥️ DeskData Pro <span style='color:#94a3b8; font-size:12px; font-weight:normal'>"
                        "— Inventario de equipo de cómputo · Python + PySide6</span>")
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color:#38bdf8; border:none;")
        insignia = QLabel("● Funciona sin Internet · datos locales")
        insignia.setStyleSheet("background:#065f46; color:#a7f3d0; padding:6px 12px; border-radius:6px; font-weight:bold;")
        fila.addWidget(titulo)
        fila.addStretch()
        fila.addWidget(insignia)
        return marco

    def _tarjetas(self) -> QHBoxLayout:
        fila = QHBoxLayout()
        self.kpi = {}
        for clave, titulo in [("registros", "Registros"), ("unidades", "Unidades totales"),
                              ("valor", "Valor del inventario (MXN)"), ("alertas", f"Bajo stock (≤ {models.BAJO_STOCK})")]:
            tarjeta = QFrame()
            tarjeta.setStyleSheet("background:#1e293b; border:1px solid #334155; border-radius:8px;")
            col = QVBoxLayout(tarjeta)
            etiqueta = QLabel(titulo)
            etiqueta.setStyleSheet("color:#94a3b8; font-size:11px; font-weight:bold; border:none;")
            valor = QLabel("0")
            valor.setStyleSheet("font-size:20px; font-weight:bold; border:none;")
            col.addWidget(etiqueta)
            col.addWidget(valor)
            fila.addWidget(tarjeta)
            self.kpi[clave] = valor
        return fila

    def _pestana_inventario(self) -> QWidget:
        pagina = QWidget()
        fila = QHBoxLayout(pagina)

        # ----- Formulario (izquierda) -----
        self.grupo_form = QGroupBox("Nuevo registro")
        self.grupo_form.setFixedWidth(340)
        form = QFormLayout(self.grupo_form)
        self.f_id = QLineEdit(placeholderText="Ej. INV-013")
        self.f_nombre = QLineEdit(placeholderText="Nombre del equipo o licencia")
        self.f_categoria = QComboBox()
        self.f_categoria.addItems(models.CATEGORIAS)
        self.f_estado = QComboBox()
        self.f_estado.addItems(models.ESTADOS)
        self.f_cantidad = QSpinBox(maximum=999999)
        self.f_precio = QDoubleSpinBox(maximum=9999999.99, decimals=2, prefix="$ ")
        self.f_ubicacion = QLineEdit(placeholderText="Almacén, laboratorio, rack…")
        self.f_notas = QPlainTextEdit(placeholderText="Notas (opcional)")
        self.f_notas.setFixedHeight(64)
        for etiqueta, campo in [("ID:", self.f_id), ("Nombre:", self.f_nombre), ("Categoría:", self.f_categoria),
                                ("Estado:", self.f_estado), ("Cantidad:", self.f_cantidad), ("Precio unitario:", self.f_precio),
                                ("Ubicación:", self.f_ubicacion), ("Notas:", self.f_notas)]:
            form.addRow(etiqueta, campo)
        b_guardar = QPushButton("💾 Guardar", objectName="verde", clicked=self.guardar_formulario)
        b_nuevo = QPushButton("➕ Nuevo (limpiar)", objectName="gris", clicked=self.limpiar_formulario)
        self.b_eliminar = QPushButton("🗑️ Eliminar seleccionado", objectName="rojo", clicked=self.eliminar_seleccionado)
        for b in (b_guardar, b_nuevo, self.b_eliminar):
            form.addRow(b)
        fila.addWidget(self.grupo_form)

        # ----- Barra de búsqueda, archivos y tabla (derecha) -----
        derecha = QVBoxLayout()
        barra = QHBoxLayout()
        self.buscador = QLineEdit(placeholderText="🔎 Buscar por ID, nombre o ubicación…", textChanged=self.refrescar_tabla)
        self.filtro_cat = QComboBox()
        self.filtro_cat.addItems(["Todas"] + models.CATEGORIAS)
        self.filtro_cat.currentTextChanged.connect(self.refrescar_tabla)
        self.filtro_est = QComboBox()
        self.filtro_est.addItems(["Todos"] + models.ESTADOS)
        self.filtro_est.currentTextChanged.connect(self.refrescar_tabla)
        self.contador = QLabel()
        self.contador.setStyleSheet("color:#94a3b8;")
        barra.addWidget(self.buscador, 3)
        barra.addWidget(QLabel("Categoría:"))
        barra.addWidget(self.filtro_cat, 1)
        barra.addWidget(QLabel("Estado:"))
        barra.addWidget(self.filtro_est, 1)
        barra.addWidget(self.contador)
        derecha.addLayout(barra)

        archivos = QHBoxLayout()
        archivos.addWidget(QPushButton("📂 Importar CSV", clicked=lambda: self.importar("csv")))
        archivos.addWidget(QPushButton("📊 Exportar CSV", clicked=lambda: self.exportar("csv")))
        archivos.addWidget(QPushButton("📥 Importar JSON", clicked=lambda: self.importar("json")))
        archivos.addWidget(QPushButton("📤 Exportar JSON", clicked=lambda: self.exportar("json")))
        archivos.addStretch()
        derecha.addLayout(archivos)

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Categoría", "Estado", "Cantidad", "Precio", "Ubicación"])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        encabezado = self.tabla.horizontalHeader()
        encabezado.setSectionResizeMode(QHeaderView.ResizeToContents)
        encabezado.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.itemSelectionChanged.connect(self.cargar_seleccion)
        derecha.addWidget(self.tabla)
        fila.addLayout(derecha)
        return pagina

    def _pestana_resumen(self) -> QWidget:
        pagina = QWidget()
        col = QVBoxLayout(pagina)
        grupo = QGroupBox("Unidades por categoría")
        QVBoxLayout(grupo).addWidget(grafica := GraficaBarras())
        self.grafica = grafica
        col.addWidget(grupo, 3)
        self.tabla_resumen = QTableWidget(0, 4)
        self.tabla_resumen.setHorizontalHeaderLabels(["Categoría", "Unidades", "Valor (MXN)", "% del valor"])
        self.tabla_resumen.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_resumen.verticalHeader().setVisible(False)
        self.tabla_resumen.setEditTriggers(QTableWidget.NoEditTriggers)
        col.addWidget(self.tabla_resumen, 2)
        return pagina

    def _pestana_equipo(self) -> QWidget:
        pagina = QWidget()
        col = QVBoxLayout(pagina)
        grupo = QGroupBox("Recursos reales de esta computadora (se actualizan cada 2 s en segundo plano)")
        form = QFormLayout(grupo)
        self.e_sistema, self.e_equipo, self.e_nucleos = QLabel(), QLabel(), QLabel()
        self.e_cpu, self.e_ram, self.e_disco = QProgressBar(), QProgressBar(), QProgressBar()
        for etiqueta, w in [("Sistema operativo:", self.e_sistema), ("Equipo:", self.e_equipo), ("Núcleos lógicos:", self.e_nucleos),
                            ("Uso de CPU:", self.e_cpu), ("Memoria RAM:", self.e_ram), ("Disco:", self.e_disco)]:
            form.addRow(etiqueta, w)
        col.addWidget(grupo)

        grupo_datos = QGroupBox("Archivos locales de la aplicación")
        g = QVBoxLayout(grupo_datos)
        ruta = QLabel(f"Base de datos: {self.almacen.archivo}")
        ruta.setTextInteractionFlags(Qt.TextSelectableByMouse)
        g.addWidget(ruta)
        botones = QHBoxLayout()
        botones.addWidget(QPushButton("📁 Abrir carpeta de datos", clicked=self.abrir_carpeta))
        botones.addWidget(QPushButton("🛟 Crear respaldo ahora", clicked=self.crear_respaldo))
        botones.addStretch()
        g.addLayout(botones)
        self.bitacora = QPlainTextEdit(readOnly=True)
        self.bitacora.setPlaceholderText("Bitácora de la aplicación")
        g.addWidget(self.bitacora)
        col.addWidget(grupo_datos)
        return pagina

    # ================== Datos y tabla ==================
    def filtrados(self) -> list[dict]:
        return models.filtrar(self.registros, self.buscador.text(), self.filtro_cat.currentText(), self.filtro_est.currentText())

    def refrescar(self) -> None:
        """Actualiza tabla, tarjetas y resumen después de cualquier cambio."""
        self.refrescar_tabla()
        est = models.estadisticas(self.registros)
        self.kpi["registros"].setText(str(est["registros"]))
        self.kpi["unidades"].setText(f"{est['unidades']:,}")
        self.kpi["valor"].setText(f"${est['valor']:,.2f}")
        self.kpi["alertas"].setText(str(est["alertas"]))
        self.kpi["alertas"].setStyleSheet(
            f"font-size:20px; font-weight:bold; border:none; color:{'#fbbf24' if est['alertas'] else '#f8fafc'};")

        resumen = models.resumen_por_categoria(self.registros)
        self.grafica.mostrar([(c, u) for c, u, _ in resumen])
        self.tabla_resumen.setRowCount(len(resumen))
        for fila, (cat, unidades, valor) in enumerate(resumen):
            pct = valor / est["valor"] * 100 if est["valor"] else 0
            for col, texto in enumerate([cat, f"{unidades:,}", f"${valor:,.2f}", f"{pct:.1f} %"]):
                self.tabla_resumen.setItem(fila, col, QTableWidgetItem(texto))

    def refrescar_tabla(self) -> None:
        lista = self.filtrados()
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(lista))
        for fila, r in enumerate(lista):
            valores = [r["id"], r["nombre"], r["categoria"], r["estado"], str(r["cantidad"]), f"${r['precio']:,.2f}", r["ubicacion"]]
            for col, texto in enumerate(valores):
                celda = QTableWidgetItem(texto)
                if col in (4, 5):
                    celda.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if col == 4 and r["cantidad"] <= models.BAJO_STOCK:
                    celda.setForeground(Qt.yellow)
                self.tabla.setItem(fila, col, celda)
        self.tabla.blockSignals(False)
        self.contador.setText(f"{len(lista)} de {len(self.registros)} registros")

    def guardar_y_refrescar(self, mensaje: str) -> None:
        self.almacen.guardar(self.registros)
        self.refrescar()
        self.statusBar().showMessage(mensaje, 6000)
        self.anotar(mensaje)

    # ================== Alta, edición y eliminación ==================
    def leer_formulario(self) -> dict:
        return models.normalizar({
            "id": self.f_id.text(), "nombre": self.f_nombre.text(), "categoria": self.f_categoria.currentText(),
            "estado": self.f_estado.currentText(), "cantidad": self.f_cantidad.value(), "precio": self.f_precio.value(),
            "ubicacion": self.f_ubicacion.text(), "notas": self.f_notas.toPlainText(),
        })

    def guardar_formulario(self) -> None:
        r = self.leer_formulario()
        if not r["id"] or not r["nombre"]:
            QMessageBox.warning(self, "Faltan datos", "El ID y el nombre son obligatorios.")
            return
        ids = [x["id"] for x in self.registros]
        if self.editando_id is None:                          # alta
            if r["id"] in ids:
                QMessageBox.warning(self, "ID repetido", f"Ya existe un registro con el ID {r['id']}.")
                return
            self.registros.append(r)
            mensaje = f"Registro {r['id']} agregado."
        else:                                                # edición
            if r["id"] != self.editando_id and r["id"] in ids:
                QMessageBox.warning(self, "ID repetido", f"Ya existe un registro con el ID {r['id']}.")
                return
            self.registros[ids.index(self.editando_id)] = r
            mensaje = f"Registro {r['id']} actualizado."
        self.guardar_y_refrescar(mensaje)
        self.limpiar_formulario()

    def cargar_seleccion(self) -> None:
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            return
        r = self.filtrados()[filas[0].row()]
        self.editando_id = r["id"]
        self.grupo_form.setTitle(f"Editando {r['id']}")
        self.f_id.setText(r["id"])
        self.f_nombre.setText(r["nombre"])
        self.f_categoria.setCurrentText(r["categoria"])
        self.f_estado.setCurrentText(r["estado"])
        self.f_cantidad.setValue(r["cantidad"])
        self.f_precio.setValue(r["precio"])
        self.f_ubicacion.setText(r["ubicacion"])
        self.f_notas.setPlainText(r["notas"])

    def limpiar_formulario(self) -> None:
        self.editando_id = None
        self.grupo_form.setTitle("Nuevo registro")
        for campo in (self.f_id, self.f_nombre, self.f_ubicacion):
            campo.clear()
        self.f_notas.clear()
        self.f_categoria.setCurrentIndex(0)
        self.f_estado.setCurrentIndex(0)
        self.f_cantidad.setValue(0)
        self.f_precio.setValue(0)
        self.tabla.clearSelection()

    def dialogo_confirmar(self, r: dict) -> QMessageBox:
        caja = QMessageBox(QMessageBox.Question, "Confirmar eliminación",
                           f"¿Eliminar el registro {r['id']} — {r['nombre']}?\nEsta acción no se puede deshacer.",
                           QMessageBox.Yes | QMessageBox.No, self)
        caja.button(QMessageBox.Yes).setText("Sí, eliminar")
        caja.button(QMessageBox.No).setText("Cancelar")
        caja.setDefaultButton(QMessageBox.No)
        return caja

    def eliminar_seleccionado(self) -> None:
        if self.editando_id is None:
            QMessageBox.information(self, "Eliminar", "Primero selecciona un registro en la tabla.")
            return
        r = next(x for x in self.registros if x["id"] == self.editando_id)
        if self.dialogo_confirmar(r).exec() == QMessageBox.Yes:
            self.registros.remove(r)
            self.guardar_y_refrescar(f"Registro {r['id']} eliminado.")
            self.limpiar_formulario()

    # ================== Importar y exportar (diálogos nativos del sistema) ==================
    def importar(self, tipo: str) -> None:
        ruta, _ = QFileDialog.getOpenFileName(self, f"Importar {tipo.upper()}", str(Path.home()),
                                              f"Archivos {tipo.upper()} (*.{tipo})")
        if not ruta:
            return
        try:
            nuevos = models.Almacen.leer_csv(Path(ruta)) if tipo == "csv" else models.Almacen.leer_json(Path(ruta))
        except Exception as error:
            QMessageBox.critical(self, "No se pudo importar", f"El archivo no tiene el formato esperado.\n{error}")
            return
        respaldo = self.almacen.respaldar()
        self.registros, agregados, actualizados = models.combinar(self.registros, nuevos)
        self.guardar_y_refrescar(f"Importado {Path(ruta).name}: {agregados} nuevos, {actualizados} actualizados "
                                 f"(respaldo previo: {respaldo.name}).")

    def exportar(self, tipo: str) -> None:
        sugerido = str(Path.home() / f"inventario_deskdata.{tipo}")
        ruta, _ = QFileDialog.getSaveFileName(self, f"Exportar {tipo.upper()}", sugerido, f"Archivos {tipo.upper()} (*.{tipo})")
        if not ruta:
            return
        lista = self.filtrados()
        if tipo == "csv":
            models.Almacen.exportar_csv(lista, Path(ruta))
        else:
            models.Almacen.exportar_json(lista, Path(ruta))
        self.statusBar().showMessage(f"Exportados {len(lista)} registros a {ruta}", 6000)
        self.anotar(f"Exportados {len(lista)} registros a {Path(ruta).name}")

    # ================== Equipo y archivos locales ==================
    def mostrar_equipo(self, d: dict) -> None:
        self.e_sistema.setText(d["sistema"])
        self.e_equipo.setText(d["equipo"])
        self.e_nucleos.setText(str(d["nucleos"]))
        self.e_cpu.setValue(round(d["cpu"]))
        self.e_cpu.setFormat(f"{d['cpu']:.0f} %")
        self.e_ram.setValue(round(d["ram_pct"]))
        self.e_ram.setFormat(f"{d['ram_pct']:.0f} %  ({d['ram_usada_gb']:.1f} de {d['ram_total_gb']:.1f} GB)")
        self.e_disco.setValue(round(d["disco_pct"]))
        self.e_disco.setFormat(f"{d['disco_pct']:.0f} %  ({d['disco_libre_gb']:.0f} GB libres de {d['disco_total_gb']:.0f} GB)")

    def abrir_carpeta(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.almacen.carpeta)))

    def crear_respaldo(self) -> None:
        destino = self.almacen.respaldar()
        self.statusBar().showMessage(f"Respaldo creado: {destino}", 6000)
        self.anotar(f"Respaldo creado: {destino.name}")

    def anotar(self, texto: str) -> None:
        from datetime import datetime
        self.bitacora.appendPlainText(f"[{datetime.now():%H:%M:%S}] {texto}")

    def closeEvent(self, evento) -> None:
        self.monitor.lectura.disconnect(self.mostrar_equipo)
        self.monitor.detener()
        super().closeEvent(evento)
