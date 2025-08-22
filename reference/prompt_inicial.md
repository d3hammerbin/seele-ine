Vamos a desarrollar un sistema para obtener la información de las credenciales de identificación mexicana INE, lo que tiene que hacer el sistema es leer las credenciales para votar mexicanas, clasificarlas, tratarlas y extraer el contenido tanto de frente como el reverso, existen 3 tipos de credenciales activas, las credenciales tienen un tamaño muy específico que es 790px de ancho y 490px de alto, esto aplica para los 3 tipos, sin embargo hay diferencias entre estos que radica en marcadores que adornan la credencial así como organización de algunos datos, por lo cual de primera instancia el sistema debe de tener la habilidad para poder distinguir entre estos 3 tipos, los cambios son por ambos lados tanto de frente como de reverso, por lo cual lo primero es identificar el tipo.

Para los tipos 1 y 2 de la parte trasera se va a obtener un código QR el cual es muy importante obtenerlo, en caso de no poderlo leer/obtener se notificará como credencial inválida lo cual forzará a que se tenga que volver a proporcionar la credencial con mejor calidad, para el tipo 3 hay un solo dato que es de tipo texto/numérico.

Para los 3 tipos de credenciales se van a obtener datos muy concretos los cuales describiremos a continuación:
    Tipo 1:
        Delantera:
            - Nombre
            - Sexo
            - Domicilio (En este tipo es opcional ya que hay credenciales que ya no tienen este campo)
            - Clave de elector (Obligatorio)
            - Curp (Obligatorio)
            - Año de registro
            - Fecha de nacimiento
            - Seccion (Obligatorio)
            - Vigencia
        Trasera:
            - QR (Obligatorio)
            - MRZ (Opcional)
    Tipo 2:
        Delantera:
            - Nombre
            - Fecha de nacimiento
            - Sexo
            - Domicilio
            - Clave de elector (Obligatorio)
            - Curp (Obligatorio)
            - Año de registro
            - Estado
            - Municipio
            - Seccion (Obligatorio)
            - Localidad
            - Emision
            - Vigencia
        Trasera:
            - QR (Obligatorio)
            - MRZ (Opcional)
    Tipo 3:
        Delantera:
            - Nombre
            - Edad
            - Sexo
            - Domicilio
            - Folio
            - Año de registro
            - Clave de elector (Obligatorio)
            - Curp (Obligatorio)
            - Estado
            - Municipio
            - Localidad
            - Seccion (Obligatorio)
            - Emision
            - Vigencia Hasta

Cada credencial consta de dos lados, la delantera y la trasera, si alguno de los campos obligatorios de los dos lados no se puede obtener se notificará como credencial inválida lo cual forzará a que se tenga que volver a proporcionar la credencial con mejor calidad.

Como nota importante hay que implementar un método para distinguir entre los 3 tipos, también hay que tomar en cuenta que lo primero a validar es que la imagen cumple exactamente las dimensiones proporcionadas que son de 790px de ancho y 490px de alto, si no cumple con estas dimensiones se notificará como credencial inválida.

El stack tecnológico sería el siguiente:
    Backend: FastAPI + asyncpg + SQLAlchemy
    Frontend: React + Redux + Tailwind CSS (La aplicación será una aplicación SPA - Single Page Application)
    Database: PostgreSQL
    Servicio de OCR: OpenAI Vision API (De ser posible hay que utilizar el sdk oficial) + Tesseract + OpenCV2 + pyzbar
    Orquestación: Docker + Docker Compose

## 🐳 Configuración Docker

### Docker Compose:
- **Servicios principales**:
  - `postgres`: Base de datos PostgreSQL con volumen persistente en `./psgs`
  - `backend`: API FastAPI con multi-stage build
  - `frontend`: Aplicación React con multi-stage build
  - `redis`: Cache para optimización (opcional)

### Multi-Stage Builds:
- **Backend**: 
  - Stage 1: Instalación de dependencias y build
  - Stage 2: Runtime optimizado con imagen Python slim
- **Frontend**:
  - Stage 1: Build de la aplicación React
  - Stage 2: Servidor nginx con archivos estáticos

### Volúmenes y Persistencia:
- `./psgs:/var/lib/postgresql/data`: Datos de PostgreSQL
- `./credentials:/app/credentials`: Credenciales de prueba
- `./logs:/app/logs`: Logs de la aplicación

### Optimizaciones Docker:
- Uso de `.dockerignore` para reducir contexto de build
- Capas optimizadas para mejor caching
- Imágenes base oficiales y seguras
- Health checks para todos los servicios
- Restart policies configuradas

Arquitectura:
    - Vamos a utilizar clean Architecture para el backend.

Importante:
    - Esta aplicación va a ser ejecutada en un contenedor docker-compose.yml
    - Tener en cuenta que el backend va a ser una API REST.
    - Es primordial que tanto base de datos, como backend y frontend tienen que utilizar el Time Zone America/Mexico_City.
    - Aunque el sistema va tener en su momento pruebas unitarias así como de integración estas no van a ser implementadas aún.
    - Para la lectura y extracción del QR contamos con un script probado que se llama qr_extractor_pro.py que está localizado en la carpeta de references/ toma ese script y aplícalo para la lectura de las credenciales tipo 1 y 2.
    - Para la extracción de los datos de la parte delantera utilizaremos lo que está definido en la sección de stack tecnológico del apartado "Servicio de OCR".
    - Para el tema de la extracción hay que priorizar los métodos de extracción local, en caso de que no se puedan extraer o no sea válida o haya posibilidad de que los datos no se hayan extraído correctamente lo intentaremos mediante APIs de IA (OpenAI, DeepSeek, Gemini, Claude, etc.), el modelo a utilizar será configurable por el administrador.
    - El sistema debe ser flexible para soportar múltiples proveedores de IA: OpenAI, DeepSeek, Gemini (Google), Claude (Anthropic), y otros que puedan agregarse en el futuro.
    - La selección del modelo de IA será gestionada exclusivamente por el administrador del sistema, no por el usuario final.
    - Cada proveedor de IA tendrá su propia configuración de precios, límites y características específicas.
    - Recuerda que es imperativo que las versiones sean las más recientes compatibles y de preferencia LTS de existir, haz una búsqueda para asegurarte de cuáles son las versiones más recientes compatibles esto con más importancia en el Frontend.
    - Para todos los temas relacionados con devolver listados de ítems hay que considerar que utilizaremos paginación del tipo lazy loading.
     - Para el tema de login este tiene que utilizar JWT para la autenticación, también este contará con refresh token.
    - Una vez que el usuario esté registrado y activado hay que permitirle crear y generar unas claves (CLIENT_KEY y CLIENT_SECRET) para poder utilizar la API mediante una aplicación.

