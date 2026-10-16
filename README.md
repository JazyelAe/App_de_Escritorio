# DeskData Pro — Aplicación de Escritorio (Python + PySide6 + JSON/CSV + Manifest + Worker Service)

Este paquete contiene la implementación completa y funcional de la **Aplicación de Escritorio** descrita en tu especificación técnica:

1. **Definición**: Programa instalado directamente en una computadora para realizar funciones especializadas de gestión de datos y monitoreo.
2. **Ejecución local y recursos**: Se ejecuta localmente, monitorea el uso de CPU, memoria RAM y almacenamiento del equipo, y trabaja directamente con archivos **JSON** y **CSV** almacenados en la computadora.
3. **Funcionamiento sin Internet (Offline-First)**: Funciona al 100% sin conexión a Internet, brindando herramientas especializadas de importación, exportación, filtrado, cálculo de inventario y respaldos automáticos.
4. **Instalación y actualizaciones locales**: Incluye instaladores para el sistema operativo (`instalar_y_ejecutar.bat` para Windows, `instalar_y_ejecutar.sh` para Linux/macOS), configuración de manifiesto (`manifest.json`), servicio en segundo plano (`worker_service.py` y `service-worker.js`) y módulo de actualizaciones locales (`datos/actualizacion_local.json`).

## Estructura de Archivos del Paquete

- `main.py`: Aplicación de escritorio nativa con interfaz gráfica construida en **Python + PySide6 (Qt6)**.
- `models.py`: Lógica completa de negocio para manejo de archivos locales **JSON** (`datos/registros.json`) y **CSV** (`datos/catalogo_inicial.csv`), validaciones, estadísticas y respaldos transaccionales.
- `worker_service.py`: Servicio de trabajo en segundo plano (`QThread` Worker Service) que recolecta métricas de hardware del equipo (CPU, RAM, Disco, SO) y ejecuta respaldos automáticos sin bloquear la ventana principal.
- `manifest.json`: Manifiesto completo compatible tanto con la configuración nativa de escritorio como con instalación Web/PWA (`display: standalone`, íconos, manejadores de archivos `.json` y `.csv`).
- `service-worker.js` y `worker-service.js`: Service Worker con caché local completo (`Cache-First`) para funcionamiento sin Internet e instalación desde navegador.
- `index.html`, `app.js`, `styles.css`: Interfaz instalable PWA de escritorio lista para abrir o instalar en un clic.
- `datos/registros.json` y `datos/catalogo_inicial.csv`: Bases de datos locales pre-pobladas y sincronizadas.
- `datos/actualizacion_local.json`: Paquete de actualización local para probar el flujo de actualización sin Internet.
- `icons/`: Íconos PNG (`icon-192.png`, `icon-512.png`, `app_icon.png`).
- `requirements.txt`, `instalar_y_ejecutar.bat`, `instalar_y_ejecutar.sh`: Scripts de instalación y arranque directo.

## Cómo Ejecutar la Aplicación Nativa (Python + PySide6)

### En Windows:
Haz doble clic en `instalar_y_ejecutar.bat` o ejecuta en terminal:
```bash
pip install -r requirements.txt
python main.py
```

### En Linux / macOS:
```bash
chmod +x instalar_y_ejecutar.sh
./instalar_y_ejecutar.sh
```

### Para generar un ejecutable instalable (`.exe`) en Windows:
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --icon=icons/app_icon.png --name="DeskDataPro" main.py
```

## Cómo Ejecutar o Instalar la Versión con Manifest y Service Worker (PWA de Escritorio)

```bash
python -m http.server 8080
```
Abre `http://localhost:8080` en Chrome o Edge y haz clic en **"Instalar en Escritorio"**.
