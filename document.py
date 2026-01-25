from __future__ import annotations
from types import NoneType
from jsonschema import validate as check_schema
from numpy import float64, floor, ceil, abs, min, max, round
import math
from pandas import DataFrame, Series
import json
from datetime import datetime


class CyclicDependencyError(Exception):
    pass


with open("schema.json") as file:
    schema = json.load(file)


def clean_nan(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    return obj


def validate(data: dict):
    check_schema(instance=data, schema=schema)


def validate_column_name(name: str):
    if not name.isidentifier():
        raise ValueError("Columns name must be valid identifier")


class Document:
    def __init__(
        self,
        title: str,
        course: str,
        code: str,
        date: datetime,
        filename: str | None = None,
    ):
        self.__source = DataFrame()
        self.__computed = {}
        self.title = title
        self.code = code
        self.date = date
        self.course = course
        self.filename = filename

    @staticmethod
    def new() -> Document:
        return Document(title="Untitled", course="", code="", date=datetime.now())

    @staticmethod
    def from_file(path: str) -> Document:
        with open(path) as file:
            data = json.load(file)
        self = Document.from_dict(data)
        self.filename = path
        return self

    @staticmethod
    def from_dict(data: dict) -> Document:
        validate(data)
        self = Document(
            data["title"],
            data["course"],
            data["code"],
            datetime.fromisoformat(data["datetime"]),
        )
        for column in data["columns"]:
            if column["type"] == "source":
                self.add_source_column(column["name"], column["rows"])
            else:
                self.add_computed_column(column["name"], column["formula"])
        return self

    def add_source_column(self, name: str, column: dict):
        validate_column_name(name)
        if all(isinstance(index, str) for index in column):
            if all(
                isinstance(value, (float, int, NoneType)) for value in column.values()
            ):
                serie = Series(column, dtype=float64)
            elif all(isinstance(value, (str, NoneType)) for value in column.values()):
                serie = Series(column)
            else:
                raise ValueError("Values must be all the same type (number or string)")
            self.__source[name] = serie
        else:
            raise ValueError("Indexes must be str")

    def add_computed_column(self, name: str, formula: str):
        validate_column_name(name)
        self.__computed[name] = formula

    def add_row(self, index: str):
        if index in self.indexes:
            raise IndexError("Index already exist")

        values = {}
        for column in self.__source.columns:
            values[column] = None

        self.__source.loc[index] = values

    def set_formula(self, name: str, formula: str):
        if name not in self.__computed:
            raise IndexError(f"{name} is not a computed column")
        self.__computed[name] = formula

    def formula(self, name: str) -> str:
        if name not in self.__computed:
            raise IndexError(f"{name} is not a computed column")
        return self.__computed[name]

    @property
    def column_names(self):
        return list(self.__source.columns) + list(self.__computed)

    def __compute_column(self, df: DataFrame, name: str):
        ns: dict = {
            "__builtins__": {},
            "max": max,
            "min": min,
            "ceil": ceil,
            "floor": floor,
            "round": round,
            "abs": abs,
        }
        # ns = {}
        for col in df.columns:
            ns[col] = df[col]
        df[name] = eval(self.__computed[name], ns)

    def compute(self) -> DataFrame:
        df = self.__source.copy()
        to_compute = list(self.__computed.keys())
        max_iter = len(to_compute) ** 2
        count = 0
        while len(to_compute) > 0:
            if count > max_iter:
                raise CyclicDependencyError()
            name = to_compute.pop(0)
            try:
                self.__compute_column(df, name)
            except NameError as e:
                if e.name not in self.__computed:
                    raise e
                else:
                    to_compute.append(name)
            count += 1
        return df

    def column(self, column_name: str) -> dict:
        return self.compute()[column_name].to_dict()

    def is_computed(self, column) -> bool:
        return column in self.__computed

    def index(self, index: str) -> dict:
        return self.compute().loc[index].to_dict()

    @property
    def indexes(self):
        return self.__source.index.to_list()

    def column_type(self, name: str) -> str:
        if self.compute()[name].dtype == "float64":
            return "number"
        else:
            return "string"

    def save(self, path: str | None):
        if path is None:
            if self.filename is not None:
                path = self.filename
            else:
                raise ValueError("No filename")

        columns = []
        for name in self.__source.columns:
            # print(
            #     type(dict(self.column(name))["11111"]), dict(self.column(name))["11111"]
            # )
            columns.append(
                {
                    "type": "source",
                    "dtype": self.column_type(name),
                    "name": name,
                    "rows": clean_nan(dict(self.column(name))),
                }
            )

        for name in self.__computed:
            columns.append(
                {"type": "computed", "name": name, "formula": self.__computed[name]}
            )

        res = {
            "title": self.title,
            "course": self.course,
            "code": self.code,
            "datetime": self.date.isoformat(),
            "columns": columns,
        }
        with open(path, "w", encoding="utf8") as file:
            json.dump(res, file, indent=4)

    def __getitem__(self, coords: tuple[str, str]):
        return self.compute().loc[coords]

    def __setitem__(self, coords: tuple[str, str], value):
        _, column = coords
        if column in self.__source.columns:
            if self.__source[column].dtype == "float64" and not isinstance(
                value, (float, int)
            ):
                raise TypeError(f"`{value}` is incompatible with column type `number`")
            if self.__source[column].dtype == "object" and not isinstance(value, str):
                raise TypeError(f"`{value}` is incompatible with column type `string`")
            self.__source.loc[coords] = value
        else:
            validate_column_name(column)
            if column in self.__computed:
                raise IndexError("Cannot assign values to cells of a computed column")
            if not isinstance(value, (int, float, str)):
                raise TypeError("Document only support number and string columns")
            self.__source.loc[coords] = value

    def __str__(self):
        return str(self.compute())


def main():
    data = {
        "title": "Examen",
        "course": "Programmation",
        "code": "in2l",
        "datetime": "2025-10-23T15:45:12",
        "columns": [
            {
                "type": "source",
                "dtype": "number",
                "name": "lab1",
                "rows": {"lur": 10},
            },
            {"type": "computed", "name": "quad", "formula": "twice * 2"},
            {"type": "computed", "name": "twice", "formula": "lab1 * 2"},
        ],
    }
    doc = Document.from_dict(data)
    print(doc)
    print(doc.index("lur"))
    print(doc.column("twice"))
    print(doc["lur", "quad"])
    doc["lrg", "lab1"] = 15
    print(doc)
    doc2 = Document("Title", "Course", "code", datetime.now())
    doc2["11111", "math"] = -20
    doc2["22222", "math"] = 15
    doc2.add_computed_column("prout", "total * 2")
    doc2.add_computed_column("total", "abs(math)")
    doc2["11111", "name"] = "Quentin"
    doc2["22222", "info"] = 12.5
    print(doc2)
    doc2.save("test.json")
    doc3 = Document.from_file("test.json")
    print(doc3)
    doc3.add_computed_column("pipi", "info * 2")
    print(doc3)
    doc3.save("test2.json")
    print(doc3.index("11111"))


# TODO: on va utiliser textual pour le TUI
if __name__ == "__main__":
    main()
