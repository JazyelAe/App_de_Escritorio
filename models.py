"""models.py — Datos de DeskData Pro: lectura y escritura de archivos JSON y CSV en la computadora.

No usa Internet: todo vive en una carpeta local del usuario (por defecto %APPDATA%\\DeskDataPro).
"""
import csv
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

CAMPOS = ["id", "nombre", "categoria", "estado", "cantidad", "precio", "ubicacion", "notas"]
CATEGORIAS = ["Hardware", "Software", "Periféricos", "Almacenamiento", "Componentes", "Redes"]
ESTADOS = ["Activo", "Mantenimiento", "Bajo stock", "Archivado"]
BAJO_STOCK = 5  # se considera alerta si la cantidad es menor o igual a este número


def ruta_recurso(relativa: str) -> Path:
    """Ruta a un archivo incluido en la app. Con PyInstaller los archivos se extraen en sys._MEIPASS."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relativa


def carpeta_datos_por_defecto() -> Path:
    """Carpeta de datos del usuario en Windows (%APPDATA%) o en su carpeta personal en otros sistemas."""
    base = os.environ.get("APPDATA") or str(Path.home() / ".config")
    return Path(base) / "DeskDataPro"


def normalizar(registro: dict) -> dict:
    """Limpia un registro: textos sin espacios extra y números con el tipo correcto."""
    limpio = {campo: str(registro.get(campo, "") or "").strip() for campo in CAMPOS}
    limpio["id"] = limpio["id"].upper()
    try:
        limpio["cantidad"] = int(float(limpio["cantidad"] or 0))
    except ValueError:
        limpio["cantidad"] = 0
    try:
        limpio["precio"] = round(float(limpio["precio"] or 0), 2)
    except ValueError:
        limpio["precio"] = 0.0
    return limpio


class Almacen:
    """Guarda los registros del inventario en registros.json y hace respaldos."""

    def __init__(self, carpeta: Path | None = None):
        self.carpeta = Path(carpeta) if carpeta else carpeta_datos_por_defecto()
        self.archivo = self.carpeta / "registros.json"
        self.respaldos = self.carpeta / "respaldos"
        self.respaldos.mkdir(parents=True, exist_ok=True)
        if not self.archivo.exists():
            # Primera vez: se copian los datos de ejemplo incluidos en la app.
            semilla = json.loads(ruta_recurso("datos/semilla.json").read_text(encoding="utf-8"))
            self.guardar([normalizar(r) for r in semilla])

    # ---------- JSON ----------
    def cargar(self) -> list[dict]:
        datos = json.loads(self.archivo.read_text(encoding="utf-8"))
        return [normalizar(r) for r in datos.get("registros", [])]

    def guardar(self, registros: list[dict]) -> None:
        contenido = {
            "aplicacion": "DeskData Pro",
            "guardado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(registros),
            "registros": registros,
        }
        # Se escribe primero a un archivo temporal y luego se reemplaza: así no se corrompe si algo falla.
        temporal = self.archivo.with_suffix(".tmp")
        temporal.write_text(json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8")
        temporal.replace(self.archivo)

    def respaldar(self) -> Path:
        destino = self.respaldos / f"registros_{datetime.now():%Y%m%d_%H%M%S}.json"
        shutil.copy2(self.archivo, destino)
        return destino

    # ---------- CSV ----------
    @staticmethod
    def exportar_csv(registros: list[dict], ruta: Path) -> None:
        # utf-8-sig agrega una marca para que Excel muestre bien los acentos.
        with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
            escritor = csv.DictWriter(f, fieldnames=CAMPOS)
            escritor.writeheader()
            escritor.writerows(registros)

    @staticmethod
    def leer_csv(ruta: Path) -> list[dict]:
        with open(ruta, newline="", encoding="utf-8-sig") as f:
            return [normalizar(fila) for fila in csv.DictReader(f) if fila.get("id")]

    @staticmethod
    def exportar_json(registros: list[dict], ruta: Path) -> None:
        Path(ruta).write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def leer_json(ruta: Path) -> list[dict]:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
        lista = datos.get("registros", []) if isinstance(datos, dict) else datos
        return [normalizar(r) for r in lista if r.get("id")]


# ---------- Funciones de apoyo (se prueban con --self-test) ----------
def combinar(actuales: list[dict], nuevos: list[dict]) -> tuple[list[dict], int, int]:
    """Agrega los registros nuevos y actualiza los que ya existen (mismo ID). Devuelve (lista, agregados, actualizados)."""
    por_id = {r["id"]: r for r in actuales}
    agregados = actualizados = 0
    for r in nuevos:
        if r["id"] in por_id:
            actualizados += 1
        else:
            agregados += 1
        por_id[r["id"]] = r
    return list(por_id.values()), agregados, actualizados


def filtrar(registros: list[dict], texto: str = "", categoria: str = "Todas", estado: str = "Todos") -> list[dict]:
    texto = texto.strip().lower()
    return [
        r for r in registros
        if (categoria == "Todas" or r["categoria"] == categoria)
        and (estado == "Todos" or r["estado"] == estado)
        and (not texto or texto in f"{r['id']} {r['nombre']} {r['ubicacion']}".lower())
    ]


def estadisticas(registros: list[dict]) -> dict:
    return {
        "registros": len(registros),
        "unidades": sum(r["cantidad"] for r in registros),
        "valor": sum(r["cantidad"] * r["precio"] for r in registros),
        "alertas": sum(1 for r in registros if r["cantidad"] <= BAJO_STOCK),
    }


def resumen_por_categoria(registros: list[dict]) -> list[tuple[str, int, float]]:
    """[(categoría, unidades, valor)] ordenado de mayor a menor número de unidades."""
    totales: dict[str, list] = {}
    for r in registros:
        t = totales.setdefault(r["categoria"], [0, 0.0])
        t[0] += r["cantidad"]
        t[1] += r["cantidad"] * r["precio"]
    return sorted(((c, u, v) for c, (u, v) in totales.items()), key=lambda x: -x[1])
