#!/usr/bin/env python3
"""
Script para ejecutar el backend con PostgreSQL para pruebas locales
sin modificar el archivo .env principal.

Uso:
    python run_with_postgres.py

Este script:
1. Configura las variables de entorno para usar PostgreSQL
2. Verifica que PostgreSQL esté ejecutándose
3. Ejecuta el servidor backend
"""

import os
import sys
import subprocess
import time
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
    
    # Asegurar que se use PostgreSQL (no SQLite)
    if 'DATABASE_URL' in os.environ and 'sqlite' in os.environ['DATABASE_URL']:
        # Construir URL de PostgreSQL desde las variables individuales
        host = os.environ.get('POSTGRES_HOST', 'localhost')
        port = os.environ.get('POSTGRES_PORT', '5432')
        db = os.environ.get('POSTGRES_DB', 'seele_ine')
        user = os.environ.get('POSTGRES_USER', 'seele_user')
        password = os.environ.get('POSTGRES_PASSWORD', 'seele_password_2024')
        
        postgres_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
        sync_postgres_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        
        os.environ['DATABASE_URL'] = postgres_url
        os.environ['SYNC_DATABASE_URL'] = sync_postgres_url

def check_postgres_connection():
    """Verifica que PostgreSQL esté disponible"""
    print("🔍 Verificando conexión a PostgreSQL...")
    
    host = os.environ.get('POSTGRES_HOST', 'localhost')
    port = os.environ.get('POSTGRES_PORT', '5432')
    
    try:
        # Intentar conectar usando docker si está disponible
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
        print(f"🔍 Intentando conectar directamente a {host}:{port}")
        return True  # Asumir que está disponible si no hay Docker
    except Exception as e:
        print(f"❌ Error verificando PostgreSQL: {e}")
        return False

def run_backend():
    """Ejecuta el servidor backend"""
    print("🚀 Iniciando servidor backend con PostgreSQL...")
    print(f"📍 Base de datos: PostgreSQL ({os.environ.get('POSTGRES_HOST', 'localhost')}:{os.environ.get('POSTGRES_PORT', '5432')})")
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
    print("🔧 SEELE-INE Backend - Modo PostgreSQL para Desarrollo")
    print("=" * 50)
    
    # Cambiar al directorio del script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Configurar variables de entorno
    setup_postgres_env()
    
    # Verificar conexión a PostgreSQL
    if not check_postgres_connection():
        print("\n❌ No se puede conectar a PostgreSQL")
        print("💡 Opciones:")
        print("   1. Ejecutar: docker-compose up -d postgres")
        print("   2. Usar SQLite: python run_with_sqlite.py")
        sys.exit(1)
    
    # Ejecutar el backend
    run_backend()

if __name__ == '__main__':
    main()