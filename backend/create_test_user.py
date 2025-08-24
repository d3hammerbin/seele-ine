#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from app.infrastructure.database.session import get_session_manager
from app.infrastructure.database.models.user import UserModel
from app.core.security.jwt_service import JWTService
from app.infrastructure.database.connection import DatabaseManager
from datetime import datetime
from uuid import uuid4

async def create_test_user():
    """Crear un usuario de prueba en la base de datos SQLite."""
    
    # Inicializar el database manager
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # Obtener session manager y crear sesión
    session_manager = get_session_manager()
    session_manager.initialize(db_manager.engine)
    session = session_manager.get_session()
    
    try:
        # Crear usuario directamente (SQLite manejará duplicados con UNIQUE constraint)
        print("🔄 Creando usuario de prueba...")
        
        # Crear hash de la contraseña
        jwt_service = JWTService()
        password_hash = jwt_service.hash_password("password123")
        
        # Crear usuario de prueba
        test_user = UserModel(
            id=str(uuid4()),
            email="test@example.com",
            username="testuser",
            password_hash=password_hash,
            first_name="Test",
            last_name="User",
            phone="+1234567890",
            role="user",
            status="active",
            subscription_plan="free",
            email_verified=True,
            two_factor_enabled=False,
            login_count=0,
            preferences={"theme": "light", "language": "en"},
            statistics={"total_logins": 0},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(test_user)
        await session.commit()
        
        print("✅ Usuario de prueba creado exitosamente:")
        print(f"   Email: test@example.com")
        print(f"   Password: password123")
        print(f"   ID: {test_user.id}")
        
    except Exception as e:
        await session.rollback()
        print(f"❌ Error al crear usuario de prueba: {e}")
        raise
    finally:
        await session.close()
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())