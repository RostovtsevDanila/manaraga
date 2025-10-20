from nicegui import ui

from src.configs import ALLOWED_AIRPORT_CODES
from src.services.assistant import FlightAssistantService
from src.services.sessions import SessionManager


def register_ui(session_manager: SessionManager, service: FlightAssistantService) -> None:
    @ui.page('/')
    async def main():
        client_id = ui.context.client.id
        session = session_manager.get(client_id)

        async def send() -> None:
            question = text.value
            text.value = ''

            selected_option = selector.value
            if not selected_option:
                ui.notify('Please select an airport', color='negative')
                return

            user_key = session.flightapi_key or ''
            if not user_key.strip():
                ui.notify('Please enter FlightAPI key above', color='negative')
                return

            with message_container:
                you_message = ui.chat_message(name='You', sent=True)
                with you_message:
                    ui.markdown(question)
                response_message = ui.chat_message(name='Flights Bot', sent=False)
                spinner = ui.spinner(type='ios')

            try:
                await service.ensure_dependencies(session, user_key)
                messages = await service.build_messages(session, selected_option, question)

                answer = ''
                async for partial in service.stream_answer(session, messages):
                    answer = partial
                    response_message.clear()
                    with response_message:
                        ui.markdown(answer)
                    await ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')

                service.persist_history(session, question, answer)
                session_manager.set_selected(client_id, selected_option)
            except Exception as e:
                ui.notify(f'Error: {e}', color='negative')
            finally:
                message_container.remove(spinner)

        ui.add_css(r'a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}')

        ui.query('.q-page').classes('flex  justify-center')
        ui.query('.nicegui-content').classes('w-full flex items-center justify-center')

        with ui.row().classes('w-full max-w-2xl mx-auto items-center justify-center mt-4'):
            key_input = ui.input(
                label='FlightAPI key',
                placeholder='Please enter FlightAPI key...',
                password=True,
                password_toggle_button=True,
                value=session.flightapi_key,
            ).props('dense outlined clearable').classes('w-full')

            def on_key_change(e):
                session_manager.set_flightapi_key(client_id, e.value or '')

            key_input.on_value_change(on_key_change)

        with ui.tabs().classes('w-full') as tabs:
            chat_tab = ui.tab('Chat')

        with ui.tab_panels(tabs, value=chat_tab).classes('w-full max-w-2xl mx-auto flex-grow items-stretch'):
            message_container = ui.tab_panel(chat_tab).classes('items-stretch')

        with ui.footer().classes('bg-white'), ui.column().classes('w-full max-w-3xl mx-auto my-6 items-center'):
            with ui.row().classes('w-full no-wrap items-center justify-center'):
                placeholder = 'Enter your question here...'
                selector = ui.select(
                    options=list(ALLOWED_AIRPORT_CODES),
                    with_input=False,
                    label='Airport',
                    value=session.selected,
                ).props('dense outlined').classes('min-w-[180px]')

                selector.on_value_change(lambda e: session_manager.set_selected(client_id, e.value))
                text = ui.input(placeholder=placeholder).props('rounded outlined input-class=mx-3').classes('w-full self-center').on('keydown.enter', send)
