from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    nova_ref_db_host: str = "localhost"
    nova_ref_db_port: int = 5432
    nova_ref_db_name: str = "nova_ref_db"
    nova_ref_db_user: str = "nova_ref"
    nova_ref_db_pass: str = "changeme"
    nova_learn_db_pool_min: int = 1
    nova_learn_db_pool_max: int = 5
    nova_learn_db_pool_idle_timeout: int = 300

    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    @property
    def db_dsn(self) -> str:
        return (
            f"host={self.nova_ref_db_host} port={self.nova_ref_db_port} "
            f"dbname={self.nova_ref_db_name} user={self.nova_ref_db_user} password={self.nova_ref_db_pass}"
        )


settings = Settings()
