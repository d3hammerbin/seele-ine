#!/usr/bin/env python3
"""
Script para ejecutar migraciones de Alembic con PostgreSQL
sin modificar el archivo .env principal.

Uso:
    python run_migrations_postgres.py

Este script:
1. Configura las variables de entorno para PostgreSQL
2. Verifica que PostgreSQL esté disponible
3. Ejecuta las migraciones de Alembic
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_postgres_env():
    """Configura las variables de entorno para usar PostgreSQL"""
    # Leer configuración del .env
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    # Configurar URLs de PostgreSQL para Alembic
    host = os.environ.get('POSTGRES_HOST', 'localhost')
    port = os.environ.get('POSTGRES_PORT', '5432')
    db = os.environ.get('POSTGRES_DB', 'seele_ine_db')
    user = os.environ.get('POSTGRES_USER', 'seele_user')
    password = os.environ.get('POSTGRES_PASSWORD', 'seele_secure_password_2024')
    
    # URL síncrona para Alembic
    sync_postgres_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    os.environ['DATABASE_URL'] = sync_postgres_url
    os.environ['SYNC_DATABASE_URL'] = sync_postgres_url
    
    return sync_postgres_url

def check_postgres_connection():
    """Verifica que PostgreSQL esté disponible"""
    print("🔍 Verificando conexión a PostgreSQL...")
    
    try:
        # Verificar si el contenedor PostgreSQL está ejecutándose
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=postgres', '--format', '{{.Names}}'],
            capture_output=True, text=True, timeout=10
        )
        
        if 'postgres' in result.stdout:
            print("✅ Contenedor PostgreSQL encontrado y ejecutándose")
            return True
        else:
            print("⚠️  Contenedor PostgreSQL no encontrado")
            print("💡 Sugerencia: Ejecuta 'docker-compose up -d postgres' para iniciar PostgreSQL")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout verificando Docker")
        return False
    except FileNotFoundError:
        print("⚠️  Docker no está disponible")
        return True  # Asumir que está disponible si no hay Docker
    except Exception as e:
        print(f"❌ Error verificando PostgreSQL: {e}")
        return False

def run_migrations():
    """Ejecuta las migraciones de Alembic"""
    print("🔄 Ejecutando migraciones de Alembic...")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'alembic', 'upgrade', 'head'],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("✅ Migraciones ejecutadas exitosamente")
            if result.stdout:
                print("📋 Salida:")
                print(result.stdout)
            return True
        else:
            print("❌ Error ejecutando migraciones")
            if result.stderr:
                print("🔍 Error:")
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando Alembic: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 SEELE-INE - Migraciones PostgreSQL")
    print("=" * 40)
    
    # Cambiar al directorio del script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Configurar variables de entorno
    db_url = setup_postgres_env()
    print(f"📍 Base de datos: {db_url}")
    
    # Verificar conexión a PostgreSQL
    if not check_postgres_connection():
        print("\n❌ No se puede conectar a PostgreSQL")
        print("💡 Opciones:")
        print("   1. Ejecutar: docker-compose up -d postgres")
        print("   2. Verificar que PostgreSQL esté ejecutándose")
        sys.exit(1)
    
    # Ejecutar migraciones
    if run_migrations():
        print("\n🎉 Migraciones completadas exitosamente")
    else:
        print("\n❌ Error en las migraciones")
        sys.exit(1)

if __name__ == '__main__':
    main()