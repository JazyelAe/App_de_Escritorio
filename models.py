#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
models.py - Lógica de negocio y persistencia de datos locales (JSON y CSV).
Permite trabajar con archivos almacenados directamente en la computadora sin necesidad de Internet.
"""

import csv
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class LocalDataManager:
    """Gestor de almacenamiento local para archivos JSON y CSV con respaldo transaccional."""

    REQUIRED_FIELDS = [
        "id",
        "nombre",
        "categoria",
        "estado",
        "cantidad",
        "precio_unitario",
        "ubicacion",
        "ultima_actualizacion",
        "notas",
    ]

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent
        self.data_dir = self.base_dir / "datos"
        self.backups_dir = self.data_dir / "respaldos"
        self.json_path = self.data_dir / "registros.json"
        self.csv_path = self.data_dir / "catalogo_inicial.csv"
        self.manifest_path = self.base_dir / "manifest.json"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_initial_files()

    def _ensure_initial_files(self) -> None:
        """Garantiza que los archivos JSON y CSV locales existan en el equipo."""
        if not self.json_path.exists():
            default_data = self._get_seed_data()
            self.save_to_json(default_data, self.json_path)
        if not self.csv_path.exists():
            records = self.load_from_json(self.json_path)
            self.export_to_csv(records, self.csv_path)

    @staticmethod
    def _get_seed_data() -> List[Dict]:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [
            {
                "id": "INV-001",
                "nombre": "Estación de Trabajo Portátil Pro 16",
                "categoria": "Hardware",
                "estado": "Activo",
                "cantidad": 12,
                "precio_unitario": 24500.00,
                "ubicacion": "Almacén Central - Estante A1",
                "ultima_actualizacion": now_str,
                "notas": "Equipo configurado para desarrollo local con Python y Qt.",
            },
            {
                "id": "INV-002",
                "nombre": "Monitor UltraWide 34 Pulgadas IPS",
                "categoria": "Periféricos",
                "estado": "Activo",
                "cantidad": 8,
                "precio_unitario": 8900.50,
                "ubicacion": "Almacén Central - Estante B2",
                "ultima_actualizacion": now_str,
                "notas": "Calibrado de fábrica para diseño de interfaces.",
            },
            {
                "id": "INV-003",
                "nombre": "Servidor NAS Local 4 Bahías 16TB",
                "categoria": "Almacenamiento",
                "estado": "Activo",
                "cantidad": 3,
                "precio_unitario": 18200.00,
                "ubicacion": "Sala de Servidores - Rack 1",
                "ultima_actualizacion": now_str,
                "notas": "Respaldo automático sin conexión a Internet (Red Local).",
            },
        ]

    def normalize_record(self, raw: Dict) -> Dict:
        """Normaliza y valida los tipos de datos de un registro individual."""
        try:
            cantidad = int(float(str(raw.get("cantidad", 0)).strip() or 0))
        except ValueError:
            cantidad = 0

        try:
            precio = round(float(str(raw.get("precio_unitario", 0.0)).strip() or 0.0), 2)
        except ValueError:
            precio = 0.0

        return {
            "id": str(raw.get("id", "")).strip() or f"INV-{int(datetime.now().timestamp())}",
            "nombre": str(raw.get("nombre", "Sin nombre")).strip(),
            "categoria": str(raw.get("categoria", "General")).strip(),
            "estado": str(raw.get("estado", "Activo")).strip(),
            "cantidad": max(0, cantidad),
            "precio_unitario": max(0.0, precio),
            "ubicacion": str(raw.get("ubicacion", "Local")).strip(),
            "ultima_actualizacion": str(
                raw.get("ultima_actualizacion") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ).strip(),
            "notas": str(raw.get("notas", "")).strip(),
        }

    def load_from_json(self, file_path: Optional[Path] = None) -> List[Dict]:
        """Carga registros desde un archivo JSON local."""
        target = Path(file_path) if file_path else self.json_path
        if not target.exists():
            return []
        with open(target, "r", encoding="utf-8") as f:
            content = json.load(f)
        if isinstance(content, dict) and "registros" in content:
            raw_list = content["registros"]
        elif isinstance(content, list):
            raw_list = content
        else:
            raw_list = []
        return [self.normalize_record(item) for item in raw_list if isinstance(item, dict)]

    def save_to_json(self, records: List[Dict], file_path: Optional[Path] = None) -> Path:
        """Guarda los registros en formato JSON de forma atómica."""
        target = Path(file_path) if file_path else self.json_path
        target.parent.mkdir(parents=True, exist_ok=True)
        normalized = [self.normalize_record(r) for r in records]
        payload = {
            "metadata": {
                "aplicacion": "DeskData Pro (Python + PySide6)",
                "formato": "JSON Local Database",
                "ultima_escritura": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_registros": len(normalized),
            },
            "registros": normalized,
        }
        temp_file = target.with_suffix(".tmp.json")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, target)
        return target

    def export_to_csv(self, records: List[Dict], file_path: Optional[Path] = None) -> Path:
        """Exporta la lista de registros a un archivo CSV estándar codificado en UTF-8."""
        target = Path(file_path) if file_path else self.csv_path
        target.parent.mkdir(parents=True, exist_ok=True)
        normalized = [self.normalize_record(r) for r in records]
        with open(target, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.REQUIRED_FIELDS)
            writer.writeheader()
            for row in normalized:
                writer.writerow(row)
        return target

    def import_from_csv(self, file_path: Path) -> List[Dict]:
        """Importa registros desde un archivo CSV almacenado en la computadora."""
        target = Path(file_path)
        if not target.exists():
            raise FileNotFoundError(f"No se encontró el archivo CSV: {target}")
        imported = []
        with open(target, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if any(row.values()):
                    imported.append(self.normalize_record(row))
        return imported

    def create_local_backup(self, records: List[Dict]) -> Path:
        """Crea una copia de seguridad local con marca de tiempo en la carpeta de respaldos."""
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backups_dir / f"respaldo_{stamp}.json"
        self.save_to_json(records, backup_file)
        # Mantener solo los últimos 10 respaldos locales para cuidar el almacenamiento
        backups = sorted(self.backups_dir.glob("respaldo_*.json"))
        while len(backups) > 10:
            oldest = backups.pop(0)
            oldest.unlink(missing_ok=True)
        return backup_file

    def compute_statistics(self, records: List[Dict]) -> Dict:
        """Calcula métricas e indicadores locales del inventario/dataset."""
        total_items = len(records)
        total_unidades = sum(int(r.get("cantidad", 0)) for r in records)
        valor_total = sum(
            int(r.get("cantidad", 0)) * float(r.get("precio_unitario", 0.0)) for r in records
        )
        bajo_stock = sum(
            1 for r in records if int(r.get("cantidad", 0)) <= 5 or r.get("estado") == "Bajo Stock"
        )
        categorias: Dict[str, int] = {}
        for r in records:
            cat = r.get("categoria", "General")
            categorias[cat] = categorias.get(cat, 0) + 1

        return {
            "total_registros": total_items,
            "total_unidades": total_unidades,
            "valor_inventario": round(valor_total, 2),
            "alertas_bajo_stock": bajo_stock,
            "categorias": categorias,
        }

    def load_manifest(self) -> Dict:
        """Lee el archivo manifest.json local con la configuración de la aplicación."""
        if self.manifest_path.exists():
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"name": "DeskData Pro", "version": "2.1.0", "offline_enabled": True}
