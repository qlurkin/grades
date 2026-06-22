import pandas as pd
from pathlib import Path


def read_csv(path: Path | str, delimiter=";", index_col="matricule", decimal=","):
    path = Path(path)
    return pd.read_csv(
        path,
        delimiter=delimiter,
        index_col=index_col,
        decimal=decimal,
        dtype={index_col: str},
    )


def save_csv(df: pd.DataFrame, path: Path | str, delimiter=";", decimal=","):
    path = Path(path)
    df.to_csv(path, sep=delimiter, decimal=decimal)


def concat(*args):
    return pd.concat(args, axis=1)


def serve(df: pd.DataFrame):
    cmd = ""
    try:
        while cmd != "/exit":
            if cmd == "":
                print(df)
            elif not cmd.startswith("/"):
                matricule = cmd
                try:
                    print(df.loc[matricule])
                except KeyError:
                    print(f"`{matricule}` not present")
            else:
                if cmd == "/save":
                    filename = input("filename: ")
                    if not filename.endswith(".csv"):
                        filename += ".csv"
                    save_csv(df, filename)
                else:
                    print(f"Unknown command: {cmd}")
            cmd = input("\n> ")
    except KeyboardInterrupt:
        pass
    print("\nBye")


def to_half(df: pd.DataFrame, column: str):
    df[column] = (2 * df[column]).round() / 2


def to_tenth(df: pd.DataFrame, column: str):
    df[column] = df[column].round(1)
