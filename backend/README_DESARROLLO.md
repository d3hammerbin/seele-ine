# SEELE-INE Backend - Guía de Desarrollo

## Ejecución Local para Desarrollo

Para facilitar las pruebas locales sin afectar la configuración de Docker, se han creado scripts especializados que permiten ejecutar el backend con diferentes bases de datos.

### Scripts Disponibles

#### 1. Ejecución con SQLite (Recomendado para desarrollo)

```bash
python run_with_sqlite.py
```

**Características:**
- ✅ No requiere Docker ni PostgreSQL
- ✅ Base de datos local en archivo `seele_dev.db`
- ✅ Configuración automática de variables de entorno
- ✅ Creación automática de la base de datos si no existe
- ✅ Ideal para desarrollo y pruebas rápidas

#### 2. Ejecución con PostgreSQL

```bash
python run_with_postgres.py
```

**Características:**
- 🐘 Usa PostgreSQL como base de datos
- 🐳 Requiere que PostgreSQL esté ejecutándose (Docker recomendado)
- ✅ Verificación automática de conexión
- ✅ Configuración automática desde el archivo `.env`
- ⚠️ Requiere `docker-compose up -d postgres` si usas Docker

#### 3. Migraciones de PostgreSQL

```bash
python run_migrations_postgres.py
```

**Características:**
- 🔄 Ejecuta migraciones de Alembic con PostgreSQL
- ✅ Configura automáticamente las variables de entorno
- ✅ Verifica que PostgreSQL esté disponible
- ✅ Crea todas las tablas necesarias en la base de datos
- ⚠️ Ejecutar antes del primer uso con PostgreSQL

### Ventajas de estos Scripts

1. **No modifican el archivo `.env`**: La configuración original se mantiene intacta para Docker
2. **Configuración automática**: Las variables de entorno se configuran dinámicamente
3. **Verificaciones integradas**: Comprueban que todo esté listo antes de iniciar
4. **Mensajes informativos**: Proporcionan feedback claro sobre el estado del sistema
5. **Manejo de errores**: Guían al usuario sobre cómo resolver problemas comunes

### Flujo de Trabajo Recomendado

#### Para Desarrollo Rápido
```bash
# Navegar al directorio backend
cd backend

# Ejecutar con SQLite (más rápido)
python run_with_sqlite.py
```

#### Para Pruebas con PostgreSQL
```bash
# Iniciar PostgreSQL con Docker
docker-compose up -d postgres

# Navegar al directorio backend
cd backend

# Ejecutar migraciones (solo la primera vez o después de cambios en modelos)
python run_migrations_postgres.py

# Ejecutar con PostgreSQL
python run_with_postgres.py
```

#### Para Producción/Docker
```bash
# Usar docker-compose normalmente
docker-compose up -d
```

### Solución de Problemas

#### Error de conexión a PostgreSQL
```bash
# Verificar que PostgreSQL esté ejecutándose
docker ps | grep postgres

# Si no está ejecutándose, iniciarlo
docker-compose up -d postgres

# Verificar logs de PostgreSQL
docker logs seele_ine_postgres
```

#### Error con SQLite
```bash
# Eliminar base de datos corrupta
rm seele_dev.db

# El script recreará la base de datos automáticamente
python run_with_sqlite.py
```

### Estructura de Archivos

```
backend/
├── main.py                 # Aplicación principal
├── run_with_sqlite.py      # Script para SQLite
├── run_with_postgres.py    # Script para PostgreSQL
├── create_sqlite_db.py     # Creación de BD SQLite
├── seele_dev.db           # Base de datos SQLite (generada)
└── README_DESARROLLO.md    # Esta guía
```

### Variables de Entorno

Los scripts manejan automáticamente estas variables:

- **SQLite**: `DATABASE_URL=sqlite+aiosqlite:///./seele_dev.db`
- **PostgreSQL**: Construida desde `POSTGRES_HOST`, `POSTGRES_PORT`, etc.

### Notas Importantes

- ⚠️ **No modifiques el archivo `.env`** para pruebas locales
- ✅ **Usa estos scripts** para desarrollo local
- 🐳 **Usa docker-compose** para despliegue
- 📝 **Los logs** se muestran en tiempo real durante la ejecución