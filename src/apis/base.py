import json
from abc import ABC, abstractmethod
from typing import Any, Literal

import httpx


class BaseFlightsApi(ABC):
    @abstractmethod
    async def fetch_schedule(self, iata: str, mode: Literal['arrivals', 'departures'], day: int = 1) -> dict[str, Any]:
        """Fetch raw schedule data from provider API."""

    @staticmethod
    @abstractmethod
    def normalize_flight_data(raw_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Normalize provider-specific schema to a common schema."""

    @abstractmethod
    async def get_today_flights(self, airport: str) -> dict[str, list[dict[str, Any]]]:
        """Convenience method to fetch today's arrivals and departures for an airport."""
