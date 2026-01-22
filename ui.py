from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, ScrollableContainer
from textual.widgets import Button, Footer, Header, DataTable
from textual.reactive import reactive
from document import Document


class Sheet(DataTable):
    def on_data_table_cell_selected(self, event: DataTable.CellSelected):
        with open("output", "a") as file:
            file.write(str(event) + "\n")


class UI(App):
    TITLE = "Grades"
    CSS_PATH = "ui.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self, doc: Document):
        super().__init__()
        self.doc = doc

    def compose(self) -> ComposeResult:
        yield Header()
        yield Sheet(id="sheet")
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
    doc = Document.from_file("test.json")
    UI(doc).run()
