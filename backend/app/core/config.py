from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/docextraction"

    # Both the first-pass and escalation models are deployments on the same
    # Azure AI Foundry resource, reachable through its OpenAI-SDK-compatible
    # v1 surface (base_url + model=<deployment name>, no per-call
    # api-version, no separate AzureOpenAI client) — one key covers every
    # deployment on the resource.
    foundry_api_key: str = ""
    foundry_base_url: str = "https://ai-training-msftfoundry.services.ai.azure.com/openai/v1/"
    deepseek_deployment: str = "deepseek-v3.2"

    # Escalation model — a second deployment on the same Foundry resource.
    azure_openai_deployment: str = "gpt-5"

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
