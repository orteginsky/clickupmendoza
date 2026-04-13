# app/config.py
"""
Configuración centralizada usando Pydantic Settings.
Lee desde variables de entorno (Cloud Run) o archivo .env (desarrollo local).

IMPORTANTE: Este archivo no debe contener valores reales de producción.
- Secrets (tokens, passwords, webhook secrets) → GCP Secret Manager
- Config no-sensible (IDs, URLs, flags) → variables de entorno en cloudbuild.yaml
- Desarrollo local → archivo .env (ignorado por git)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import json


class Settings(BaseSettings):
    """Configuración de la aplicación"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ClickUp — tokens y secrets vienen de Secret Manager
    clickup_api_token: str
    clickup_webhook_secret: str
    clickup_webhook_secret_assignments: str
    clickup_webhook_secret_strategy: Optional[str] = "REPLACE_ME"
    clickup_team_id: Optional[str] = None
    clickup_list_id: Optional[str] = None
    clickup_trigger_condicional: Optional[str] = None
    clickup_field_id_ai_link: Optional[str] = None
    clickup_field_id_link_intake: Optional[str] = None

    # Database — password viene de Secret Manager
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "nexus_legal_db"
    database_user: str = "postgres"
    database_password: str
    database_url: Optional[str] = None
    database_ssl_mode: str = "disable"

    # Google Sheets
    google_sheets_enabled: bool = True
    google_sheets_spreadsheet_id: Optional[str] = None
    google_sheets_sheet_name: str = "Leads DVS"
    google_sheets_credentials_path: Optional[str] = None
    google_sheets_credentials_json: Optional[str] = None
    google_sheets_field_mapping: Optional[str] = None

    # External Dispatch (Enqueuer + Filtros IA)
    external_dispatch_enabled: bool = True
    external_dispatch_url: Optional[str] = None
    filtros_api_key: Optional[str] = None
    external_dispatch_callback_base_url: Optional[str] = None

    # Application
    app_env: str = "production"
    debug: bool = False
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "*"

    # Security
    encryption_key: Optional[str] = None

    # Drive Sync
    drive_sync_secret: Optional[str] = None    # Bearer token para autenticar llamadas desde AppScript

    @property
    def database_dsn(self) -> str:
        """Construye la URL de conexión a la DB"""
        if self.database_url:
            return self.database_url

        # Si estamos en Cloud Run (identificado por la ruta del socket)
        if self.database_host.startswith("/cloudsql/"):
            return (
                f"postgresql://{self.database_user}:{self.database_password}"
                f"@/{self.database_name}?host={self.database_host}"
            )

        # Si estamos en local (IP/localhost)
        return (
            f"postgresql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
            f"?sslmode={self.database_ssl_mode}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """Convierte CORS_ORIGINS en lista"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def google_credentials_dict(self) -> Optional[dict]:
        """
        Parsea las credenciales de Google Service Account.
        Prioriza JSON string (para Cloud Run/Secrets) sobre file path.
        """
        if self.google_sheets_credentials_json:
            try:
                return json.loads(self.google_sheets_credentials_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in GOOGLE_SHEETS_CREDENTIALS_JSON: {e}")
        return None

    @property
    def sheets_field_mapping_dict(self) -> dict:
        """
        Convierte el mapeo de campos JSON a diccionario.
        Formato esperado: {"campo_task": numero_columna}
        """
        if self.google_sheets_field_mapping:
            try:
                return json.loads(self.google_sheets_field_mapping)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in GOOGLE_SHEETS_FIELD_MAPPING: {e}")
        return {}


# Singleton
settings = Settings()