Costos:
    - El sistema debe registrar y controlar el consumo de tokens/créditos de múltiples proveedores de IA para cada petición realizada por aplicación registrada.
    - Cada intento/uso de APIs de IA debe generar un historial de consumo detallado por petición, incluyendo:
        - Extracción y decodificación de códigos QR
        - Extracción de información de la parte frontal de credenciales
        - Extracción de información de la parte trasera de credenciales
        - Cualquier otra consulta a APIs de IA (OpenAI, DeepSeek, Gemini, Claude, etc.)
    - El historial interno (solo para administradores) debe incluir:
        - Timestamp de la petición
        - Usuario que realizó la petición
        - Aplicación registrada que consumió el servicio
        - Proveedor de IA utilizado (OpenAI, DeepSeek, Gemini, Claude, etc.)
        - Modelo específico utilizado (GPT-4V, DeepSeek-VL, Gemini-Pro-Vision, Claude-3-Vision, etc.)
        - Tipo de operación (QR, OCR frontal, OCR trasero, etc.)
        - Cantidad de tokens/créditos consumidos (input y output)
        - Costo en moneda original del proveedor (USD, CNY, etc.)
        - Costo convertido a pesos mexicanos
        - Costo final aplicado a la aplicación (con multiplicador)
        - Estado de la petición (exitosa, fallida, parcial)
        - Tiempo de respuesta del proveedor
    - Vista de la aplicación (solo costo final):
        - Fecha y hora de la petición
        - Tipo de operación realizada
        - Costo final en pesos mexicanos
        - Estado de la operación (exitosa/fallida)
        - Sin detalles técnicos del modelo o proveedor utilizado
    - Sistema de configuración de precios multi-proveedor:
        - Precios actuales por proveedor, modelo y tipo de token/crédito
        - Tipos de cambio múltiples (USD/MXN, CNY/MXN, EUR/MXN, etc.)
        - Multiplicador de ganancia configurable por administrador y por proveedor
        - Diferentes tarifas por tipo de aplicación (básica, premium, enterprise)
        - Configuración de prioridad de proveedores (fallback automático)
    - Control de límites:
        - Límite de tokens por aplicación por día/mes
        - Límite de gasto por aplicación
        - Alertas cuando se alcance el 80% del límite
        - Bloqueo automático al alcanzar el 100% del límite
    - Reportes de consumo:
         - Reporte diario/mensual de consumo por aplicación
         - Reporte diario/mensual de consumo por usuario
         - Reporte cruzado usuario-aplicación con trazabilidad completa
         - Reporte de costos totales del sistema
         - Análisis de rentabilidad por tipo de operación
         - Análisis de uso por proveedor de IA
        - Exportación de reportes en CSV/PDF

Áreas de la Aplicación:
    ## 👨‍💼 Área de Administración (Solo Administradores)
    - Gestión de proveedores de IA y modelos disponibles
    - Configuración de precios por proveedor y modelo
    - Gestión de tipos de cambio de múltiples monedas
    - Configuración de multiplicadores de ganancia
    - Gestión de tipos de usuario y tarifas
    - Configuración de límites globales del sistema
    - Reportes financieros y de consumo
    - Gestión de usuarios (activar, desactivar, modificar límites)
    - Configuración de prioridades de proveedores (fallback)
    - Monitoreo del sistema y logs de errores
    - Configuración de alertas y notificaciones
    - Gestión de versiones y actualizaciones del sistema
    
    ## 👤 Área de Usuario (Usuarios Finales)
    - Procesamiento de credenciales INE
    - Visualización de historial de procesamiento
    - Gestión de perfil personal
    - Generación y gestión de API Keys (CLIENT_KEY y CLIENT_SECRET)
    - Consulta de consumo y costos personales
    - Consulta de límites y saldo disponible
    - Recarga de saldo (si aplica)
    - Descarga de reportes personales
    - Configuración de notificaciones personales
    
    **Nota Importante**: Los usuarios NO pueden seleccionar el proveedor de IA o modelo a utilizar. Esta configuración es exclusiva del administrador y se aplica de forma automática según las reglas establecidas por el sistema.

/:  
    - En el directorio raíz crearemos los archivos de configuración como el .env, docker-compose.yml y otros requeridos.
    - Archivo README.md (Si este ya existe lo actualizaremos), para este archivo hay que agregar un badge con la versión de nuestra aplicación la cual comenzará en 0.0.0-Alpha, así como badges de las versiones de las tecnologías que estamos utilizando.
    - Archivo CHANGELOG.md:
      - Changelog Management:
        - **Keep a Changelog** format
        - Generación automática desde commits
        - Categorías: Added, Changed, Deprecated, Removed, Fixed, Security
        - Links a issues y pull requests
        
        Estructura:
            ```
            # Changelog
            
            ## [1.2.0] - 2024-01-15
            ### Added
            - Nueva funcionalidad de gestión de usuarios
            - Endpoint para exportar configuraciones
            
            ### Changed
            - Mejorado performance de queries de servidores
            
            ### Fixed
            - Corregido bug en paginación
            ```

## 📁 Estructura de Carpetas del Proyecto

