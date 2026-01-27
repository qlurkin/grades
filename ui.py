from typing import Any, Callable
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, Grid, Container
from textual.widgets import Button, Footer, Header, DataTable, Label, Input, TextArea
from textual.widgets.data_table import RowKey, ColumnKey, CellType
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.message import Message
from document import Document


class SourceCellUpdate(Message):
    def __init__(self, row: str, column: str, value):
        self.row = row
        self.column = column
        self.value = value
        super().__init__()


class ComputedColumnUpdate(Message):
    def __init__(self, column: str, formula: str):
        self.column = column
        self.formula = formula
        super().__init__()


class StartEditFormula(Message):
    def __init__(self, column: str):
        self.column = column
        super().__init__()


class AddColumn(Message):
    def __init__(self, name: str, computed: bool):
        self.name = name
        self.computed = computed
        super().__init__()


class AddRow(Message):
    def __init__(self, index: str):
        self.index = index
        super().__init__()


class Sheet(DataTable):
    def on_data_table_cell_selected(self, event: DataTable.CellSelected):
        col_name = event.cell_key.column_key.value
        assert col_name is not None
        if isinstance(event.value, Text):
            self.post_message(StartEditFormula(col_name))
        else:
            type = str if self.app.doc.column_type(col_name) == "string" else float  # type: ignore
            value = "" if event.value is None else str(event.value)
            self.app.push_screen(
                CellInputScreen(
                    event.cell_key.row_key,
                    event.cell_key.column_key,
                    value,
                    type,
                )
            )


class FormScreen(ModalScreen):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, data: dict[str, Any], callback: Callable):
        super().__init__()
        self.data = data
        self.callback = callback

    def compose(self):
        self.inputs = {}
        widgets = []
        for k, v in self.data.items():
            widgets.append(Label(k.capitalize()))
            input = Input(v, placeholder=v)
            self.inputs[k] = input
            widgets.append(input)

        widgets.append(Button("Ok", variant="success", id="ok"))
        widgets.append(Button("Cancel", variant="primary", id="cancel"))

        yield Grid(*widgets)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.on_input_submitted()
        else:
            self.action_cancel()

    def on_input_submitted(self):
        result = {}
        for k, input in self.inputs.items():
            result[k] = input.value

        self.callback(result)
        self.app.pop_screen()

    def action_cancel(self):
        self.app.pop_screen()


