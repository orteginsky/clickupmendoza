# Nexus Legal Integration v2.3.0

Middleware de integración entre ClickUp, Cloud SQL (PostgreSQL) y servicios externos (Filtros IA) con API para búsqueda fuzzy, sincronización de datos y procesamiento inteligente de leads. Soporta múltiples listas de ClickUp de forma independiente.

## Arquitectura

```
ClickUp API/Webhooks
    │
    ├── /webhooks/clickup       (CONSULTAS AGENDA)
    │       └── LeadService → leads_cache → Enqueuer → Filtros IA
    │                                   └── Google Sheets
    │
    └── /webhooks/assignments   (CASE ASSIGNMENT)
            └── AssignmentService → case_assignments

Filtros IA → /callbacks/filtros → ClickUp Update (AI Link field)

API Consumers (MCP / Google Sheets / externos)
    └── GET /leads/search, /leads/{id}, /leads/mycase/{id}
```

**Componentes principales:**

- **FastAPI**: API REST con endpoints de webhook, búsqueda y callbacks
- **Cloud SQL**: PostgreSQL con extensión `pg_trgm` para búsqueda fuzzy
- **Cloud Run**: Hosting serverless (scale-to-zero)
- **Secret Manager**: Gestión de credenciales
- **Enqueuer + Filtros IA**: Procesamiento inteligente de leads vía Cloud Tasks
- **Google Sheets**: Sincronización de logs y reportes

## Stack Tecnológico

- **Python 3.11+**
- **FastAPI** (framework web)
- **SQLAlchemy** (ORM)
- **httpx** (cliente HTTP async)
- **PostgreSQL 15** con `pg_trgm`
- **Google Cloud Run** (hosting)
- **Alembic** (migraciones de DB)
- **gspread + google-auth** (integración Google Sheets)

## Estructura del Proyecto

```
clickupmendoza/
├── app/
│   ├── __init__.py
│   ├── main.py                      # Aplicación FastAPI principal (v2.3.0)
│   ├── config.py                    # Configuración (Pydantic Settings)
│   ├── database.py                  # Conexión a DB
│   ├── models/                      # Modelos SQLAlchemy
│   │   ├── lead.py                  # Tabla leads_cache (CONSULTAS AGENDA)
│   │   └── case_assignment.py       # Tabla case_assignments (CASE ASSIGNMENT)
│   ├── schemas/                     # Schemas Pydantic (request/response)
│   │   ├── lead.py                  # LeadResponse, LeadSearchResponse
│   │   ├── webhook.py               # Payload genérico de webhook
│   │   ├── case_assignment.py       # CaseAssignmentWebhook, CaseAssignmentResponse
│   │   └── filtros.py               # FiltrosCallbackPayload (respuesta de Filtros IA)
│   ├── core/                        # Lógica de parsing y normalización
│   │   ├── parser.py                # Extrae campos de task_content (regex)
│   │   ├── normalizer.py            # Normaliza nombres para búsqueda
│   │   └── text_utils.py            # Utilidades de texto (teléfonos, fechas)
│   ├── repositories/                # Patrón Repository (acceso a datos)
│   │   ├── lead_repository.py       # CRUD + búsqueda fuzzy para leads
│   │   └── assignment_repository.py # Upsert para case_assignments
│   ├── services/                    # Lógica de negocio
│   │   ├── clickup_service.py       # ClickUp API (GET task, POST field, verify)
│   │   ├── lead_service.py          # Transforma task → LeadsCache
│   │   ├── assignment_service.py    # Transforma task → CaseAssignment (21 campos)
│   │   └── sheets_service.py        # Integración Google Sheets
│   └── api/                         # Endpoints FastAPI
│       ├── webhooks.py              # POST /webhooks/clickup (CONSULTAS AGENDA)
│       ├── webhook_assignments.py   # POST /webhooks/assignments (CASE ASSIGNMENT)
│       ├── callbacks.py             # POST /callbacks/filtros (Filtros IA)
│       └── leads.py                 # GET /leads/search, /leads/{id}, etc.
├── alembic/                         # Migraciones de base de datos
│   ├── env.py
│   └── versions/
├── scripts/
│   ├── init_db.py                   # Inicializa leads_cache + pg_trgm
│   ├── init_db_ca.py                # Inicializa case_assignments
│   ├── import_history.py            # Carga datos históricos de leads
│   ├── import_case_assignments.py   # Carga datos históricos de assignments
│   ├── register_webhook.py          # Registra webhook CONSULTAS AGENDA en ClickUp
│   └── register_webhook_assignments.py # Registra webhook CASE ASSIGNMENT en ClickUp
├── tests/
│   ├── test_webhook.py
│   └── test_assignment_webhook.py
├── requirements.txt
├── Dockerfile
├── cloudbuild.yaml
├── deploy.sh
└── .env.example
```

