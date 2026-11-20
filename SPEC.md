# SPEC · DeskData Pro — Subproducto No. 3 "Aplicación de escritorio"

**Materia:** Aplicaciones Web Progresivas · Unidad I · Actividad Desarrollo
**Alumno:** Jahir Jaziel Serrano Arana · 10° D
**Repositorio:** `JazyelAe/App_de_Escritorio`
**Estado:** borrador para aprobación (Checkpoint A)

## 1. Objetivo
Tener una **aplicación de escritorio para Windows** hecha con Python + PySide6 (Qt): un gestor de inventario de equipo de cómputo que se instala y ejecuta en la PC, trabaja **sin Internet**, guarda sus datos en archivos locales, usa los diálogos nativos del sistema para abrir y guardar archivos y muestra los recursos reales del equipo. Se distribuye como un **.exe** (PyInstaller) en un GitHub Release, generado con GitHub Actions.

## 2. Auditoría del repo actual
| Elemento | Estado | Decisión |
|---|---|---|
| `main.py` (708 líneas) + `models.py` + `worker_service.py` | PySide6. Abre bien y `--self-test` pasa. Tiene 3 pestañas: **Gestión JSON/CSV** (formulario, tabla, búsqueda, filtro, importar/exportar CSV y JSON), **Recursos del equipo** (CPU, RAM, disco y bitácora del hilo en segundo plano) y **Manifiesto y actualizaciones**. | Se conserva la base y se corrige lo de abajo. |
| Uso de CPU | ❗ **En Windows el valor es falso**: está fijo en 12.5 % porque `os.getloadavg()` no existe en Windows. | Se mide de verdad con `psutil`. |
| Pestaña "Manifiesto" | Muestra un `manifest.json` de **PWA** (`start_url`, `display: standalone`), que es un concepto web y confunde con SP7. | Se reemplaza por una pestaña **Resumen** con gráfica por categoría (RF-4). |
| Archivos web: `index.html`, `app.js`, `styles.css`, `manifest.json`, `service-worker.js`, `worker-service.js`, `icons/icon-192/512.png` | Son una PWA mezclada en el repo, y GitHub Pages la publica en `jazyelae.github.io/App_de_Escritorio/`. **Ningún archivo Python los usa** (solo se lee `manifest.json` para el título y la versión). | **Preguntarte:** moverlos a `legacy/` o eliminarlos. |
| Carpeta de datos | Se guarda junto a `main.py`. En un .exe de PyInstaller esa carpeta es temporal, así que **los datos se perderían al cerrar**. | Los datos pasan a `%APPDATA%\DeskDataPro\`. |
| Gráfica o resumen por categoría | No existe (solo hay 4 indicadores generales). | Se agrega. |
| `--capturas` | No existe. | Se agrega. |
| `requirements.txt` | `PySide6>=6.5.0`, sin versión fija. | Se fijan las versiones. |
| PyInstaller, Actions y Release | No existen. | Se agregan. |
| README | Exagera ("implementación completa", "PWA de escritorio"). | Se reescribe. |

## 3. Requisitos funcionales
- **RF-1 Tabla de registros con alta, edición y eliminación.**
  - La tabla muestra ID, nombre, categoría, estado, cantidad, precio y ubicación.
  - El formulario lateral sirve para **dar de alta**; al seleccionar una fila se **edita**; el botón eliminar **pide confirmación**.
  - Se valida que el ID y el nombre no estén vacíos y que el ID no esté repetido.
- **RF-2 Persistencia local y archivos.**
  - Cada cambio se guarda en `%APPDATA%\DeskDataPro\registros.json`.
  - **Importar y exportar CSV** (también JSON) con el **diálogo nativo de Windows** (`QFileDialog`).
  - Se hace un respaldo automático antes de importar.
- **RF-3 Búsqueda y filtro.** Texto libre (ID, nombre o ubicación), filtro por categoría y filtro por estado, combinables, con contador "N de M registros".
- **RF-4 Resumen.** Pestaña **Resumen** con:
  - Una gráfica de barras de las **unidades por categoría**, dibujada con `QPainter` (sin librerías extra).
  - Una tabla con el total de unidades y el valor en MXN por categoría.
  - Los indicadores generales: registros, unidades, valor y alertas de bajo stock.
- **RF-5 Funciona sin Internet y usa recursos locales.**
  - No hace ninguna petición de red.
  - La pestaña **Equipo** muestra datos reales con `psutil`: sistema operativo, CPU %, RAM y disco. Un hilo en segundo plano (`QThread`) los actualiza cada 2 s.
  - Usa diálogos nativos de archivos y mensajes, y el icono de la ventana y de la barra de tareas.
- **RF-6 `--capturas`.**
  - `python main.py --capturas` (o `DeskDataPro.exe --capturas`) abre la app con **datos de ejemplo en una carpeta temporal**, sin tocar tus datos.
  - Recorre cada vista y guarda las imágenes con `QWidget.grab()` en `docs/capturas/`: inicio, formulario lleno, búsqueda, filtro, resumen, equipo y diálogo de confirmación.
  - Al terminar, se cierra sola.

## 4. Requisitos no funcionales
- **RNF-1** Windows 10/11, sin necesitar Python en la PC donde se ejecuta el .exe.
- **RNF-2** Código en español, comentado y dividido en módulos cortos, para poder explicarlo en clase.
- **RNF-3** Versiones fijas en `requirements.txt` (PySide6, psutil y PyInstaller).
- **RNF-4** La interfaz se conserva en tema oscuro, con la tabla legible y columnas ajustadas al contenido.

## 5. Tecnologías
| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.13 |
| Interfaz gráfica | PySide6 (Qt 6): QMainWindow, QTableWidget, QFileDialog, QMessageBox y QPainter |
| Segundo plano | QThread + señales |
| Recursos del equipo | psutil (CPU, RAM y disco) |
| Persistencia | JSON y CSV (módulos `json` y `csv`) en `%APPDATA%` |
| Empaquetado | PyInstaller `--onefile --windowed` con icono `.ico` |
| CI/CD | GitHub Actions (`windows-latest`) + GitHub Releases |

## 6. Estructura propuesta
```
main.py              ← arranque y opciones (--capturas, --self-test)
ventana.py           ← ventana principal y pestañas
grafica.py           ← gráfica de barras con QPainter
models.py            ← datos: JSON, CSV, respaldos y estadísticas
worker_service.py    ← hilo de monitoreo con psutil
capturas.py          ← modo --capturas
datos/semilla.json   ← datos de ejemplo de la primera ejecución
icons/app_icon.png, app_icon.ico
requirements.txt · .github/workflows/build.yml · README.md · SPEC.md · docs/capturas/
```

## 7. Criterios de aceptación
| # | Criterio | Cómo se verifica |
|---|---|---|
| CA-1 | `python main.py` abre en Windows sin errores. | Ejecución local |
| CA-2 | Alta, edición y eliminación funcionan, y se conservan al cerrar y abrir. | Prueba automatizada (`--self-test` ampliado) + capturas |
| CA-3 | Exportar e importar CSV conserva todos los registros; los diálogos son los nativos. | Prueba automatizada + captura del diálogo |
| CA-4 | La búsqueda y los filtros reducen la tabla correctamente. | Prueba automatizada + capturas |
| CA-5 | El resumen por categoría coincide con la suma de la tabla. | Prueba automatizada + captura |
| CA-6 | CPU, RAM y disco son reales (coinciden con `psutil`) y no fijos. | Prueba + captura |
| CA-7 | El workflow genera `DeskDataPro.exe` y lo adjunta al Release `v1.0.0`. | Actions + página del Release |
| CA-8 | El .exe abre en un Windows **limpio** sin usar Python: en Actions se ejecuta `DeskDataPro.exe --capturas` y produce las imágenes. | Artefacto de Actions |
| CA-9 | `--capturas` genera las imágenes de cada vista. | `docs/capturas/` |
| CA-10 | README con capturas, instrucciones y enlaces. | Revisar el repo |

## 8. Plan de despliegue
`.github/workflows/build.yml` en `windows-latest`. En cada push:
1. Instala las dependencias.
2. Corre `--self-test`.
3. Empaqueta con PyInstaller.
4. Ejecuta `DeskDataPro.exe --capturas` para probar el .exe.
5. Sube el .exe y las capturas como artefactos.

Con la etiqueta `v1.0.0` crea el **Release**. **URL de la aplicación:** `https://github.com/JazyelAe/App_de_Escritorio/releases/tag/v1.0.0`.

