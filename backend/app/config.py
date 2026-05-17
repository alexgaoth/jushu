from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    DATABASE_URL: str
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    SECRET_KEY: str = "changeme-please-set-a-real-secret"
    OPENAI_API_KEY: Optional[str] = None
    SCRAPER_SCHEDULER_ENABLED: bool = False
    SCRAPER_SCHEDULE_TIMEZONE: str = "UTC"
    BILIBILI_CRAWL_CRON: str = "0 3 * * *"
    NLP_PIPELINE_CRON: str = "20 3 * * *"
    BILIBILI_SCHEDULED_KEYWORDS: List[str] = [
        "社会热点",
        "时事吐槽",
        "网络热梗",
        "历史对比",
        "评论区",
        "懂的都懂",
    ]
    BILIBILI_SCHEDULED_KEYWORD_RESULTS: int = 10
    BILIBILI_SCHEDULED_MAX_PAGES: int = 5
    BILIBILI_SCHEDULED_MAX_DANMAKU: int = 150

    @field_validator("CORS_ORIGINS", "BILIBILI_SCHEDULED_KEYWORDS", mode="before")
    @classmethod
    def parse_list_field(cls, v):
        if isinstance(v, str):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # Fallback: treat as comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()
