#app/config.py
"""
Configuración centralizada usando Pydantic Settings.
Lee desde variables de entorno o .env
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

    # ClickUp
    clickup_api_token: str = "pk_88282073_3EL5TAYA7G4VB5W7AFXXRD9PE3K231J0"
    clickup_webhook_secret: str
    clickup_team_id: Optional[str] = None
    clickup_list_id: Optional[str] = "901403238634"
    clickup_trigger_condicional: Optional[str] = None
    clickup_field_id_ai_link: Optional[str] = "3aa46502-0763-42d3-8cb9-71513566e3ae"
    clickup_webhook_secret_assignments: str = "10VI1B1T82MO55WX9KRQTEOG1XLZYDTM2PDCIYW8HT1LGTYFY1FNY7796K0P5P6V"
    clickup_field_id_link_intake: str = "1c35f9be-9fe2-4a0c-b0af-9f4f92dd4554"
    
    # Database
    database_host: str = "/cloudsql/ortega-473114:us-central1:nexus-legal-db"
    database_port: int = 5432
    database_name: str = "nexus_legal_db"
    database_user: str = "nexus_user"
    database_password: str = "nr5EPzU1fDQph1Kb*"
    database_url: Optional[str] = None
    database_ssl_mode: str = "disable"

    # Google Sheets
    google_sheets_enabled: bool = True
    google_sheets_spreadsheet_id: Optional[str] = "161uBv2YTWOiR-82zlsf6ANbiqtfiow8B4x62VXCTPwU"
    google_sheets_sheet_name: str = "Leads DVS"
    google_sheets_credentials_path: Optional[str] = None
    google_sheets_credentials_json: Optional[str] = None
    google_sheets_field_mapping: Optional[str] = '{"task_id": 1, "task_name": 2, "status": 3, "name": 4, "dvs_name": 5, "link_intake": 6, "url": 7, "date_created": 8, "date_updated": 9}'

    # External Dispatch (HTTP POST on webhook trigger)
    external_dispatch_enabled: bool = True
    external_dispatch_url: Optional[str] = "https://enqueuer-api-907757756276.us-central1.run.app/enqueue"
    filtros_api_key: Optional[str] = "tu-api-key-real"
    external_dispatch_callback_base_url: Optional[str] = "https://nexus-legal-api-223080314602.us-central1.run.app"

    # Application
    app_env: str = "production"
    debug: bool = False
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "*"

    # Security
    encryption_key: Optional[str] = None

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
        Formato esperado: {"task_name": 1, "phone": 2, "email": 3}
        """
        if self.google_sheets_field_mapping:
            try:
                return json.loads(self.google_sheets_field_mapping)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in GOOGLE_SHEETS_FIELD_MAPPING: {e}")
        return {}


# Singleton
settings = Settings()
