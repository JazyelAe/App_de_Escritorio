"""DeskData Pro — aplicación de escritorio (Python + PySide6) para llevar un inventario de equipo de cómputo.

Uso:
    python main.py                  abre la aplicación
    python main.py --capturas       genera las capturas de cada vista en docs/capturas/
    python main.py --self-test      prueba la lógica de datos sin abrir ventanas
    python main.py --datos CARPETA  usa otra carpeta de datos (por defecto %APPDATA%\\DeskDataPro)
"""
import argparse
import sys
import tempfile
from pathlib import Path


def self_test() -> int:
    """Pruebas de la lógica: alta/edición/baja persistentes, CSV ida y vuelta, filtros, resumen y psutil."""
    import models
    from worker_service import leer_equipo

    carpeta = Path(tempfile.mkdtemp(prefix="deskdata_test_"))
    a = models.Almacen(carpeta)
    regs = a.cargar()
    assert len(regs) == 12, "la semilla debe tener 12 registros"
    print("OK  semilla cargada:", len(regs), "registros")

    regs.append(models.normalizar({"id": "inv-900", "nombre": "Prueba", "categoria": "Redes", "estado": "Activo",
                                   "cantidad": "7", "precio": "100.5"}))
    regs[0]["cantidad"] = 99
    regs = [r for r in regs if r["id"] != "INV-002"]
    a.guardar(regs)
    otra = models.Almacen(carpeta).cargar()   # como si se cerrara y abriera la app
    assert any(r["id"] == "INV-900" and r["cantidad"] == 7 for r in otra)
    assert otra[0]["cantidad"] == 99 and not any(r["id"] == "INV-002" for r in otra)
    print("OK  alta, edición y eliminación persisten en", a.archivo)

    csv_ruta = carpeta / "exportado.csv"
    models.Almacen.exportar_csv(otra, csv_ruta)
    assert models.Almacen.leer_csv(csv_ruta) == otra
    print("OK  CSV exportado e importado sin pérdidas:", len(otra), "registros")

    ejemplo = models.Almacen.leer_csv(models.ruta_recurso("datos/ejemplo_importar.csv"))
    combinados, nuevos, actualizados = models.combinar(otra, ejemplo)
    assert (nuevos, actualizados) == (3, 0) and len(combinados) == len(otra) + 3
    print("OK  importar ejemplo_importar.csv agrega", nuevos, "registros")

    assert [r["id"] for r in models.filtrar(otra, "laptop")] == ["INV-001"]
    assert all(r["categoria"] == "Periféricos" for r in models.filtrar(otra, categoria="Periféricos"))
    assert all(r["estado"] == "Bajo stock" for r in models.filtrar(otra, estado="Bajo stock"))
    print("OK  búsqueda y filtros")

    resumen = models.resumen_por_categoria(otra)
    assert sum(u for _, u, _ in resumen) == models.estadisticas(otra)["unidades"]
    assert abs(sum(v for _, _, v in resumen) - models.estadisticas(otra)["valor"]) < 0.01
    print("OK  resumen por categoría coincide con los totales:", [(c, u) for c, u, _ in resumen])

    eq = leer_equipo(str(Path(carpeta).anchor or "/"))
    assert eq["ram_total_gb"] > 0 and 0 <= eq["disco_pct"] <= 100 and eq["nucleos"] >= 1
    print(f"OK  recursos reales con psutil: {eq['sistema']}, {eq['nucleos']} núcleos, "
          f"RAM {eq['ram_pct']:.0f} % de {eq['ram_total_gb']:.1f} GB, disco {eq['disco_pct']:.0f} %")
    print("Todas las pruebas pasaron.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="DeskData Pro — inventario local de escritorio")
    parser.add_argument("--capturas", nargs="?", const="docs/capturas", metavar="CARPETA",
                        help="genera capturas de cada vista y cierra")
    parser.add_argument("--self-test", action="store_true", help="prueba la lógica sin abrir ventanas")
    parser.add_argument("--datos", metavar="CARPETA", help="carpeta de datos alternativa")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    from PySide6.QtCore import QEvent
    from PySide6.QtWidgets import QApplication
    import models

    app = QApplication(sys.argv)
    app.setApplicationName("DeskData Pro")
    if args.capturas:
        import capturas
        return capturas.ejecutar(app, Path(args.capturas))

    from ventana import VentanaPrincipal
    ventana = VentanaPrincipal(models.Almacen(Path(args.datos) if args.datos else None))
    ventana.show()
    codigo = app.exec()
    # Se libera la ventana antes que la aplicación para que Qt se cierre en orden.
    ventana.deleteLater()
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    del ventana
    return codigo


if __name__ == "__main__":
    sys.exit(main())