### Carpetas Principales:
- **backend/**: Contiene toda la lógica del servidor FastAPI
- **frontend/**: Aplicación React SPA
- **psgs/**: Datos persistentes de PostgreSQL (volumen Docker)
- **credentials/**: Almacenamiento de credenciales de prueba
  - **t1/**: Credenciales tipo 1
  - **t2/**: Credenciales tipo 2  
  - **t3/**: Credenciales tipo 3
  - **uncategorized/**: Credenciales sin clasificar
- **scripts/**: Scripts de utilidad y gestión
- **logo/**: Recursos gráficos del sistema
- **reference/**: Documentación y archivos de referencia

### Archivos .gitkeep:
Todas las carpetas del proyecto incluyen archivos `.gitkeep` para mantener la estructura en el repositorio Git, especialmente las carpetas que inicialmente estarán vacías:
- `backend/.gitkeep`
- `frontend/.gitkeep`
- `psgs/.gitkeep`
- `credentials/.gitkeep`
- `credentials/t1/.gitkeep`
- `credentials/t2/.gitkeep`
- `credentials/t3/.gitkeep`
- `credentials/uncategorized/.gitkeep`
- `scripts/.gitkeep`
Version Management:
    1. **Backend (Python)**:
        - Version en pyproject.toml
        - __version__ en __init__.py
        - API version en headers
    
    2. **Frontend (React)**:
        - Version en package.json
        - Build version en environment
        - Version display en UI
    
    3. **Docker**:
        - Image tags con version numbers
        - Latest tag para última stable

scripts/:
    - version_manager.py (Este script se encargará de gestionar las versiones del sistema Major, Minor, Patch, Alpha, Beta, RC) este script tiene que actualizar el badge de versión del archivo README.md, también considera la información que se va a requerir para la sección de "Version Management".

Frontend:
    - El frontend va a ser una aplicación SPA.
    - El frontend va a interactuar con el backend a través de una API REST.
    - El diseño tiene que ser responsive.

    ## 🎨 Paleta de Colores del Frontend

    Paleta de colores inspirada en GitHub con un enfoque moderno y profesional <mcreference link="https://www.color-hex.com/color-palette/41067" index="5">5</mcreference> <mcreference link="https://github.blog/news-insights/product-news/accelerating-github-theme-creation-with-color-tooling/" index="1">1</mcreference>:

    ### Colores Principales
    - **Primario**: #24292e (GitHub Dark Gray - Principal)
    - **Secundario**: #2b3137 (GitHub Medium Gray)
    - **Éxito**: #2dba4e (GitHub Green - Success)
    - **Advertencia**: #f66a0a (GitHub Orange)
    - **Error**: #d73a49 (GitHub Red)
    - **Info**: #0366d6 (GitHub Blue)

    ### Colores de Fondo
    - **Fondo Principal**: #ffffff (Blanco Puro)
    - **Fondo Secundario**: #fafbfc (GitHub Light Gray)
    - **Fondo Oscuro**: #24292e (GitHub Dark)
    - **Fondo Sidebar**: #f6f8fa (GitHub Sidebar)

    ### Colores de Texto
    - **Texto Principal**: #24292e (GitHub Dark)
    - **Texto Secundario**: #586069 (GitHub Medium)
    - **Texto Claro**: #ffffff (Blanco)
    - **Texto Muted**: #6a737d (GitHub Muted)

    ### Colores de Acento
    - **Hover**: #0366d6 (GitHub Blue Hover)
    - **Active**: #005cc5 (GitHub Blue Active)
    - **Border**: #e1e4e8 (GitHub Border)
    - **Focus**: #0366d6 (GitHub Focus Blue)

    ## 🎨 Identidad Visual y Temas

    ### Logo del Sistema
    - **Nombre del Sistema**: SEELE - E
    - **Archivo de Logo**: `/logo/logo_v2_simple_cropped.svg`
    - **Formato**: SVG vectorial escalable
    - **Ubicación**: Disponible en la carpeta `/logo/` del proyecto
    - **Características**: 
      - Diseño minimalista con triángulo y ojo estilizado
      - Colores de acento en rojo (#ff2a2a)
      - Optimizado para diferentes tamaños
      - Compatible con temas claro y oscuro

    ### Sistema de Temas
    - **Tema Claro (Predeterminado)**: Utiliza la paleta de colores definida anteriormente
    - **Tema Oscuro**: Versión oscura adaptada de la paleta GitHub con:
      - Fondo principal: #0d1117 (GitHub Dark)
      - Fondo secundario: #161b22 (GitHub Dark Secondary)
      - Texto principal: #f0f6fc (GitHub Dark Text)
      - Texto secundario: #7d8590 (GitHub Dark Muted)
      - Bordes: #30363d (GitHub Dark Border)
    
    - **Funcionalidades del Sistema de Temas**:
      - Toggle de tema en la interfaz de usuario
      - Persistencia de preferencia en localStorage
      - Transiciones suaves entre temas
      - Adaptación automática del logo según el tema
      - Soporte para preferencia del sistema (prefers-color-scheme)
      - Iconos y elementos UI adaptados a cada tema

Backend/:
    - Aquí generaremos nuestro backend
    - Recordar que para el backend utilizaremos FastAPI, asyncpg y SQLAlchemy, alembic para las migraciones de la base de datos y pydantic para la validación de datos.
    - Usaremos Clean Architecture

Base de datos/:
    - **Motor**: PostgreSQL con asyncpg para conexiones asíncronas
    - **ORM**: SQLAlchemy con soporte async/await
    - **Migraciones**: Alembic para control de versiones del esquema
    - **Timezone**: Todas las fechas en America/Mexico_City
    
    ### 🗄️ Esquemas de Tablas Principales
    
    #### Tabla de Usuarios:
    ```sql
    CREATE TABLE users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) UNIQUE NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        is_active BOOLEAN DEFAULT false,
        is_admin BOOLEAN DEFAULT false,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        last_login TIMESTAMPTZ,
        activation_token VARCHAR(255),
        activation_expires_at TIMESTAMPTZ
    );
    ```
    
    #### Tabla de Aplicaciones Registradas:
    ```sql
    CREATE TABLE applications (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        client_key VARCHAR(64) UNIQUE NOT NULL,
        client_secret VARCHAR(128) NOT NULL,
        is_active BOOLEAN DEFAULT true,
        daily_limit INTEGER DEFAULT 1000,
        monthly_limit INTEGER DEFAULT 30000,
        current_balance DECIMAL(10,2) DEFAULT 0.00,
        tier_type VARCHAR(50) DEFAULT 'basic', -- basic, premium, enterprise
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    ```
    
    #### Tabla Principal de Credenciales:
    ```sql
    CREATE TABLE credentials (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
        
        -- Metadatos de procesamiento
        credential_type INTEGER NOT NULL CHECK (credential_type IN (1, 2, 3)),
        processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
        
        -- Datos extraídos (campos obligatorios)
        clave_elector VARCHAR(18),
        curp VARCHAR(18),
        seccion VARCHAR(10),
        
        -- Datos adicionales del frente
        nombre VARCHAR(255),
        apellidos VARCHAR(255),
        fecha_nacimiento DATE,
        sexo CHAR(1),
        domicilio TEXT,
        
        -- Datos del reverso
        qr_data TEXT, -- Solo para tipos 1 y 2
        mrz_data TEXT, -- Opcional
        
        -- Información de procesamiento
        ai_provider VARCHAR(50), -- openai, deepseek, gemini, claude, local
        ai_model VARCHAR(100),
        processing_cost DECIMAL(8,4), -- Costo en MXN
        processing_time_ms INTEGER,
        
        -- Validaciones
        image_width INTEGER,
        image_height INTEGER,
        image_size_bytes INTEGER,
        validation_errors JSONB,
        
        -- Timestamps
        created_at TIMESTAMPTZ DEFAULT NOW(),
        processed_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    ```
    
    #### Tabla de Historial de Consumo:
    ```sql
    CREATE TABLE consumption_history (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
        credential_id UUID REFERENCES credentials(id) ON DELETE SET NULL,
        
        -- Detalles del consumo
        operation_type VARCHAR(50) NOT NULL, -- ocr_front, ocr_back, qr_extract, mrz_extract
        ai_provider VARCHAR(50) NOT NULL,
        ai_model VARCHAR(100) NOT NULL,
        
        -- Costos
        provider_cost_usd DECIMAL(8,6), -- Costo original del proveedor
        exchange_rate DECIMAL(8,4), -- Tipo de cambio USD->MXN
        cost_mxn DECIMAL(8,4) NOT NULL, -- Costo final en MXN
        markup_percentage DECIMAL(5,2), -- Margen aplicado
        
        -- Métricas
        processing_time_ms INTEGER,
        tokens_used INTEGER,
        success BOOLEAN DEFAULT true,
        error_message TEXT,
        
        created_at TIMESTAMPTZ DEFAULT NOW()
    ) PARTITION BY RANGE (created_at);
    ```
    
    #### Tabla de Solicitudes API:
    ```sql
    CREATE TABLE api_requests (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        application_id UUID REFERENCES applications(id) ON DELETE SET NULL,
        
        -- Detalles de la solicitud
        endpoint VARCHAR(255) NOT NULL,
        method VARCHAR(10) NOT NULL,
        status_code INTEGER NOT NULL,
        
        -- Métricas
        response_time_ms INTEGER,
        request_size_bytes INTEGER,
        response_size_bytes INTEGER,
        
        -- Información adicional
        user_agent TEXT,
        ip_address INET,
        error_details JSONB,
        
        timestamp TIMESTAMPTZ DEFAULT NOW()
    ) PARTITION BY RANGE (timestamp);
    ```
    
    #### Tabla de Proveedores de IA (Admin):
    ```sql
    CREATE TABLE ai_providers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(100) UNIQUE NOT NULL, -- openai, deepseek, gemini, claude
        display_name VARCHAR(100) NOT NULL,
        is_active BOOLEAN DEFAULT true,
        priority INTEGER DEFAULT 1, -- Para fallback automático
        
        -- Configuración
        api_endpoint VARCHAR(500),
        api_key_encrypted TEXT,
        rate_limit_per_minute INTEGER DEFAULT 60,
        
        -- Costos base
        cost_per_1k_tokens_usd DECIMAL(8,6),
        cost_per_image_usd DECIMAL(8,6),
        
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    ```
    
    #### Tabla de Modelos de IA:
    ```sql
    CREATE TABLE ai_models (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        provider_id UUID NOT NULL REFERENCES ai_providers(id) ON DELETE CASCADE,
        model_name VARCHAR(100) NOT NULL, -- gpt-4o, deepseek-chat, gemini-pro
        display_name VARCHAR(100) NOT NULL,
        is_active BOOLEAN DEFAULT true,
        
        -- Capacidades
        supports_vision BOOLEAN DEFAULT false,
        supports_ocr BOOLEAN DEFAULT false,
        max_tokens INTEGER,
        
        -- Costos específicos del modelo
        cost_multiplier DECIMAL(4,2) DEFAULT 1.00,
        
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        
        UNIQUE(provider_id, model_name)
    );
    ```
    
    #### Tabla de Configuración de Precios:
    ```sql
    CREATE TABLE pricing_config (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        provider_id UUID NOT NULL REFERENCES ai_providers(id) ON DELETE CASCADE,
        tier_type VARCHAR(50) NOT NULL, -- basic, premium, enterprise
        
        -- Multiplicadores por tier
        markup_percentage DECIMAL(5,2) NOT NULL, -- 15.00 = 15%
        volume_discount DECIMAL(5,2) DEFAULT 0.00,
        
        -- Límites por tier
        daily_limit INTEGER,
        monthly_limit INTEGER,
        
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        
        UNIQUE(provider_id, tier_type)
    );
    ```
    
    #### Tabla de Refresh Tokens (JWT):
    ```sql
    CREATE TABLE refresh_tokens (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token_hash VARCHAR(255) NOT NULL UNIQUE,
        
        -- Información del dispositivo/sesión
        device_info JSONB,
        ip_address INET,
        user_agent TEXT,
        
        -- Control de expiración
        expires_at TIMESTAMPTZ NOT NULL,
        is_revoked BOOLEAN DEFAULT false,
        revoked_at TIMESTAMPTZ,
        revoked_reason VARCHAR(100),
        
        -- Timestamps
        created_at TIMESTAMPTZ DEFAULT NOW(),
        last_used_at TIMESTAMPTZ DEFAULT NOW()
    );
    ```
    
    #### Tabla de API Keys (CLIENT_KEY y CLIENT_SECRET):
    ```sql
    CREATE TABLE api_keys (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
        
        -- Claves de API
        key_name VARCHAR(255) NOT NULL,
        client_key VARCHAR(64) UNIQUE NOT NULL,
        client_secret_hash VARCHAR(255) NOT NULL,
        
        -- Control de acceso
        is_active BOOLEAN DEFAULT true,
        permissions JSONB, -- Permisos específicos de la API key
        allowed_ips INET[], -- IPs permitidas (opcional)
        
        -- Uso y límites
        last_used_at TIMESTAMPTZ,
        usage_count INTEGER DEFAULT 0,
        rate_limit_per_minute INTEGER DEFAULT 60,
        
        -- Timestamps
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        expires_at TIMESTAMPTZ -- Opcional, para keys temporales
    );
    ```
    
    #### Tabla de Webhooks:
    ```sql
    CREATE TABLE webhooks (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
        
        -- Configuración del webhook
        name VARCHAR(255) NOT NULL,
        url VARCHAR(500) NOT NULL,
        secret_token VARCHAR(255), -- Para verificar autenticidad
        
        -- Eventos suscritos
        events TEXT[] NOT NULL, -- ['credential.processed', 'credential.failed', 'balance.low']
        
        -- Control
        is_active BOOLEAN DEFAULT true,
        retry_count INTEGER DEFAULT 3,
        timeout_seconds INTEGER DEFAULT 30,
        
        -- Estadísticas
        success_count INTEGER DEFAULT 0,
        failure_count INTEGER DEFAULT 0,
        last_success_at TIMESTAMPTZ,
        last_failure_at TIMESTAMPTZ,
        
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    ```
    
    #### Tabla de Entregas de Webhooks:
    ```sql
    CREATE TABLE webhook_deliveries (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        webhook_id UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
        credential_id UUID REFERENCES credentials(id) ON DELETE SET NULL,
        
        -- Detalles de la entrega
        event_type VARCHAR(100) NOT NULL,
        payload JSONB NOT NULL,
        
        -- Resultado
        status VARCHAR(50) DEFAULT 'pending', -- pending, success, failed, retrying
        http_status_code INTEGER,
        response_body TEXT,
        error_message TEXT,
        
        -- Reintentos
        attempt_count INTEGER DEFAULT 0,
        next_retry_at TIMESTAMPTZ,
        
        created_at TIMESTAMPTZ DEFAULT NOW(),
        delivered_at TIMESTAMPTZ
    ) PARTITION BY RANGE (created_at);
    ```
    
    #### Tabla de Auditoría de Acceso:
    ```sql
    CREATE TABLE access_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        
        -- Identificación
        user_id UUID REFERENCES users(id) ON DELETE SET NULL,
        application_id UUID REFERENCES applications(id) ON DELETE SET NULL,
        api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
        
        -- Detalles del acceso
        action VARCHAR(100) NOT NULL, -- login, api_call, credential_process, etc.
        resource VARCHAR(255), -- endpoint o recurso accedido
        method VARCHAR(10),
        
        -- Resultado
        success BOOLEAN NOT NULL,
        status_code INTEGER,
        error_message TEXT,
        
        -- Información de contexto
        ip_address INET,
        user_agent TEXT,
        request_id UUID,
        session_id VARCHAR(255),
        
        -- Datos adicionales
        metadata JSONB, -- Información adicional contextual
        
        created_at TIMESTAMPTZ DEFAULT NOW()
    ) PARTITION BY RANGE (created_at);
    ```
    
    #### Tabla de Métricas de Calidad:
    ```sql
    CREATE TABLE quality_metrics (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        credential_id UUID NOT NULL REFERENCES credentials(id) ON DELETE CASCADE,
        
        -- Métricas de OCR
        ocr_confidence_front DECIMAL(5,2), -- 0.00 - 100.00
        ocr_confidence_back DECIMAL(5,2),
        text_clarity_score DECIMAL(5,2),
        
        -- Métricas de QR
        qr_decode_success BOOLEAN,
        qr_error_correction_level VARCHAR(10),
        qr_data_integrity_score DECIMAL(5,2),
        
        -- Métricas de imagen
        image_quality_score DECIMAL(5,2),
        brightness_level DECIMAL(5,2),
        contrast_level DECIMAL(5,2),
        sharpness_score DECIMAL(5,2),
        
        -- Validación cruzada
        cross_validation_score DECIMAL(5,2), -- Consistencia entre OCR y QR
        data_completeness_percentage DECIMAL(5,2),
        
        -- Detección de anomalías
        anomaly_score DECIMAL(5,2), -- 0.00 = normal, 100.00 = muy anómalo
        fraud_risk_level VARCHAR(20), -- low, medium, high, critical
        
        -- Métricas de procesamiento
        total_processing_time_ms INTEGER,
        ai_model_used VARCHAR(100),
        fallback_used BOOLEAN DEFAULT false,
        
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    ```
    
    #### Tabla de Configuración del Sistema:
    ```sql
    CREATE TABLE system_config (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        
        -- Identificación
        config_key VARCHAR(255) UNIQUE NOT NULL,
        config_value JSONB NOT NULL,
        
        -- Metadatos
        description TEXT,
        config_type VARCHAR(50) NOT NULL, -- string, number, boolean, json, array
        is_sensitive BOOLEAN DEFAULT false, -- Para valores que requieren cifrado
        
        -- Control de cambios
        version INTEGER DEFAULT 1,
        changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
        
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    ```
    
    #### Tabla de Notificaciones:
    ```sql
    CREATE TABLE notifications (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        application_id UUID REFERENCES applications(id) ON DELETE SET NULL,
        
        -- Contenido
        title VARCHAR(255) NOT NULL,
        message TEXT NOT NULL,
        notification_type VARCHAR(50) NOT NULL, -- info, warning, error, success
        
        -- Categoría
        category VARCHAR(100), -- balance_low, processing_complete, system_maintenance
        
        -- Estado
        is_read BOOLEAN DEFAULT false,
        read_at TIMESTAMPTZ,
        
        -- Datos adicionales
        metadata JSONB,
        action_url VARCHAR(500), -- URL para acción relacionada
        
        created_at TIMESTAMPTZ DEFAULT NOW(),
        expires_at TIMESTAMPTZ -- Opcional, para notificaciones temporales
    );
    ```
    
    ### 📊 Estrategia de Indexado y Optimización
    
    #### Índices Principales para Consultas Frecuentes:
    ```sql
    -- Índices para búsquedas por fechas (más críticos)
    CREATE INDEX idx_credentials_created_at_desc ON credentials (created_at DESC);
    CREATE INDEX idx_credentials_processed_at_desc ON credentials (processed_at DESC);
    CREATE INDEX idx_consumption_history_date_desc ON consumption_history (created_at DESC);
    CREATE INDEX idx_api_requests_timestamp_desc ON api_requests (timestamp DESC);
    CREATE INDEX idx_access_logs_created_at_desc ON access_logs (created_at DESC);
    CREATE INDEX idx_webhook_deliveries_created_at_desc ON webhook_deliveries (created_at DESC);
    CREATE INDEX idx_notifications_created_at_desc ON notifications (created_at DESC);
    
    -- Índices compuestos para filtros combinados
    CREATE INDEX idx_credentials_user_date ON credentials (user_id, created_at DESC);
    CREATE INDEX idx_credentials_app_date ON credentials (application_id, created_at DESC);
    CREATE INDEX idx_credentials_status_date ON credentials (processing_status, created_at DESC);
    CREATE INDEX idx_credentials_type_date ON credentials (credential_type, created_at DESC);
    
    -- Índices para búsquedas por datos específicos
    CREATE INDEX idx_credentials_clave_elector ON credentials (clave_elector);
    CREATE INDEX idx_credentials_curp ON credentials (curp);
    CREATE INDEX idx_credentials_seccion ON credentials (seccion);
    
    -- Índices específicos para búsquedas optimizadas
    CREATE INDEX CONCURRENTLY idx_credentials_clave_elector_btree ON credentials USING btree(clave_elector) WHERE clave_elector IS NOT NULL;
    CREATE INDEX CONCURRENTLY idx_credentials_curp_btree ON credentials USING btree(curp) WHERE curp IS NOT NULL;
    CREATE INDEX CONCURRENTLY idx_credentials_fulltext ON credentials USING gin(to_tsvector('spanish', nombre || ' ' || COALESCE(apellidos, '')));
    CREATE INDEX CONCURRENTLY idx_credentials_processing_status ON credentials(processing_status) WHERE processing_status != 'completed';
    CREATE INDEX CONCURRENTLY idx_applications_active ON applications(is_active) WHERE is_active = true;
    CREATE INDEX CONCURRENTLY idx_refresh_tokens_active ON refresh_tokens(user_id, expires_at) WHERE is_revoked = false AND expires_at > NOW();
    CREATE INDEX CONCURRENTLY idx_api_keys_active_app ON api_keys(application_id) WHERE is_active = true;
    CREATE INDEX CONCURRENTLY idx_webhooks_events ON webhooks USING gin(events) WHERE is_active = true;
    CREATE INDEX CONCURRENTLY idx_access_logs_action_success ON access_logs(action, success, created_at DESC);
    CREATE INDEX CONCURRENTLY idx_notifications_unread ON notifications(user_id, created_at DESC) WHERE is_read = false;
    
    -- Índices para reportes y analytics
    CREATE INDEX idx_consumption_provider_date ON consumption_history (ai_provider, created_at DESC);
    CREATE INDEX idx_consumption_model_date ON consumption_history (ai_model, created_at DESC);
    CREATE INDEX idx_api_requests_endpoint_date ON api_requests (endpoint, timestamp DESC);
    CREATE INDEX idx_api_requests_status_date ON api_requests (status_code, timestamp DESC);
    
    -- Índices para nuevas tablas
    CREATE INDEX idx_refresh_tokens_user_expires ON refresh_tokens (user_id, expires_at DESC);
    CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens (token_hash);
    CREATE INDEX idx_api_keys_app_active ON api_keys (application_id, is_active);
    CREATE INDEX idx_api_keys_client_key ON api_keys (client_key);
    CREATE INDEX idx_webhooks_app_active ON webhooks (application_id, is_active);
    CREATE INDEX idx_webhook_deliveries_webhook_status ON webhook_deliveries (webhook_id, status);
    CREATE INDEX idx_access_logs_user_action ON access_logs (user_id, action, created_at DESC);
    CREATE INDEX idx_access_logs_app_action ON access_logs (application_id, action, created_at DESC);
    CREATE INDEX idx_quality_metrics_credential ON quality_metrics (credential_id);
    CREATE INDEX idx_system_config_key ON system_config (config_key);
    CREATE INDEX idx_notifications_user_read ON notifications (user_id, is_read, created_at DESC);
    CREATE INDEX idx_notifications_app_category ON notifications (application_id, category, created_at DESC);
    ```
    
    #### Índices para Búsquedas de Texto:
    ```sql
    -- Búsquedas de texto completo en nombres
    CREATE INDEX idx_credentials_nombre_gin ON credentials USING gin(to_tsvector('spanish', nombre));
    CREATE INDEX idx_users_name_gin ON users USING gin(to_tsvector('spanish', full_name));
    
    -- Índices para búsquedas parciales
    CREATE INDEX idx_credentials_nombre_trigram ON credentials USING gin(nombre gin_trgm_ops);
    CREATE INDEX idx_credentials_apellidos_trigram ON credentials USING gin(apellidos gin_trgm_ops);
    
    -- Índices adicionales para texto completo
    CREATE INDEX idx_applications_name_gin ON applications USING gin(to_tsvector('spanish', name));
    CREATE INDEX idx_notifications_title_gin ON notifications USING gin(to_tsvector('spanish', title));
    CREATE INDEX idx_notifications_message_gin ON notifications USING gin(to_tsvector('spanish', message));
    ```
    
    #### Particionamiento por Fechas:
    ```sql
    -- Particionamiento mensual para tablas de alto volumen
    CREATE TABLE credentials_partitioned (
        LIKE credentials INCLUDING ALL
    ) PARTITION BY RANGE (created_at);
    
    -- Particiones automáticas por mes
    CREATE TABLE credentials_2024_01 PARTITION OF credentials_partitioned
        FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
    ```
    
    #### Configuración PostgreSQL Optimizada:
    ```sql
    -- postgresql.conf optimizations
    shared_buffers = 256MB
    effective_cache_size = 1GB
    maintenance_work_mem = 64MB
    checkpoint_completion_target = 0.9
    wal_buffers = 16MB
    default_statistics_target = 100
    random_page_cost = 1.1
    effective_io_concurrency = 200
    work_mem = 4MB
    min_wal_size = 1GB
    max_wal_size = 4GB
    
    -- Configuración específica para timezone
    timezone = 'America/Mexico_City'
    log_timezone = 'America/Mexico_City'
    ```
    
    #### Optimizaciones de Consulta:
    - **Paginación eficiente**: Usar cursor-based pagination con `created_at` para evitar OFFSET costosos
    - **Consultas preparadas**: Todas las consultas frecuentes como prepared statements
    - **Connection pooling**: Pool de conexiones optimizado para carga concurrente
    - **Query hints**: Usar EXPLAIN ANALYZE para optimizar consultas complejas
    - **Vacuum automático**: Configuración optimizada para mantenimiento automático
    
    #### Métricas y Monitoreo:
    ```sql
    -- Vista para monitoreo de rendimiento
    CREATE VIEW query_performance AS
    SELECT 
        query,
        calls,
        total_time,
        mean_time,
        rows
    FROM pg_stat_statements
    ORDER BY total_time DESC;
    
    -- Extensiones requeridas para monitoreo
    CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
    CREATE EXTENSION IF NOT EXISTS pg_buffercache;
    ```
    
    #### Backup y Recuperación:
    ```bash
    # Script de backup automático
    pg_dump -h localhost -U postgres -d seele_ine > backup_$(date +%Y%m%d_%H%M%S).sql
    
    # Configuración de WAL archiving
    archive_mode = on
    archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'
    ```
    
    ### 🔍 Estrategias de Búsqueda Optimizadas:
    
    - **Búsquedas por rango de fechas**: Índices descendentes para consultas recientes
    - **Filtros combinados**: Índices compuestos para user_id + fecha, app_id + fecha
    - **Búsquedas de texto**: Full-text search con soporte para español y búsquedas parciales
    - **Reportes agregados**: Índices específicos para consultas de analytics y reportes
    - **Cache de consultas**: Redis para cachear resultados de consultas frecuentes
    - **Consultas asíncronas**: Aprovechamiento completo de asyncpg para operaciones no bloqueantes
    
    ## 🔗 Endpoints de la API REST
    
    ### 🔐 Autenticación y Autorización
    ```
    POST /api/v1/auth/register          # Registro de usuarios
    POST /api/v1/auth/login             # Login con JWT
    POST /api/v1/auth/refresh           # Refresh token
    POST /api/v1/auth/logout            # Logout
    POST /api/v1/auth/activate          # Activación de cuenta
    POST /api/v1/auth/forgot-password   # Recuperación de contraseña
    POST /api/v1/auth/reset-password    # Reset de contraseña
    ```
    
    ### 🔑 Gestión de API Keys
    ```
    POST /api/v1/users/api-keys         # Generar CLIENT_KEY y CLIENT_SECRET
    GET /api/v1/users/api-keys          # Listar API keys del usuario
    DELETE /api/v1/users/api-keys/{id}  # Eliminar API key
    PUT /api/v1/users/api-keys/{id}     # Regenerar API key
    ```
    
    ### 👤 Gestión de Usuarios
    ```
    GET /api/v1/users/profile           # Obtener perfil del usuario
    PUT /api/v1/users/profile           # Actualizar perfil
    GET /api/v1/users                   # Listar usuarios (admin, con paginación)
    DELETE /api/v1/users/{id}           # Eliminar usuario (admin)
    ```
    
    ### 📄 Procesamiento de Credenciales INE
    ```
    POST /api/v1/credentials/upload     # Subir imágenes de credencial (frente y reverso)
    POST /api/v1/credentials/validate   # Validar dimensiones (790x490px)
    POST /api/v1/credentials/classify   # Clasificar tipo de credencial (1, 2, 3)
    POST /api/v1/credentials/extract    # Extraer datos completos de la credencial
    POST /api/v1/credentials/process    # Proceso completo (validar + clasificar + extraer)
    ```
    
    ### 🔍 Extracción de Datos Específicos
    ```
    POST /api/v1/ocr/front              # Extraer datos del frente
    POST /api/v1/ocr/back               # Extraer datos del reverso
    POST /api/v1/qr/extract             # Extraer código QR (tipos 1 y 2)
    POST /api/v1/mrz/extract            # Extraer MRZ (opcional)
    ```
    
    ### 📊 Historial y Reportes
    ```
    GET /api/v1/credentials/history     # Historial de procesamiento (con paginación lazy)
    GET /api/v1/credentials/{id}        # Obtener resultado específico
    GET /api/v1/reports/stats           # Estadísticas de procesamiento
    GET /api/v1/reports/errors          # Reporte de errores
    ```
    
    ### 💰 Gestión de Costos y Consumo (Por Aplicación)
    ```
    GET /api/v1/app/consumption-history  # Historial simplificado de consumo de la aplicación
    GET /api/v1/app/cost-summary         # Resumen de costos de la aplicación
    GET /api/v1/app/limits               # Límites de consumo de la aplicación
    GET /api/v1/app/balance              # Saldo disponible de la aplicación
    POST /api/v1/app/top-up              # Recarga de saldo de la aplicación
    ```
    
    ### 🤖 Gestión de Proveedores de IA (Admin)
    ```
    GET /api/v1/admin/ai-providers      # Listar proveedores de IA disponibles
    POST /api/v1/admin/ai-providers     # Agregar nuevo proveedor de IA
    PUT /api/v1/admin/ai-providers/{id} # Actualizar configuración de proveedor
    DELETE /api/v1/admin/ai-providers/{id} # Eliminar proveedor
    GET /api/v1/admin/ai-models         # Listar modelos por proveedor
    POST /api/v1/admin/ai-models        # Agregar nuevo modelo
    PUT /api/v1/admin/ai-models/{id}    # Actualizar configuración de modelo
    DELETE /api/v1/admin/ai-models/{id} # Eliminar modelo
    GET /api/v1/admin/ai-priorities     # Obtener prioridades de proveedores
    PUT /api/v1/admin/ai-priorities     # Configurar fallback automático
    ```
    
    ### ⚙️ Configuración de Precios Multi-Proveedor (Admin)
    ```
    GET /api/v1/admin/pricing           # Obtener configuración de precios por proveedor
    PUT /api/v1/admin/pricing/{provider} # Actualizar precios de proveedor específico
    GET /api/v1/admin/exchange-rates    # Obtener tipos de cambio múltiples
    PUT /api/v1/admin/exchange-rates    # Actualizar tipos de cambio
    GET /api/v1/admin/multipliers       # Obtener multiplicadores por proveedor
    PUT /api/v1/admin/multipliers       # Actualizar multiplicadores
    GET /api/v1/admin/user-tiers        # Obtener tipos de usuario y tarifas
    PUT /api/v1/admin/user-tiers        # Actualizar tarifas por tipo de usuario
    ```
    
    ### 📈 Reportes de Costos (Admin)
    ```
    GET /api/v1/admin/reports/revenue   # Reporte de ingresos
    GET /api/v1/admin/reports/costs     # Reporte de costos totales
    GET /api/v1/admin/reports/apps      # Reporte de consumo por aplicación registrada
    GET /api/v1/admin/reports/users     # Reporte de consumo por usuario
    GET /api/v1/admin/reports/user-app  # Reporte cruzado usuario-aplicación
    GET /api/v1/admin/reports/providers # Análisis de costos por proveedor de IA
    GET /api/v1/admin/reports/operations # Análisis de rentabilidad por operación
    GET /api/v1/admin/reports/detailed/{app_id} # Historial detallado de una aplicación específica
    GET /api/v1/admin/reports/detailed/user/{user_id} # Historial detallado de un usuario específico
    POST /api/v1/admin/reports/export   # Exportar reportes (CSV/PDF)
    ```
    
    ### ⚙️ Configuración y Sistema
    ```
    GET /api/v1/system/health           # Health check
    GET /api/v1/system/version          # Versión de la API
    GET /api/v1/system/config           # Configuración del sistema
    ```
    
    ### 📋 Características de los Endpoints:
    
    - **Autenticación JWT** con refresh tokens para sesiones seguras
    - **Generación de API Keys** (CLIENT_KEY y CLIENT_SECRET) para integración programática
    - **Validación estricta** de dimensiones de imagen (790x490px)
    - **Clasificación automática** entre los 3 tipos de credenciales INE
    - **Extracción multi-proveedor**: OCR local → APIs de IA múltiples como fallback
    - **Soporte multi-modelo**: OpenAI, DeepSeek, Gemini, Claude y otros proveedores
    - **Procesamiento QR obligatorio** para credenciales tipo 1 y 2
    - **Paginación lazy loading** para todos los listados de datos
    - **Timezone America/Mexico_City** en todas las respuestas
    - **Validación con Pydantic** y manejo robusto de errores
    - **Control de costos multi-proveedor**: Registro detallado por proveedor y modelo (admin)
    - **Sistema de facturación multi-moneda**: Conversión automática a MXN
    - **Límites por aplicación**: Control de consumo diario/mensual con alertas automáticas
    - **Reportes financieros**: Análisis de rentabilidad por proveedor y aplicación
    - **Gestión de saldo**: Sistema de recarga y balance para aplicaciones registradas
    - **Tarifas diferenciadas**: Precios por tipo de aplicación y proveedor de IA
    - **Vista simplificada**: Usuarios solo ven costo final por petición sin detalles técnicos
    - **Facturación por aplicación**: Costos asociados a aplicaciones registradas, no usuarios individuales
    - **Fallback automático**: Sistema de prioridades entre proveedores de IA
    - **Separación de roles**: Área de administración vs área de usuario claramente definidas
    - **Gestión centralizada**: Solo administradores pueden configurar proveedores y modelos
    
    ### 🎯 Campos Obligatorios por Tipo de Credencial:
    - **Tipo 1**: Clave de elector, CURP, Sección, QR (reverso)
    - **Tipo 2**: Clave de elector, CURP, Sección, QR (reverso)
    - **Tipo 3**: Clave de elector, CURP, Sección
    
    Todos los endpoints incluyen validación completa y retornan error si no se pueden extraer los campos obligatorios.