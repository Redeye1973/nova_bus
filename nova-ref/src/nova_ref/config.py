from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    nova_ref_db_host: str = "localhost"
    nova_ref_db_port: int = 5432
    nova_ref_db_name: str = "nova_ref_db"
    nova_ref_db_user: str = "nova_ref"
    nova_ref_db_pass: str = "changeme"
    nova_ref_db_pool_min: int = 2
    nova_ref_db_pool_max: int = 10
    nova_ref_db_pool_idle_timeout: int = 300

    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""
    learn_service_url: str = "http://localhost:8401"
    surilians_codex_path: str = "/opt/nova/codex/surilians"
    adapter_wikidata_enabled: bool = True
    adapter_pdok_bag_enabled: bool = True
    adapter_surilians_enabled: bool = True
    cache_ttl_default_days: int = 30
    cache_ttl_fictional_days: int = 36500

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    @property
    def db_dsn(self) -> str:
        return (
            f"host={self.nova_ref_db_host} port={self.nova_ref_db_port} "
            f"dbname={self.nova_ref_db_name} user={self.nova_ref_db_user} password={self.nova_ref_db_pass}"
        )


settings = Settings()
