from __future__ import annotations
from typing import Callable
from jsonschema import validate as check_schema
from pandas import DataFrame, Series
import json
import inspect


schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "course": {"type": "string"},
        "datetime": {"type": "string"},
        "columns": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["source", "computed"]},
                },
                "required": ["name", "type"],
                "if": {"properties": {"type": {"const": "source"}}},
                "then": {
                    "properties": {
                        "rows": {
                            "type": "object",
                        },
                        "dtype": {"enum": ["number", "string"]},
                    },
                    "required": ["rows", "dtype"],
                    "if": {"properties": {"dtype": {"const": "number"}}},
                    "then": {
                        "properties": {
                            "rows": {
                                "patternProperties": {"^.+$": {"type": "number"}},
                            }
                        }
                    },
                    "else": {
                        "properties": {
                            "rows": {
                                "patternProperties": {"^.+$": {"type": "string"}},
                            }
                        }
                    },
                },
                "else": {
                    "properties": {"formula": {"type": "string"}},
                    "required": ["formula"],
                },
            },
        },
    },
    "required": ["title", "course", "datetime", "columns"],
}


def validate(data: dict):
    check_schema(instance=data, schema=schema)


class Document:
    def __init__(self):
        self.__source = DataFrame()
        self.__computed = {}

    @staticmethod
    def from_file(path: str) -> Document:
        with open(path) as file:
            data = json.load(file)
        return Document.from_dict(data)

    @staticmethod
    def from_dict(data: dict) -> Document:
        validate(data)
        self = Document()
        for column in data["columns"]:
            if column["type"] == "source":
                self.add_source_column(column["name"], column["rows"])
            else:
                self.add_computed_column(column["name"], column["formula"])
        return self

    def add_source_column(self, name: str, column: dict):
        if all(isinstance(index, str) for index in column):
            serie = Series(column)
            self.__source[name] = serie
        else:
            raise ValueError("Indexes must be str")

    def add_computed_column(self, name: str, formula: str):
        self.__computed[name] = formula

    def __compute_column(self, df: DataFrame, name: str):
        ns = {}
        for col in df.columns:
            ns[col] = df[col]
        df[name] = eval(self.__computed[name], ns)

    def compute(self) -> DataFrame:
        df = self.__source.copy()
        to_compute = list(self.__computed.keys())
        # TODO: do something about cycle
        while len(to_compute) > 0:
            name = to_compute.pop(0)
            try:
                self.__compute_column(df, name)
            except NameError as e:
                if e.name not in self.__computed:
                    raise e
                else:
                    to_compute.append(name)
        return df

    def column(self, column_name: str) -> dict:
        return self.compute()[column_name].to_dict()

    def index(self, index: str) -> dict:
        return self.compute().loc[index].to_dict()

    def __getitem__(self, coords: tuple[str, str]):
        return self.compute().loc[coords]

    def __setitem__(self, coords: tuple[str, str], value):
        self.__source.loc[coords] = value

    def __str__(self):
        return str(self.compute())


def main():
    data = {
        "title": "Examen",
        "course": "in2l",
        "datetime": "",
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


if __name__ == "__main__":
    main()
