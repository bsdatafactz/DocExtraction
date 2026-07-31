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

    # $ per 1,000,000 tokens, used by services/cost.py to turn the token
    # counts captured off each API response into a dollar figure. Defaults
    # are Azure AI Foundry's published list pricing for deepseek-v3.2 and
    # gpt-5 (looked up 2026-07-30) — override here or in .env if this
    # account's contracted rate differs.
    deepseek_input_price_per_1m: float = 0.58
    deepseek_output_price_per_1m: float = 1.68
    azure_openai_input_price_per_1m: float = 1.25
    azure_openai_output_price_per_1m: float = 10.00

    # Aggregate confidence below this triggers escalation to the stronger model.
    # There is no confidence-based auto-approval — every document requires a
    # human review step regardless of score.
    confidence_escalation_threshold: float = 0.75

    upload_dir: str = "./uploads"

    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24 * 7


settings = Settings()
