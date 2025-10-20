import json
from datetime import UTC, datetime
from typing import Any, AsyncGenerator

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.configs import (
    CACHE_FILE_PATH,
    CACHE_TTL_SECONDS,
    MEMORY_LEN_MESSAGES,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    SYSTEM_PROMPT,
)
from src.apis.flightapi import FlightApi
from src.services.sessions import SessionData


class FlightAssistantService:
    def __init__(self) -> None:
        pass

    async def ensure_dependencies(self, session: SessionData, user_key: str) -> None:
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

    async def build_messages(self, session: SessionData, airport: str, question: str) -> list:
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

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            SystemMessage(content=f'SELECTED_AIRPORT={airport}'),
            SystemMessage(content=f'DATASET_JSON={dataset_json}'),
        ] + session.history + [HumanMessage(content=question)]

        return messages

    async def stream_answer(self, session: SessionData, messages: list) -> AsyncGenerator[str, Any]:
        response = ''
        async for chunk in session.llm.astream(messages):
            response += chunk.content
            yield response

    def persist_history(self, session: SessionData, question: str, answer: str) -> None:
        session.history.append(HumanMessage(content=question))
        session.history.append(AIMessage(content=answer))

        if len(session.history) > MEMORY_LEN_MESSAGES:
            session.history = session.history[-MEMORY_LEN_MESSAGES:]
