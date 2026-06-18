from .document import Document
from .ui import UI
import argparse
from pathlib import Path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="grades",
        description="A Simple Command Line Tabler Specialized in Students Grades Management",
    )

    parser.add_argument(
        "filename",
        help="The file to open or to create",
        nargs="?",
    )

    args = parser.parse_args()

    if args.filename is None:
        doc = Document.new()
    else:
        path = Path(args.filename)
        if path.exists():
            doc = Document.from_file(str(path))
        else:
            doc = Document.new()
            doc.filename = str(path)

    UI(doc).run()