## Instalación Local

### 1. Requisitos previos

- Python 3.11+
- PostgreSQL 15+ (con extensión `pg_trgm`)
- Google Cloud SDK (para deployment)

### 2. Clonar repositorio

```bash
git clone <repo-url>
cd clickupmendoza
```

### 3. Configurar entorno

```bash
# Crear entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar template
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

**Variables críticas:**
- `CLICKUP_API_TOKEN`: Token de API de ClickUp
- `CLICKUP_WEBHOOK_SECRET`: Secret para validar webhooks de CONSULTAS AGENDA
- `CLICKUP_WEBHOOK_SECRET_ASSIGNMENTS`: Secret para validar webhooks de CASE ASSIGNMENT
- `DATABASE_URL`: Connection string de PostgreSQL

### 5. Inicializar base de datos

```bash
# Inicializar tabla leads (CONSULTAS AGENDA)
python scripts/init_db.py

# Inicializar tabla case_assignments (CASE ASSIGNMENT)
python scripts/init_db_ca.py

# Opcional: usar Alembic
alembic upgrade head
```

El script `init_db.py` hace:
1. Habilita extensión `pg_trgm`
2. Crea tabla `leads_cache`
3. Crea índice GIN para búsqueda fuzzy

El script `init_db_ca.py` crea la tabla `case_assignments` con sus 21+ campos personalizados.

### 6. Ejecutar localmente

```bash
# Modo desarrollo (con auto-reload)
uvicorn app.main:app --reload --port 8080

# Acceder a documentación interactiva
open http://localhost:8080/docs
```

## Deployment en Google Cloud Run

### 1. Configurar proyecto GCP

```bash
# Autenticarse
gcloud auth login

# Configurar proyecto
export GCP_PROJECT_ID="tu-proyecto-id"
export GCP_REGION="us-central1"

gcloud config set project $GCP_PROJECT_ID
```

### 2. Crear Cloud SQL instance

```bash
gcloud sql instances create nexus-legal-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$GCP_REGION

# Crear base de datos
gcloud sql databases create nexus_legal_db \
    --instance=nexus-legal-db

# Crear usuario
gcloud sql users create dbuser \
    --instance=nexus-legal-db \
    --password=SECURE_PASSWORD
```

### 3. Configurar Secret Manager

```bash
# Crear secrets
echo -n "pk_YOUR_CLICKUP_TOKEN" | gcloud secrets create CLICKUP_API_TOKEN --data-file=-
echo -n "your_webhook_secret" | gcloud secrets create CLICKUP_WEBHOOK_SECRET --data-file=-
echo -n "your_assignments_secret" | gcloud secrets create CLICKUP_WEBHOOK_SECRET_ASSIGNMENTS --data-file=-
echo -n "postgresql://user:pass@host/db" | gcloud secrets create DATABASE_URL --data-file=-
```

### 4. Deploy

```bash
# Opción 1: Script automatizado
./deploy.sh

# Opción 2: Manual con gcloud
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/nexus-legal-api

gcloud run deploy nexus-legal-api \
    --image gcr.io/$GCP_PROJECT_ID/nexus-legal-api \
    --region $GCP_REGION \
    --platform managed \
    --set-secrets CLICKUP_API_TOKEN=CLICKUP_API_TOKEN:latest \
    --min-instances 0 \
    --max-instances 10
