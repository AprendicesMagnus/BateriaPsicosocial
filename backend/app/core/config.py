from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_database_url(url: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query))
    query.pop("schema", None)
    return urlunparse(parsed._replace(query=urlencode(query)))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    env: str = "development"

    database_url: str = ""
    test_database_url: str = ""

    port: int = 8000
    frontend_url: str = "http://localhost:5173"

    wompi_api_url: str = "https://sandbox.wompi.co/v1"
    wompi_public_key: str = ""
    wompi_private_key: str = ""
    wompi_events_secret: str = ""
    wompi_integrity_secret: str = ""

    jwt_secret: str = ""
    encryption_key: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = "Magnus|SIG <no-reply@magnussig.local>"

    admin_email: str = ""
    admin_password: str = ""
    admin_nombre: str = "Administrador"
    admin_apellido: str = "Sistema"

    storage_path: str = "./storage"

    min_grupo_anonimato: int = 5

    jwt_expira_minutos: int = 120
    reset_expira_minutos: int = 15
    codigo_expira_minutos: int = 15

    max_intentos_login: int = 5
    bloqueo_minutos: int = 15

    def model_post_init(self, __context) -> None:
        if not self.database_url.strip():
            raise ValueError(
                "DATABASE_URL es obligatorio y debe estar configurado."
            )

        if self.env.lower() == "production":
            if not self.jwt_secret.strip():
                raise ValueError(
                    "En producción es obligatorio configurar JWT_SECRET."
                )

            if len(self.jwt_secret.strip()) < 32:
                raise ValueError(
                    "JWT_SECRET debe tener al menos 32 caracteres en producción."
                )

            if not self.encryption_key.strip():
                raise ValueError(
                    "En producción es obligatorio configurar ENCRYPTION_KEY."
                )

            if not self.admin_password.strip():
                raise ValueError(
                    "En producción es obligatorio configurar ADMIN_PASSWORD."
                )

            if not self.wompi_public_key.strip():
                raise ValueError(
                    "En producción es obligatorio configurar WOMPI_PUBLIC_KEY."
                )

            if not self.wompi_private_key.strip():
                raise ValueError(
                    "En producción es obligatorio configurar WOMPI_PRIVATE_KEY."
                )

            if not self.wompi_integrity_secret.strip():
                raise ValueError(
                    "En producción es obligatorio configurar "
                    "WOMPI_INTEGRITY_SECRET."
                )

            if not self.wompi_events_secret.strip():
                raise ValueError(
                    "En producción es obligatorio configurar "
                    "WOMPI_EVENTS_SECRET."
                )

    @property
    def sqlalchemy_database_url(self) -> str:
        return _normalize_database_url(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()