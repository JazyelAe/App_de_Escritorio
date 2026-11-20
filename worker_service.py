"""worker_service.py — Hilo en segundo plano que lee los recursos reales del equipo con psutil.

Corre en un QThread para que la ventana nunca se congele mientras mide CPU, RAM y disco.
"""
import platform
from datetime import datetime

import psutil
from PySide6.QtCore import QThread, Signal


def leer_equipo(carpeta: str = "C:\\") -> dict:
    """Toma una lectura del sistema operativo y del hardware local."""
    memoria = psutil.virtual_memory()
    disco = psutil.disk_usage(carpeta)
    return {
        "hora": datetime.now().strftime("%H:%M:%S"),
        "sistema": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "equipo": platform.node(),
        "nucleos": psutil.cpu_count(logical=True),
        "cpu": psutil.cpu_percent(interval=None),
        "ram_pct": memoria.percent,
        "ram_usada_gb": memoria.used / 1024 ** 3,
        "ram_total_gb": memoria.total / 1024 ** 3,
        "disco_pct": disco.percent,
        "disco_libre_gb": disco.free / 1024 ** 3,
        "disco_total_gb": disco.total / 1024 ** 3,
    }


class MonitorEquipo(QThread):
    """Emite una lectura nueva cada `intervalo` segundos."""

    lectura = Signal(dict)

    def __init__(self, carpeta: str, intervalo: float = 2.0, parent=None):
        super().__init__(parent)
        self.carpeta = carpeta
        self.intervalo_ms = int(intervalo * 1000)
        self._activo = True

    def run(self) -> None:
        psutil.cpu_percent(interval=None)  # la primera lectura de CPU siempre es 0: se descarta
        while self._activo:
            self.msleep(self.intervalo_ms)
            if self._activo:
                self.lectura.emit(leer_equipo(self.carpeta))

    def detener(self) -> None:
        self._activo = False
        self.wait(3000)
