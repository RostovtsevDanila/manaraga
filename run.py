from nicegui import ui

from src.fe import register_ui
from src.services.assistant import FlightAssistantService
from src.services.sessions import SessionManager


def main() -> None:
    session_manager = SessionManager()
    service = FlightAssistantService()
    register_ui(session_manager, service)
    ui.run(title='Flights Discovery', reload=False)


if __name__ == '__main__':
    main()