## 9. Capturas
Todas automáticas con `--capturas`, sin pedirte nada:
`01_inicio.png`, `02_formulario.png`, `03_busqueda.png`, `04_filtro.png`, `05_resumen.png`, `06_equipo.png`, `07_confirmar_eliminar.png`, `08_dialogo_exportar.png`.

Opcional: si quieres una captura de la app en **tu escritorio de Windows** con la barra de tareas, te la pido en el Checkpoint B.

## 10. Ejemplos reales propuestos (URL comprobadas el 20/11/2026)
| App | Por qué es de escritorio | URL |
|---|---|---|
| Visual Studio Code | Editor que se instala en Windows, macOS y Linux; trabaja con archivos locales y terminales del sistema (Electron). | https://code.visualstudio.com/ |
| Microsoft Excel | Hoja de cálculo instalada en la PC; abre y guarda archivos locales y funciona sin conexión. | https://www.microsoft.com/es-mx/microsoft-365/excel |
| OBS Studio | Grabación y transmisión que usa directamente la cámara, el audio y la GPU del equipo (C/C++ con Qt). | https://obsproject.com/ |

Fuentes técnicas (comprobadas): documentación de Qt for Python, PyInstaller y psutil, y el repositorio de OBS Studio.

## 11. Pruebas
_(Se llena después de implementar.)_
