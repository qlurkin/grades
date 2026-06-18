from .document import Document
from .ui import UI
from datetime import datetime

if __name__ == "__main__":
    doc = Document(
        title="No Title", course="No Course", code="xxxxxx", date=datetime.now()
    )
    UI(doc).run()
