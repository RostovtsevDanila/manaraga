from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.apis.base import BaseFlightsApi

Message = SystemMessage | HumanMessage | AIMessage


class SessionData(BaseModel):
    history: list[Message] = Field(default_factory=list)
    selected: str | None = None
    flightapi_key: str = ''
    llm: ChatOpenAI | None = None
    flight_api: BaseFlightsApi | None = None


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[int, SessionData] = {}

    def get(self, client_id: int) -> SessionData:
        if client_id not in self._sessions:
            self._sessions[client_id] = SessionData()
        return self._sessions[client_id]

    def set_selected(self, client_id: int, value: str | None) -> None:
        session = self.get(client_id)
        session.selected = value

    def set_flightapi_key(self, client_id: int, key: str) -> None:
        session = self.get(client_id)
        session.flightapi_key = key or ''
