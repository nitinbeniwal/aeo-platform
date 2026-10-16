from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM provider: auto | anthropic | openai | ollama | heuristic
    # auto resolves (in order): anthropic key -> openai key -> ollama running -> heuristic
    llm_provider: str = "auto"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # OpenAI-COMPATIBLE provider — bring your own key for ANY of:
    # OpenAI, OpenRouter, Groq, Mistral, Together, Fireworks, LM Studio, vLLM, etc.
    # Just point openai_base_url at the provider and set the matching model id.
    #   OpenAI:     https://api.openai.com/v1            gpt-4o-mini
    #   OpenRouter: https://openrouter.ai/api/v1         meta-llama/llama-3.1-70b-instruct
    #   Groq:       https://api.groq.com/openai/v1       llama-3.3-70b-versatile
    #   LM Studio:  http://localhost:1234/v1             (local, no key)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # Answer-engine probe key (AEO agent). Optional.
    perplexity_api_key: str = ""

    # Free local LLM (no API key). Install: https://ollama.com ; then `ollama pull llama3.2`
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    scraper_timeout: int = 30
    scraper_user_agent: str = "AEOBot/0.1 (+https://example.com/bot)"


@lru_cache
def get_settings() -> Settings:
    return Settings()
