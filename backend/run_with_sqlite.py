#!/usr/bin/env python3
"""
Script para ejecutar el backend con SQLite para pruebas locales
sin modificar el archivo .env principal.

Uso:
    python run_with_sqlite.py

Este script:
1. Configura las variables de entorno para usar SQLite
2. Crea la base de datos SQLite si no existe
3. Ejecuta el servidor backend
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_sqlite_env():
    """Configura las variables de entorno para usar SQLite"""
    # Configurar variables de entorno para SQLite
    os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./seele_dev.db'
    os.environ['SYNC_DATABASE_URL'] = 'sqlite:///./seele_dev.db'
    
    # Mantener otras configuraciones del .env original
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # No sobrescribir las URLs de base de datos
                    if key not in ['DATABASE_URL', 'SYNC_DATABASE_URL']:
                        os.environ[key] = value

def create_sqlite_db():
    """Crea la base de datos SQLite si no existe"""
    db_file = Path('./seele_dev.db')
    if not db_file.exists():
        print("📦 Creando base de datos SQLite...")
        try:
            result = subprocess.run([sys.executable, 'create_sqlite_db.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Base de datos SQLite creada exitosamente")
            else:
                print(f"❌ Error creando la base de datos: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error ejecutando create_sqlite_db.py: {e}")
            return False
    else:
        print("📦 Base de datos SQLite ya existe")
    return True

def run_backend():
    """Ejecuta el servidor backend"""
    print("🚀 Iniciando servidor backend con SQLite...")
    print("📍 Base de datos: SQLite (seele_dev.db)")
    print("🌐 URL: http://localhost:8000")
    print("⏹️  Presiona Ctrl+C para detener el servidor")
    print("-" * 50)
    
    try:
        subprocess.run([sys.executable, 'main.py'])
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error ejecutando el servidor: {e}")
        return False
    return True

def main():
    """Función principal"""
    print("🔧 SEELE-INE Backend - Modo SQLite para Desarrollo")
    print("=" * 50)
    
    # Cambiar al directorio del script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Configurar variables de entorno
    setup_sqlite_env()
    
    # Crear base de datos SQLite si es necesario
    if not create_sqlite_db():
        sys.exit(1)
    
    # Ejecutar el backend
    run_backend()

if __name__ == '__main__':
    main()