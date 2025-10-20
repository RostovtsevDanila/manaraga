from nicegui import ui

from src.fe import register_ui
from src.services.assistant import FlightAssistantService
from src.services.sessions import SessionManager

session_manager = SessionManager()
service = FlightAssistantService()
register_ui(session_manager, service)
ui.run(title='Flight Assistant', reload=False, port=8080)