```

## API Endpoints

### Health Check

```
GET /          → status, versión, entorno
GET /health    → {"status": "ok"}
```

### Webhooks ClickUp

**POST /webhooks/clickup**

Recibe eventos de la lista **CONSULTAS AGENDA** (taskUpdated, taskCreated).

- Verifica firma HMAC-SHA256 (`X-Signature`)
- Guarda lead en `leads_cache`
- Dispara en background: Enqueuer (Filtros IA) + Google Sheets
- Protección anti-bucle via campo `AI Link`

**POST /webhooks/assignments**

Recibe eventos de la lista **CASE ASSIGNMENT**.

- Verifica firma con secret independiente
- Mapea 21 custom fields via ID_MAP
- Guarda en tabla `case_assignments`

### Callbacks

**POST /callbacks/filtros**

Recibe respuesta del microservicio Filtros IA.

Payload esperado:
```json
{
  "task_id": "abc123",
  "status": "success",
  "outcome": "viable",
  "first_outcome": "POTENTIAL VAWA",
  "artifacts": {
    "doc_id": "...",
    "doc_url": "https://..."
  },
  "diagnostics": {
    "processing_time_ms": 1200,
    "version": "1.0"
  }
}
```

Al recibir éxito, actualiza los siguientes campos en ClickUp:

| Campo ClickUp | Tipo | Campo payload | Obligatorio |
|---|---|---|---|
| Link AI Filtro | `url` | `artifacts.doc_url` | Sí |
| 1st Outcome | `drop_down` | `first_outcome` | No |

**Valores válidos para `first_outcome`:**

| Etiqueta | UUID de opción |
|---|---|
| `DENIED` | `53e46014-6add-4b02-9afa-f90f2e158ec1` |
| `N/Q - TS` | `60eaca67-5a9c-4620-bd93-4afc19b46b6e` |
| `NO INFO/SOLO QUEST` | `efda53a6-acc4-44e7-88c2-9b511aa6f518` |
| `NON VAWA` | `c4516db1-a473-4603-919e-e1f47af5b846` |
| `NQ - FORCED LABOR` | `ed5f8ef1-e81d-47f0-80b0-ca2aecd55961` |
| `NQ - GMC` | `06c87578-65d7-42af-b9b6-e019f36e0828` |
| `NQ - VAWA/VISA T` | `174ae76a-fb7e-47aa-a54e-bd1a649a78dd` |
| `NQ - VISA U` | `0c3c2a4c-83c2-4012-b2a8-8891bd784729` |
| `NQ-NOT QAL RELATION` | `8c98f179-ef5b-4b82-baf3-edb8d42d05c8` |
| `Pass` | `94dcc461-ee3c-4b07-9afa-a203344e8352` |
| `POSSIBLE NON VAWA` | `64433fb2-b60b-4f43-9a06-6c463f9c1755` |
| `POTENTIAL VAWA` | `77c293fc-f305-42f0-924d-f1345bac054d` |
| `POTENTIAN VISA T` | `199e41b1-9d64-4f18-8e8c-e8afd17d6b72` |
| `Reactivation` | `544e383e-3f39-4d75-ba4c-1d343e6680fb` |
| `REESCREENING` | `8511a7e2-4354-435f-ad13-1f006a3aa594` |
| `VAWA - NEA` | `f09c6265-61f8-40fa-a42d-687f6849255b` |
| `VAWA SPOUSE` | `06ea9e6f-150b-42cd-b840-9c58051d9662` |
| `VISA U` | `dbff9536-51a0-4d5a-924d-26eda89bce99` |

> Si `first_outcome` no se incluye en el payload, solo se actualiza el campo `Link AI Filtro`. Si se incluye un valor inválido, la API retorna `422 Unprocessable Entity`.

### Búsqueda de Leads

**GET /leads/search?q=nombre&limit=10**

Búsqueda fuzzy por nombre (usa pg_trgm similarity).

Parámetros:
- `q`: Texto a buscar (min 2 caracteres)
- `limit`: Máximo de resultados (default 10, max 50)

**GET /leads/{task_id}**

Obtiene un lead por ID de tarea de ClickUp.

**GET /leads/mycase/{mycase_id}**

Obtiene un lead por MyCase ID (8 dígitos).

**GET /leads/?skip=0&limit=100**

Lista todos los leads con paginación.

## Configurar Webhooks en ClickUp

### CONSULTAS AGENDA

1. Ir a ClickUp → Settings → Integrations → Webhooks
2. Crear nuevo webhook:
   - **URL**: `https://YOUR-CLOUD-RUN-URL/webhooks/clickup`
   - **Events**: Task Updated, Task Created
   - **Secret**: (mismo que `CLICKUP_WEBHOOK_SECRET`)
