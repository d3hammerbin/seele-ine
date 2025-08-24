#!/usr/bin/env python3
"""
Script para crear la base de datos SQLite con todas las tablas necesarias.
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

# Cargar variables de entorno
load_dotenv()

# Importar los modelos
from app.infrastructure.database.base import Base
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.models.application import ApplicationModel
from app.infrastructure.database.models.processing_job import ProcessingJobModel
from app.infrastructure.database.models.credential import CredentialModel
from app.infrastructure.database.models.billing import BillingModel

async def create_database():
    """Crear la base de datos SQLite con todas las tablas."""
    database_url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./seele_dev.db')
    
    # Crear engine asíncrono
    engine = create_async_engine(database_url, echo=True)
    
    try:
        # Crear todas las tablas
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Base de datos SQLite creada exitosamente")
        
    except Exception as e:
        print(f"❌ Error al crear la base de datos: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_database())