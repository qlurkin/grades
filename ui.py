from typing import Callable
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, Grid
from textual.widgets import Button, Footer, Header, DataTable, Label, Input
from textual.widgets.data_table import RowKey, ColumnKey, CellType
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.message import Message
from document import Document


class DocumentUpdate(Message):
    def __init__(self, row: str, column: str, value):
        self.row = row
        self.column = column
        self.value = value
        super().__init__()


class Sheet(DataTable):
    def on_data_table_cell_selected(self, event: DataTable.CellSelected):
        col_name = event.cell_key.column_key.value
        type = str if self.app.doc.column_type(col_name) == "string" else float  # type: ignore
        value = "" if event.value is None else str(event.value)
        self.app.push_screen(
            CellInputScreen(
                event.cell_key.row_key, event.cell_key.column_key, value, type
            )
        )


class CellInputScreen(ModalScreen):
    def __init__(
        self,
        row: RowKey,
        column: ColumnKey,
        value: str,
        type: Callable,
    ):
        super().__init__()
        self.value = value
        self.row = row
        self.column = column
        self.type = type

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(f"{self.column.value} for {self.row.value}"),
            Input(self.value, placeholder=self.value),
            Button("Ok", variant="success", id="ok"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            row = self.row.value
            column = self.column.value
            assert isinstance(row, str)
            assert isinstance(column, str)
            value = self.type(self.query_one(Input).value)
            self.post_message(DocumentUpdate(row, column, value))
            self.app.pop_screen()
        else:
            self.app.pop_screen()


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
        yield Sheet()
        yield Footer()

    def on_mount(self) -> None:
        self.table = self.query_one(DataTable)

        self.render_table()

        self.table.cursor_type = "cell"
        self.table.focus()

    def on_document_update(self, event: DocumentUpdate):
        self.doc[event.row, event.column] = event.value
        self.render_table()

    def render_table(self):
        self.table.clear(columns=True)

        cols = self.doc.column_names

        for name in cols:
            self.table.add_column(name, key=name)

        for index in self.doc.indexes:
            row = self.doc.index(index)
            values = [row[key] for key in cols]
            self.table.add_row(*values, label=index, key=index)


if __name__ == "__main__":
    doc = Document.from_file("test.json")
    UI(doc).run()
