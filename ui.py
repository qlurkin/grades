from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, ScrollableContainer
from textual.widgets import Button, Footer, Header, DataTable
from textual.reactive import reactive


class UI(App):
    TITLE = "Grades"
    CSS_PATH = "ui.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="sheet")
        yield Footer()

    def on_mount(self) -> None:
        self.table = self.query_one(DataTable)

        self.table.add_column("name", key="name")
        self.table.add_column("project", key="project")
        self.table.add_column("exam", key="exam")
        self.table.add_column("total", key="total")

        for i in range(20):
            self.table.add_row("", "", "", label=f"240{i:0>2}", key=f"240{i:0>2}")

        self.table.cursor_type = "cell"
        self.table.focus()


if __name__ == "__main__":
    UI().run()
