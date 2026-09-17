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

    database_url: str = "postgresql://usuario:contrasena@localhost:5432/magnussing"
    test_database_url: str = "postgresql://postgres:12345@localhost:5432/magnussing_test"
    port: int = 4000
    frontend_url: str = "http://localhost:5173"
    jwt_secret: str = "cambia-este-valor-por-una-cadena-larga-y-aleatoria"
    encryption_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = "Magnus|SIG <no-reply@magnussig.local>"
    admin_email: str = "admin@magnussig.local"
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

    @property
    def sqlalchemy_database_url(self) -> str:
        return _normalize_database_url(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
