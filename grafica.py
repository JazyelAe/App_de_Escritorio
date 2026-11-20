"""grafica.py — Gráfica de barras sencilla dibujada a mano con QPainter (sin librerías extra)."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QWidget

COLORES = ["#38bdf8", "#a78bfa", "#34d399", "#fbbf24", "#f87171", "#fb923c"]


class GraficaBarras(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.datos: list[tuple[str, int]] = []
        self.setMinimumHeight(280)

    def mostrar(self, datos: list[tuple[str, int]]) -> None:
        """datos = [(categoría, unidades), ...]"""
        self.datos = datos
        self.update()  # pide a Qt que vuelva a dibujar el widget

    def paintEvent(self, evento) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#1e293b"))
        if not self.datos:
            p.setPen(QColor("#94a3b8"))
            p.drawText(self.rect(), Qt.AlignCenter, "Sin datos para graficar")
            return

        margen_izq, margen_inf, margen_sup = 20, 46, 30
        ancho_util = self.width() - margen_izq * 2
        alto_util = self.height() - margen_inf - margen_sup
        maximo = max(u for _, u in self.datos) or 1
        espacio = ancho_util / len(self.datos)
        ancho_barra = min(80, espacio * 0.6)

        p.setFont(QFont("Segoe UI", 9))
        for i, (categoria, unidades) in enumerate(self.datos):
            alto = alto_util * unidades / maximo
            x = margen_izq + i * espacio + (espacio - ancho_barra) / 2
            y = margen_sup + alto_util - alto
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(COLORES[i % len(COLORES)]))
            p.drawRoundedRect(QRectF(x, y, ancho_barra, alto), 4, 4)
            # valor arriba de la barra y categoría abajo
            p.setPen(QColor("#f8fafc"))
            p.drawText(QRectF(x - 20, y - 22, ancho_barra + 40, 20), Qt.AlignCenter, str(unidades))
            p.setPen(QColor("#94a3b8"))
            p.drawText(QRectF(margen_izq + i * espacio, self.height() - margen_inf + 8, espacio, 20),
                       Qt.AlignCenter, categoria)