3. O usar el script: `python scripts/register_webhook.py`

### CASE ASSIGNMENT

1. Crear otro webhook:
   - **URL**: `https://YOUR-CLOUD-RUN-URL/webhooks/assignments`
   - **Events**: Task Updated, Task Created
   - **Secret**: (mismo que `CLICKUP_WEBHOOK_SECRET_ASSIGNMENTS`)
2. O usar el script: `python scripts/register_webhook_assignments.py`

## Listas Soportadas

| Lista | Webhook | Tabla DB | Campos |
|-------|---------|----------|--------|
| CONSULTAS AGENDA | `/webhooks/clickup` | `leads_cache` | ~40 campos + búsqueda fuzzy |
| CASE ASSIGNMENT | `/webhooks/assignments` | `case_assignments` | 21 custom fields mapeados |

## Lógica de Parsing (CONSULTAS AGENDA)

El sistema extrae información de dos fuentes:

### 1. Metadatos nativos de ClickUp
- `task_name`, `status`, `assignee`, fechas, etc.

### 2. Mining del campo `task_content` (descripción)

Usa regex para extraer:

**Campos de línea simple:**
```
Name: Juan Perez
Phone: (555) 123-4567
Email: juan@example.com
```

**Campos de bloque:**
```
Other result of interview (optional):
[Texto multilínea capturado hasta "Type of Interview"]
```

**Normalización de nombres:**

```python
"López García | 12345678" →
  nombre_clickup: "López García"
  id_mycase: "12345678"
  nombre_normalizado: "LOPEZ GARCIA"  # Para búsqueda fuzzy
```

**Validación de teléfonos:**
- Extrae solo dígitos
- Valida longitud (10-15)
- Descarta si no cumple

## Mapeo de Campos (CASE ASSIGNMENT)

El servicio `AssignmentService` usa un `ID_MAP` que traduce 21 UUIDs de custom fields de ClickUp a columnas de la tabla `case_assignments`:

```python
ID_MAP = {
    "298c4ec5-...": "abogado_asignado",
    "a1c9d406-...": "proyecto",
    "a42586d8-...": "label_type",
    # ... 18 campos más
}
```

Campos incluidos: `abogado_asignado`, `proyecto`, `label_type`, `case_review_status`, `open_case_type`, `rapsheet_status`, `link_audio_cr`, `link_google_meet`, `cr_done_date`, `fecha_asignacion`, entre otros.

## Búsqueda Fuzzy (pg_trgm)

La búsqueda usa **trigramas** para encontrar nombres similares incluso con errores tipográficos:

```sql
SELECT * FROM leads_cache
WHERE nombre_normalizado % 'JUAN PEREZ'
ORDER BY similarity(nombre_normalizado, 'JUAN PEREZ') DESC
LIMIT 10;
```

**Requisitos:**
1. Extensión `pg_trgm` habilitada
2. Índice GIN en `nombre_normalizado`

```sql
CREATE EXTENSION pg_trgm;
CREATE INDEX idx_nombre_normalizado_gin ON leads_cache USING gin (nombre_normalizado gin_trgm_ops);
```

## Mantenimiento

### Ver logs en Cloud Run

```bash
gcloud run logs read nexus-legal-api --region $GCP_REGION --limit 100
```

### Ejecutar migraciones

