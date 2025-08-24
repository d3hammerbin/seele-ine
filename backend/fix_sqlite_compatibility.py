#!/usr/bin/env python3
"""
Script para hacer los modelos compatibles con SQLite reemplazando JSONB con JSON.
"""

import os
import re

def fix_model_file(file_path):
    """Reemplazar JSONB con JSON y UUID con String en un archivo de modelo."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Reemplazar la importación
    content = content.replace(
        'from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB',
        'from sqlalchemy.dialects.postgresql import UUID as PostgresUUID\nfrom sqlalchemy import JSON'
    )
    
    content = content.replace(
        'from sqlalchemy.dialects.postgresql import UUID as PostgresUUID\nfrom sqlalchemy import JSON',
        'from sqlalchemy.dialects.postgresql import UUID as PostgresUUID\nfrom sqlalchemy import JSON'
    )
    
    # Reemplazar JSONB con JSON
    content = re.sub(r'\bJSONB\b', 'JSON', content)
    
    # Reemplazar PostgresUUID() y PostgresUUID(as_uuid=True) con String(36) para SQLite
    content = re.sub(r'PostgresUUID\(\)', 'String(36)', content)
    content = re.sub(r'PostgresUUID\(as_uuid=True\)', 'String(36)', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Archivo actualizado: {file_path}")

def main():
    """Actualizar todos los archivos de modelo."""
    models_dir = 'app/infrastructure/database/models'
    
    model_files = [
        'user.py',
        'application.py',
        'billing.py',
        'credential.py',
        'processing_job.py'
    ]
    
    for model_file in model_files:
        file_path = os.path.join(models_dir, model_file)
        if os.path.exists(file_path):
            fix_model_file(file_path)
        else:
            print(f"⚠️ Archivo no encontrado: {file_path}")
    
    print("\n✅ Todos los modelos han sido actualizados para compatibilidad con SQLite")

if __name__ == "__main__":
    main()