class AddColumnScreen(ModalScreen):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, computed: bool):
        super().__init__()
        self.computed = computed

    def compose(self):
        yield Grid(
            Label("Column"),
            Input(),
            Button("Ok", variant="success", id="ok"),
            Button("Cancel", variant="primary", id="cancel"),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.on_input_submitted()
        else:
            self.action_cancel()

    def on_input_submitted(self):
        column = self.query_one(Input).value
        self.post_message(AddColumn(column, self.computed))
        self.app.pop_screen()

    def action_cancel(self):
        self.app.pop_screen()


class AddRowScreen(ModalScreen):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def compose(self):
        yield Grid(
            Label("Index"),
            Input(),
            Button("Ok", variant="success", id="ok"),
            Button("Cancel", variant="primary", id="cancel"),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.on_input_submitted()
        else:
            self.action_cancel()

    def on_input_submitted(self):
        index = self.query_one(Input).value
        self.post_message(AddRow(index))
        self.app.pop_screen()

    def action_cancel(self):
        self.app.pop_screen()


class FormulaInputScreen(ModalScreen):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("shift+enter", "submit", "Submit"),
    ]

    def __init__(self, column: str, formula: str):
        super().__init__()
        self.column = column
        self.formula = formula

    def compose(self) -> ComposeResult:
        yield Grid(
            TextArea.code_editor(self.formula, language="python"),
            Button("Ok", variant="success", id="ok"),
            Button("Cancel", variant="primary", id="cancel"),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.action_submit()
        else:
            self.action_cancel()

    def action_submit(self):
        formula = self.query_one(TextArea)
        self.post_message(ComputedColumnUpdate(self.column, formula.text))
        self.app.pop_screen()

    def action_cancel(self):
        self.app.pop_screen()


class CellInputScreen(ModalScreen):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        row: RowKey,
        column: ColumnKey,
        value: str,
        type: Callable,
        cursor: str = "replace",
    ):
        super().__init__()
        self.value = value
        self.row = row
        self.column = column
        self.type = type
        self.cursor = cursor

    def compose(self) -> ComposeResult:
        yield Grid(
            Container(),
            Label(f"{self.column.value}"),
            Label(f"{self.row.value}"),
            Input(self.value, placeholder=self.value),
            Button("Ok", variant="success", id="ok"),
            Button("Cancel", variant="primary", id="cancel"),
        )

    def on_mount(self):
        input = self.query_one(Input)
        if self.cursor == "start":
            input.cursor_position = 0
        if self.cursor == "end":
            input.cursor_position = len(input.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.on_input_submitted()
        else:
            self.action_cancel()

    def on_input_submitted(self):
        row = self.row.value
        column = self.column.value
        assert isinstance(row, str)
        assert isinstance(column, str)
        value = self.type(self.query_one(Input).value)
        self.post_message(SourceCellUpdate(row, column, value))
        self.app.pop_screen()

    def action_cancel(self):
        self.app.pop_screen()


class UI(App):
    TITLE = "Grades"
    CSS_PATH = "ui.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "add_computed_column", "Add Computed Column"),
        ("s", "add_source_column", "Add Source Column"),
        ("r", "add_row", "Add Row"),
        ("w", "save", "Write"),
        ("m", "metadata", "Metadata"),
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

    def on_source_cell_update(self, event: SourceCellUpdate):
        self.doc[event.row, event.column] = event.value
        coord = self.table.cursor_coordinate
        self.render_table()
        self.table.cursor_type = "cell"
        self.table.focus()
        self.table.cursor_coordinate = coord

    def on_start_edit_formula(self, event: StartEditFormula):
        formula = self.doc.formula(event.column)
        self.push_screen(FormulaInputScreen(event.column, formula))

    def on_computed_column_update(self, event: ComputedColumnUpdate):
        coord = self.table.cursor_coordinate
        self.doc.set_formula(event.column, event.formula)
        self.render_table()
        self.table.cursor_type = "cell"
        self.table.focus()
        self.table.cursor_coordinate = coord

    def on_add_column(self, event: AddColumn):
        coord = self.table.cursor_coordinate
        if event.computed:
            self.doc.add_computed_column(event.name, "0")
            self.push_screen(
                FormulaInputScreen(event.name, self.doc.formula(event.name))
            )
        else:
            self.doc.add_source_column(event.name, {})
            self.render_table()
            self.table.cursor_type = "cell"
            self.table.focus()
            self.table.cursor_coordinate = coord

    def on_add_row(self, event: AddRow):
        coord = self.table.cursor_coordinate
        self.doc.add_row(event.index)
        self.render_table()
        self.table.cursor_type = "cell"
        self.table.focus()
        self.table.cursor_coordinate = coord

    def render_table(self):
        self.title = f"{'⏺︎ ' if self.doc.dirty else ''}{doc.title} - {doc.code} - {doc.course} - {doc.date:%d-%m-%Y}"
        self.table.clear(columns=True)

        cols = self.doc.column_names

        for name in cols:
            label = name
            self.table.add_column(label, key=name)

        for index in self.doc.indexes:
            row = self.doc.index(index)
            values = []
            for key in cols:
                if self.doc.is_computed(key):
                    values.append(Text(str(row[key]), style="italic #03AC13"))
                else:
                    values.append(row[key])
            self.table.add_row(*values, label=index, key=index)

    def action_add_row(self):
        self.push_screen(AddRowScreen())

    def action_add_computed_column(self):
        self.push_screen(AddColumnScreen(True))

    def action_add_source_column(self):
        self.push_screen(AddColumnScreen(False))

    def action_save(self):
        coord = self.table.cursor_coordinate
        self.doc.save()
        self.render_table()
        self.table.cursor_type = "cell"
        self.table.focus()
        self.table.cursor_coordinate = coord

    def action_metadata(self):
        def cb(result):
            self.doc.title = result["title"]
            self.doc.code = result["code"]
            self.doc.course = result["course"]
            coord = self.table.cursor_coordinate
            self.render_table()
            self.table.cursor_type = "cell"
            self.table.focus()
            self.table.cursor_coordinate = coord

        data = {
            "title": self.doc.title,
            "code": self.doc.code,
            "course": self.doc.course,
        }

        self.push_screen(FormScreen(data, cb))


if __name__ == "__main__":
    doc = Document.from_file("test.json")
    UI(doc).run()
