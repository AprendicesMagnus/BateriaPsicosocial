from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_database_url(url: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query))
    query.pop("schema", None)
    return urlunparse(parsed._replace(query=urlencode(query)))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql://usuario:contrasena@localhost:5432/magnussing"
    test_database_url: str = "postgresql://postgres:12345@localhost:5432/magnussing_test"
    port: int = 4000
    port: int = 4000
    frontend_url: str = "http://localhost:5173"

    wompi_api_url: str = "https://sandbox.wompi.co/v1"
    wompi_public_key: str = ""
    wompi_private_key: str = ""
    wompi_events_secret: str = ""
    wompi_integrity_secret: str = ""

    jwt_secret: str = "B-Iqrp_tK8OJi4P1cpZH-9eHxWfJHvv2C0Ta88pXBCCXMyMkFZ5P32SOtwZvla8HVYySUwpFpBqOBLmzu_f-bw"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = "Magnus|SIG <no-reply@magnussig.local>"
    admin_email: str = "admin@magnussig.com"
    admin_password: str = "Admin1234"
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
        if self.env.lower() == "production":
            if self.jwt_secret == "cambia-este-valor-por-una-cadena-larga-y-aleatoria":
                raise ValueError("En producción es obligatorio configurar un JWT_SECRET seguro.")
            if not self.encryption_key:
                raise ValueError("En producción es obligatorio configurar ENCRYPTION_KEY.")
            if self.admin_password == "Admin1234":
                raise ValueError("En producción es obligatorio cambiar la contraseña por defecto de ADMIN_PASSWORD.")

    @property
    def sqlalchemy_database_url(self) -> str:
        return _normalize_database_url(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
