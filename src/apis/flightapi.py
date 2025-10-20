import asyncio
import json
from typing import Any, Literal

import httpx

from src.configs import ALLOWED_AIRPORT_CODES, FLIGHTAPI_BASE_URL
from src.apis.base import BaseFlightsApi
from src.services.inmemory_cache import InMemoryTTLCache


class FlightApi(BaseFlightsApi):
    def __init__(self, api_key: str, cache_ttl_seconds: int = 60 * 60 * 12, cache_dump_path: str | None = 'tmp/flight_cache.json'):
        if not api_key:
            raise ValueError('FlightAPI key is required')

        self.api_key = api_key
        self.base_url = FLIGHTAPI_BASE_URL
        self.client = httpx.AsyncClient(
            timeout=10,
            headers={
                'Content-Type': 'application/json',
            },
        )
        self.cache = InMemoryTTLCache(cache_ttl_seconds, dump_path=cache_dump_path)
        self.cache.load_from_disk()

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f'{self.base_url}{path}/{self.api_key}'
        cache_key = json.dumps({'u': url, 'p': params}, sort_keys=True)
        cached = self.cache.get(cache_key)

        if cached is not None:
            return cached

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            self.cache.set(cache_key, data)
            self.cache.dump_to_disk()
            return data

        except httpx.HTTPError:
            if cached is not None:
                return cached
            raise


    async def fetch_schedule(self, iata: str, mode: Literal['arrivals', 'departures'], day: int = 1) -> dict[str, Any]:
        if iata not in ALLOWED_AIRPORT_CODES:
            raise ValueError(f'Invalid airport code. Allowed codes: {ALLOWED_AIRPORT_CODES}')

        path = '/schedule'
        params = {
            'iata': iata,
            'mode': mode,
            'day': day,
        }
        try:
            return await self._get(path, params)

        except httpx.HTTPError:
            return {}

    @staticmethod
    def normalize_flight_data(raw_data: dict[str, Any]) -> list[dict[str, Any]]:
        schedule_data = raw_data.get('airport', {}).get('pluginData', {}).get('schedule', {}).get('arrivals', {}).get('data', []) or raw_data.get('airport', {}).get('pluginData', {}).get('schedule', {}).get('departures', {}).get('data', [])

        norm: list[dict[str, Any]] = []
        for it in schedule_data:
            flight = it.get('flight', {})
            airline = flight.get('airline') or {}
            flight_num = flight.get('identification', {}).get('number', {}).get('default') or flight.get('identification', {}).get('number', {}).get('alternative')
            dep = flight.get('airport', {}).get('origin') or {}
            arr = flight.get('airport', {}).get('destination') or {}
            time = flight.get('time') or {}
            sched_dep = flight.get('scheduledDepartureTime') or (time.get('scheduled') or {}).get('departure') or time.get('scheduled')
            est_dep = flight.get('estimatedDepartureTime') or (time.get('estimated') or {}).get('departure')
            sched_arr = flight.get('scheduledArrivalTime') or (time.get('scheduled') or {}).get('arrival') or time.get('scheduled')
            est_arr = flight.get('estimatedArrivalTime') or (time.get('estimated') or {}).get('arrival') or (time.get('real') or {}).get('utc')
            status = flight.get('status')
            aircraft = flight.get('aircraft') or {}

            aircraft_model = aircraft.get('model') or (aircraft.get('model', {}) or {}).get('text')
            aircraft_code = aircraft.get('code') or (aircraft.get('model', {}) or {}).get('code')

            norm.append({
                'flightNumber': flight_num,
                'airline': {
                    'name': airline.get('name') or airline.get('short') or airline.get('fullName'),
                    'iata': airline.get('iata') or airline.get('code'),
                },
                'departureAirport': {
                    'iata': dep.get('code', {}).get('iata'),
                    'city': dep.get('position', {}).get('region', {}).get('city'),
                    'country': dep.get('position', {}).get('country', {}).get('name'),
                    'countryCode': dep.get('position', {}).get('country', {}).get('code'),
                },
                'arrivalAirport': {
                    'iata': arr.get('code', {}).get('iata'),
                    'city': arr.get('position', {}).get('region', {}).get('city'),
                    'country': arr.get('position', {}).get('country', {}).get('name'),
                    'countryCode': arr.get('position', {}).get('country', {}).get('code'),
                },
                'scheduledDepartureTime': sched_dep,
                'estimatedDepartureTime': est_dep,
                'scheduledArrivalTime': sched_arr,
                'estimatedArrivalTime': est_arr,
                'status': status,
                'aircraft': {
                    'model': aircraft_model,
                    'code': aircraft_code,
                },
            })
        return norm

    async def get_today_flights(self, airport: str) -> dict[str, list[dict[str, Any]]]:
        t_arrivals_raw = asyncio.create_task(self.fetch_schedule(airport, 'arrivals', day=1))
        t_departures_raw = asyncio.create_task(self.fetch_schedule(airport, 'departures', day=1))

        arrivals_raw = await t_arrivals_raw
        departures_raw = await t_departures_raw

        return {
            'arrivals': self.normalize_flight_data(arrivals_raw),
            'departures': self.normalize_flight_data(departures_raw),
        }


