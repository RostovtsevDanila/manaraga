import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.apis.flightapi import FlightApi
from src.configs import (
    CACHE_FILE_PATH,
    CACHE_TTL_SECONDS,
    MEMORY_LEN_MESSAGES,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    SYSTEM_PROMPT,
)
from src.services.sessions import SessionData


class FlightAssistantService:
    def __init__(self) -> None:
        pass

    @staticmethod
    async def ensure_dependencies(session: SessionData, user_key: str) -> None:
        if session.llm is None:
            session.llm = ChatOpenAI(
                base_url=OPENAI_BASE_URL,
                model_name=OPENAI_MODEL,
                streaming=True,
                openai_api_key=OPENAI_API_KEY,
            )
        if session.flight_api is None:
            session.flight_api = FlightApi(
                api_key=user_key,
                cache_ttl_seconds=CACHE_TTL_SECONDS,
                cache_dump_path=CACHE_FILE_PATH,
            )

    @staticmethod
    async def build_messages(session: SessionData, airport: str, question: str) -> list:
        today = await session.flight_api.get_today_flights(airport)
        arrivals_dataset = today['arrivals']
        departures_dataset = today['departures']

        dataset_json = json.dumps(
            {
                'airport': airport,
                'date': datetime.now(UTC).strftime('%Y-%m-%d'),
                'arrivals': arrivals_dataset,
                'departures': departures_dataset,
            },
            ensure_ascii=False,
        )

        return (
            [  # noqa: RUF005
                SystemMessage(content=SYSTEM_PROMPT),
                SystemMessage(content=f'SELECTED_AIRPORT={airport}'),
                SystemMessage(content=f'DATASET_JSON={dataset_json}'),
            ]
            + session.history
            + [HumanMessage(content=question)]
        )

    @staticmethod
    async def stream_answer(session: SessionData, messages: list) -> AsyncGenerator[str, Any]:
        response = ''
        async for chunk in session.llm.astream(messages):
            response += chunk.content
            yield response

    @staticmethod
    def persist_history(session: SessionData, question: str, answer: str) -> None:
        session.history.append(HumanMessage(content=question))
        session.history.append(AIMessage(content=answer))

        if len(session.history) > MEMORY_LEN_MESSAGES:
            session.history = session.history[-MEMORY_LEN_MESSAGES:]
