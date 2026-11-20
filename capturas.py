"""capturas.py — Modo --capturas: abre la app con datos de ejemplo y guarda una imagen de cada vista.

Usa una carpeta temporal, así que no toca los datos reales del usuario. Cada imagen se obtiene con QWidget.grab().
"""
import os
import tempfile
from pathlib import Path

from PySide6.QtCore import QEvent, QTimer
from PySide6.QtWidgets import QApplication

import models
from ventana import VentanaPrincipal


def ejecutar(app: QApplication, destino: Path) -> int:
    destino.mkdir(parents=True, exist_ok=True)
    temporal = Path(tempfile.mkdtemp(prefix="deskdata_"))
    ventana = VentanaPrincipal(models.Almacen(temporal))
    ventana.show()
    pasos = []

    def guardar(nombre: str, widget=None) -> None:
        (widget or ventana).grab().save(str(destino / nombre))
        print("captura:", destino / nombre)

    # Cada paso prepara una vista y la guarda; se ejecutan uno tras otro con un pequeño retraso.
    def p_inicio():
        guardar("01_inicio.png")

    def p_formulario():
        ventana.tabla.selectRow(4)  # INV-005 (bajo stock)
        guardar("02_formulario.png")
        ventana.limpiar_formulario()

    def p_busqueda():
        ventana.buscador.setText("laptop")
        guardar("03_busqueda.png")
        ventana.buscador.clear()

    def p_filtro():
        ventana.filtro_cat.setCurrentText("Periféricos")
        guardar("04_filtro.png")
        ventana.filtro_cat.setCurrentText("Todas")

    def p_alta():
        # Se demuestra un alta real con el formulario.
        ventana.f_id.setText("INV-013")
        ventana.f_nombre.setText("Impresora láser")
        ventana.f_categoria.setCurrentText("Periféricos")
        ventana.f_cantidad.setValue(2)
        ventana.f_precio.setValue(3200)
        ventana.f_ubicacion.setText("Oficina de sistemas")
        ventana.guardar_formulario()
        ventana.tabla.scrollToBottom()
        guardar("05_alta.png")

    def p_confirmar():
        ventana.tabla.selectRow(0)
        caja = ventana.dialogo_confirmar(ventana.registros[0])
        caja.show()
        QApplication.processEvents()
        guardar("06_confirmar_eliminar.png", caja)
        caja.close()
        ventana.limpiar_formulario()

    def p_resumen():
        ventana.pestanas.setCurrentIndex(1)
        guardar("07_resumen.png")

    def p_equipo():
        ventana.pestanas.setCurrentIndex(2)
        guardar("08_equipo.png")

    def p_fin():
        ventana.close()
        app.quit()

    pasos = [p_inicio, p_formulario, p_busqueda, p_filtro, p_alta, p_confirmar, p_resumen, p_equipo, p_fin]

    def siguiente():
        if pasos:
            pasos.pop(0)()
            QApplication.processEvents()
            QTimer.singleShot(900, siguiente)

    QTimer.singleShot(2500, siguiente)  # espera a que el monitor tome la primera lectura
    # Seguro: si algo se atora, se cierra a los 60 segundos.
    QTimer.singleShot(60000, lambda: os._exit(1))
    codigo = app.exec()
    # Se libera la ventana antes que la aplicación para que Qt se cierre en orden.
    ventana.deleteLater()
    QApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    del ventana
    return codigo
