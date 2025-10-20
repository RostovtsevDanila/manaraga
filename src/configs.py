import os
from typing import Set

from pydantic import BaseModel, field_validator


class Settings(BaseModel):
    # Flights
    allowed_airport_codes: Set[str] = {'DXB', 'LHR', 'CDG', 'SIN', 'HKG', 'AMS'}
    flightapi_base_url: str = 'https://api.flightapi.io'
    cache_ttl_seconds: int = 60 * 60 * 12
    cache_file_path: str = 'tmp/flight_cache.json'

    # LLM
    system_prompt: str = (
        'You are an aviation assistant. Answer strictly about the selected airport and only for today. '
        'Use ONLY the provided dataset when answering. '
        'If the question is outside the dataset scope, say that you just have no enough data for answer. '
    )
    memory_len_messages: int = 40
    openai_api_key: str = ''
    openai_model: str = 'tngtech/deepseek-r1t2-chimera:free'
    openai_base_url: str = 'https://openrouter.ai/api/v1'

    @field_validator('openai_api_key', mode='before')
    @classmethod
    def default_openai_key_from_env(cls, v: str) -> str:
        return v or os.getenv('OPENAI_API_KEY', '')


def load_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv('OPENAI_API_KEY', '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'),
        openai_model=os.getenv('OPENAI_MODEL', 'tngtech/deepseek-r1t2-chimera:free'),
        openai_base_url=os.getenv('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1'),
        flightapi_base_url=os.getenv('FLIGHTAPI_BASE_URL', 'https://api.flightapi.io'),
        cache_ttl_seconds=int(os.getenv('CACHE_TTL_SECONDS', str(60 * 60 * 12))),
        cache_file_path=os.getenv('CACHE_FILE_PATH', 'tmp/flight_cache.json'),
        allowed_airport_codes=set(
            [it.strip().upper() for it in os.getenv('ALLOWED_AIRPORT_CODES', '').split(',') if it.strip()] or
            ['DXB', 'LHR', 'CDG', 'SIN', 'HKG', 'AMS']
        ),
        memory_len_messages=int(os.getenv('MEMORY_LEN_MESSAGES', '40')),
        system_prompt=os.getenv('SYSTEM_PROMPT', Settings().system_prompt),
    )


# Keep backward-compatible constants for existing imports
_settings = load_settings()

ALLOWED_AIRPORT_CODES = _settings.allowed_airport_codes
FLIGHTAPI_BASE_URL = _settings.flightapi_base_url
CACHE_TTL_SECONDS = _settings.cache_ttl_seconds
CACHE_FILE_PATH = _settings.cache_file_path

SYSTEM_PROMPT = _settings.system_prompt
MEMORY_LEN_MESSAGES = _settings.memory_len_messages
OPENAI_API_KEY = _settings.openai_api_key
OPENAI_MODEL = _settings.openai_model
OPENAI_BASE_URL = _settings.openai_base_url
