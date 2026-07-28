from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/docextraction"

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"

    # Escalation model — Azure AI Foundry-hosted OpenAI deployment, not a
    # raw model name. Set these from the Foundry deployment's "Endpoint"
    # and "Deployment name" fields.
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = ""
    azure_openai_api_version: str = "2024-08-01-preview"

    # Aggregate confidence below this triggers escalation to the stronger model.
    confidence_escalation_threshold: float = 0.75
    # Aggregate confidence below this (post-escalation) routes to human
    # review; at or above it, a document auto-approves with no human step.
    confidence_review_threshold: float = 0.9

    upload_dir: str = "./uploads"

    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24 * 7


settings = Settings()