```bash
# Generar migración automática
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Monitoreo

Cloud Run proporciona métricas automáticas:
- Latencia de requests
- Errores (4xx, 5xx)
- Uso de CPU/memoria
- Invocaciones

Acceder en: [Cloud Console → Cloud Run → Metrics](https://console.cloud.google.com/run)

## Seguridad

- **HTTPS/TLS**: Todo el tráfico es encriptado
- **Validación de webhooks**: Firma HMAC-SHA256 verificada por endpoint
- **Secrets independientes**: Cada lista tiene su propio webhook secret
- **Secrets Manager**: Credenciales nunca en código
- **Cloud SQL**: Encriptación en reposo por default
- **IAM**: Control de acceso granular

## Historial de Versiones

### Versión 2.3.0 (Marzo 2026)
- [x] **Campo 1st Outcome en callback**: El endpoint `/callbacks/filtros` ahora acepta opcionalmente el campo `first_outcome` (drop_down) para actualizar el resultado de la clasificación directamente en ClickUp
- [x] **Mapeo de opciones drop_down**: 18 valores válidos mapeados a UUIDs de opción de ClickUp en `FIRST_OUTCOME_OPTIONS`
- [x] **Validación automática**: Pydantic rechaza con `422` cualquier `first_outcome` que no esté en el catálogo definido
- [x] **Actualización no bloqueante**: Si el campo `1st Outcome` falla, el callback retorna éxito igual (el link principal ya fue guardado)

### Versión 2.2.1 (Febrero 2026)
- [x] **Soporte Multi-Lista**: Dos listas de ClickUp operando de forma independiente
- [x] **CASE ASSIGNMENT**: Nuevo webhook, modelo y servicio para lista de asignaciones
- [x] **21 Custom Fields**: Mapeo completo de campos personalizados para CASE ASSIGNMENT
- [x] **Scripts de inicialización**: `init_db_ca.py`, `import_case_assignments.py`, `register_webhook_assignments.py`
- [x] **Webhook secret independiente**: Cada lista valida con su propio secret

### Versión 2.2.0 (Enero 2026)
- [x] **Integración con Filtros IA (FIA)**: Envío automático de leads al microservicio de filtros inteligentes via Enqueuer
- [x] **Procesamiento en Background**: Tareas pesadas (dispatch, sheets) ejecutadas en segundo plano para respuesta rápida a ClickUp
- [x] **Protección contra Bucles**: Verificación de campo `AI Link` para evitar reprocesamiento
- [x] **Lista Optimizada**: Configuración para lista "CONSULTAS AGENDA" como fuente principal
- [x] **Callback URL**: Endpoint `/callbacks/filtros` para recibir respuestas del servicio de Filtros IA
- [x] **set_custom_field_value**: Actualización de campos en ClickUp desde callbacks

### Versión 2.1
- [x] **Integración con Google Sheets**: Sincronización automática vía Service Account
- [x] **External Dispatch**: Notificación HTTP a servicios externos (Enqueuer)
- [x] **Trigger Condicional**: Acciones basadas en campo "Link Intake"
- [x] **Filtrado por Lista**: Webhooks específicos para lista configurada

Ver [INTEGRATION_SETUP.md](INTEGRATION_SETUP.md) para instrucciones detalladas.

## Roadmap (Próximas Mejoras)

- [ ] Job nocturno con Cloud Scheduler (safety net)
- [ ] Extracción y almacenamiento del último comentario de tarea
- [ ] Exportación de datos (CSV, Excel)
- [ ] Dashboard de métricas (Looker Studio)
- [ ] Retry logic para dispatch fallido

## Soporte

Para issues o preguntas, contactar al equipo de desarrollo.

---

**Versión:** 2.3.0
**Última actualización:** 2026-03-03

## Documentación Adicional

- [INTEGRATION_SETUP.md](INTEGRATION_SETUP.md) - Guía de configuración de Google Sheets y External Dispatch
- [VARIABLES_DE_ENTORNO.md](VARIABLES_DE_ENTORNO.md) - Referencia completa de variables de entorno
- [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitectura técnica detallada
- [CHANGELOG.md](CHANGELOG.md) - Registro de cambios por versión
