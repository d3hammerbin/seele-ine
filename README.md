# SEELE-E

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-red.svg)
![React](https://img.shields.io/badge/React-19.1+-blue.svg)
![Node.js](https://img.shields.io/badge/Node.js-22_LTS-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17.0+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-development-yellow.svg)

**Sistema de Extracción de Información de Credenciales INE**

SEELE-E es un sistema avanzado para la extracción automática de información de credenciales de identificación del Instituto Nacional Electoral (INE) de México, utilizando tecnologías de OCR, procesamiento de códigos QR y APIs de inteligencia artificial.

## 🚀 Características Principales

### 📋 Procesamiento de Credenciales
- **Soporte para 3 tipos de credenciales INE** con validación automática de dimensiones (790x490px)
- **Extracción de datos obligatorios**: Clave de elector, CURP, Sección
- **Procesamiento de códigos QR** para credenciales tipo 1 y 2
- **Validación de imágenes** con control de calidad y formato
- **Clasificación automática** del tipo de credencial

### 🤖 Inteligencia Artificial Multi-Proveedor
- **OpenAI GPT-4 Vision** para análisis avanzado de imágenes
- **DeepSeek** como alternativa económica
- **Google Gemini** para procesamiento visual
- **Anthropic Claude** para análisis de documentos
- **Sistema de fallback automático** entre proveedores
- **Control de costos y consumo** por aplicación

### 🔧 Tecnologías de Extracción
- **Tesseract OCR** para reconocimiento de texto local
- **OpenCV** para procesamiento de imágenes
- **pyzbar** para decodificación de códigos QR
- **Priorización de extracción local** antes de usar APIs de IA

### 💰 Sistema de Facturación y Costos
- **Seguimiento detallado** de consumo de tokens/créditos
- **Configuración multi-proveedor** de precios
- **Soporte multi-moneda** con tipos de cambio
- **Límites por aplicación** con alertas automáticas
- **Reportes financieros** para administradores
- **Vista simplificada** de costos para usuarios

### 🔐 Seguridad y Autenticación
- **Autenticación JWT** con refresh tokens
- **Gestión de API keys** por aplicación
- **Control de acceso basado en roles**
- **Rate limiting** configurable
- **Logs de auditoría** completos

### 📊 Monitoreo y Reportes
- **Dashboard administrativo** completo
- **Métricas de rendimiento** en tiempo real
- **Historial de procesamiento** con paginación
- **Reportes de consumo** por período
- **Alertas de balance bajo**

## 🏗️ Arquitectura

### Backend (FastAPI)
- **Clean Architecture** con separación de capas
- **API REST** con documentación automática
- **Base de datos PostgreSQL** con particionado
- **Cache Redis** para optimización
- **Procesamiento asíncrono** con workers
- **Migraciones Alembic** para versionado de BD

### Frontend (React)
- **Single Page Application (SPA)**
- **Redux** para gestión de estado
- **Tailwind CSS** para estilos
- **Sistema de temas** claro/oscuro
- **Diseño responsive** para todos los dispositivos
- **Interfaz inspirada en GitHub**

### Infraestructura
- **Docker** con multi-stage builds
- **Docker Compose** para orquestación
- **Nginx** como reverse proxy
- **Prometheus + Grafana** para monitoreo
- **Backup automático** de base de datos

## 📁 Estructura del Proyecto

```
seele_ine/
├── backend/                    # Backend FastAPI
│   ├── app/
│   │   ├── domain/            # Entidades y reglas de negocio
│   │   ├── use_cases/         # Casos de uso
│   │   ├── infrastructure/    # Implementaciones concretas
│   │   ├── api/              # Endpoints REST
│   │   └── core/             # Configuración y utilidades
│   ├── tests/                # Tests unitarios e integración
│   ├── alembic/              # Migraciones de BD
│   ├── Dockerfile            # Imagen Docker del backend
│   └── requirements.txt      # Dependencias Python
├── frontend/                  # Frontend React
│   ├── src/
│   │   ├── components/       # Componentes reutilizables
│   │   ├── pages/           # Páginas de la aplicación
│   │   ├── store/           # Estado Redux
│   │   ├── services/        # Servicios API
│   │   └── utils/           # Utilidades
│   ├── public/              # Archivos estáticos
│   ├── Dockerfile           # Imagen Docker del frontend
│   └── package.json         # Dependencias Node.js
├── psgs/                     # Scripts PostgreSQL
├── credentials/              # Ejemplos de credenciales
│   ├── tipo1/
│   ├── tipo2/
│   └── tipo3/
├── scripts/                  # Scripts de utilidad
├── config/                   # Configuraciones
│   ├── nginx.conf
│   ├── redis.conf
│   └── prometheus.yml
├── logs/                     # Archivos de log
├── uploads/                  # Archivos subidos
├── temp/                     # Archivos temporales
├── backups/                  # Respaldos de BD
├── ssl/                      # Certificados SSL
├── logo/                     # Recursos de marca
├── reference/                # Documentación de referencia
├── .env                      # Variables de entorno
├── docker-compose.yml        # Configuración Docker
├── README.md                 # Este archivo
└── CHANGELOG.md              # Historial de cambios
```

## 🚀 Instalación y Configuración

### Prerrequisitos

- **Docker** 24.0+ y **Docker Compose** 2.20+
- **Node.js** 22 LTS (para desarrollo frontend)
- **Python** 3.11+ (para desarrollo backend)
- **Git** para control de versiones

### Instalación Rápida con Docker

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/seele_ine.git
   cd seele_ine
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

3. **Iniciar servicios**
   ```bash
   docker-compose up -d
   ```

4. **Ejecutar migraciones**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Acceder a la aplicación**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Documentación API: http://localhost:8000/docs
   - Grafana: http://localhost:3001 (admin/admin123)

### Desarrollo Local

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## 📚 Uso de la API

### Autenticación

```bash
# Obtener token de acceso
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

### Procesamiento de Credenciales

```bash
# Procesar credencial INE
curl -X POST "http://localhost:8000/credentials/process" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@credencial.jpg" \
  -F "extract_qr=true"
```

### Gestión de API Keys

```bash
# Crear API key para aplicación
curl -X POST "http://localhost:8000/api-keys" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Mi Aplicación", "description": "API key para mi app"}'
```

## 🔧 Configuración

### Variables de Entorno Principales

```env
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/seele_ine_db

# Seguridad
JWT_SECRET_KEY=your-super-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Proveedores de IA
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=your-deepseek-key
GEMINI_API_KEY=your-gemini-key
CLAUDE_API_KEY=your-claude-key

# Procesamiento
MAX_IMAGE_SIZE_MB=10
CREDENTIAL_WIDTH=790
CREDENTIAL_HEIGHT=490
```

### Configuración de Proveedores de IA

Los proveedores se configuran a través del panel administrativo o directamente en la base de datos:

```sql
INSERT INTO ai_providers (name, base_url, is_active, priority) VALUES
('openai', 'https://api.openai.com/v1', true, 1),
('deepseek', 'https://api.deepseek.com/v1', true, 2),
('gemini', 'https://generativelanguage.googleapis.com/v1', true, 3),
('claude', 'https://api.anthropic.com/v1', true, 4);
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### Tests de Integración
```bash
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

## 📊 Monitoreo

### Métricas Disponibles
- **Requests por segundo** por endpoint
- **Tiempo de respuesta** promedio
- **Tasa de error** por proveedor de IA
- **Consumo de tokens** por aplicación
- **Uso de recursos** (CPU, memoria, disco)
- **Salud de servicios** (base de datos, Redis, etc.)

### Dashboards Grafana
- **Overview del Sistema**
- **Performance de APIs**
- **Consumo de IA**
- **Métricas de Negocio**
- **Infraestructura**

## 🔒 Seguridad

### Mejores Prácticas Implementadas
- **Validación de entrada** en todos los endpoints
- **Sanitización de archivos** subidos
- **Rate limiting** por IP y usuario
- **Logs de auditoría** completos
- **Encriptación** de datos sensibles
- **Tokens JWT** con expiración
- **HTTPS** obligatorio en producción

### Configuración de Seguridad
```env
# Rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Archivos
MAX_IMAGE_SIZE_MB=10
ALLOWED_IMAGE_FORMATS=jpg,jpeg,png,webp

# JWT
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

## 🚀 Despliegue en Producción

### Usando Docker Compose

1. **Configurar variables de producción**
   ```bash
   cp .env.example .env.production
   # Configurar valores de producción
   ```

2. **Generar certificados SSL**
   ```bash
   ./scripts/generate-ssl.sh
   ```

3. **Desplegar**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

### Usando Kubernetes

```bash
kubectl apply -f k8s/
```

## 📈 Roadmap

### v1.1.0 (Q2 2025)
- [ ] Soporte para más tipos de documentos
- [ ] API de webhooks para notificaciones
- [ ] Integración con servicios de almacenamiento en la nube
- [ ] Mejoras en la precisión de OCR

### v1.2.0 (Q3 2025)
- [ ] Interfaz móvil nativa
- [ ] Procesamiento por lotes
- [ ] Análisis de calidad de imagen automático
- [ ] Integración con sistemas de gestión documental

### v2.0.0 (Q4 2025)
- [ ] Machine Learning personalizado
- [ ] Soporte multi-idioma
- [ ] API GraphQL
- [ ] Microservicios distribuidos

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Guías de Contribución
- Sigue las convenciones de código existentes
- Añade tests para nuevas funcionalidades
- Actualiza la documentación según sea necesario
- Usa commits semánticos (feat, fix, docs, etc.)

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👥 Equipo

- **Desarrollador Principal**: [Tu Nombre](https://github.com/tu-usuario)
- **Arquitecto de Software**: [Nombre](https://github.com/usuario)
- **DevOps Engineer**: [Nombre](https://github.com/usuario)

## 📞 Soporte

- **Documentación**: [Wiki del Proyecto](https://github.com/tu-usuario/seele_ine/wiki)
- **Issues**: [GitHub Issues](https://github.com/tu-usuario/seele_ine/issues)
- **Discusiones**: [GitHub Discussions](https://github.com/tu-usuario/seele_ine/discussions)
- **Email**: soporte@seele-ine.com

## 🙏 Agradecimientos

- Instituto Nacional Electoral (INE) por la especificación de credenciales
- Comunidad de FastAPI por el excelente framework
- Equipo de React por la biblioteca de UI
- Contribuidores de Tesseract OCR
- Todos los contribuidores del proyecto

---

**SEELE-E** - Sistema de Extracción de Información de Credenciales INE

*Desarrollado con ❤️ para la comunidad mexicana*