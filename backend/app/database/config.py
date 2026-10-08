from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from app.runtime_paths import (
    DATABASE_PATH,
)


class Settings(
    BaseSettings
):
    database_url: str = (
        f"sqlite:///{DATABASE_PATH}"
    )

    model_config = (
        SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
        )
    )


settings = Settings()