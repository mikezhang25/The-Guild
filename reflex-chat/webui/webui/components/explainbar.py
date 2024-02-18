import reflex as rx

from webui import styles
from webui.state import State
from webui.components import explainbar

def explainbar() -> rx.Component:
    """The sidebar component."""
    return rx.scroll_area(
    rx.flex(
        rx.text(
            """Justification""",
        ),
        rx.text(
            """explain""",
        ),
        direction="column",
        spacing="4",
    ),
    type="always",
    scrollbars="vertical",
    style={"height": 90},
    placement="right",
    position="right",
)
    # return rx.chakra.drawer(
    #     rx.chakra.drawer_content(
    #         rx.chakra.drawer_header(
    #             rx.chakra.hstack(
    #                 rx.chakra.text("Chats"),
    #             )
    #         ),
    #     ),
    #     placement="right",
    #     # is_open=State.explain_bar_open,
    # )
