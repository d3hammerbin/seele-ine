#!/usr/bin/env python3
"""
Script simple para crear un usuario de prueba en SQLite
"""

import asyncio
import os
from uuid import uuid4
from datetime import datetime

# Configurar la variable de entorno para SQLite
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./seele_ine.db'

from app.infrastructure.database.session import get_async_db_context
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.database.models.user import UserModel

async def create_test_user():
    """Crear un usuario de prueba simple"""
    
    # Inicializar el gestor de base de datos
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    try:
        async with get_async_db_context() as session:
            print("🔄 Creando usuario de prueba...")
            
            # Crear usuario con hash de contraseña simple (para pruebas)
            user = UserModel(
                id=str(uuid4()),
                email="test@example.com",
                username="testuser",
                password_hash="$2b$12$test_hash_for_development_only",  # Hash fijo para pruebas
                first_name="Test",
                last_name="User",
                phone="+1234567890",
                role="USER",
                status="ACTIVE",
                subscription_plan="FREE",
                email_verified=True,
                two_factor_enabled=False,
                login_count=0,
                preferences={"theme": "light", "language": "en"},
                statistics={"total_logins": 0},
                extra_metadata={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Agregar y confirmar
            session.add(user)
            await session.commit()
            
            print(f"✅ Usuario creado exitosamente:")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   ID: {user.id}")
            
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
        raise
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())