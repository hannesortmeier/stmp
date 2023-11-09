import json
from tabulate import tabulate
from abc import ABC, abstractmethod


class FormatterFactory:
    """
    The FormatterFactory class is responsible for creating the appropriate formatter based on the provided format.

    Attributes:
        formatter (Formatter): The formatter object created by the factory.

    Methods:
        getFormatter() -> Formatter:
            Returns the formatter object created by the factory.
    """

    def __init__(self, format):
        if "json" in format.lower():
            self.formatter = JSONFormatter()
        elif "table" in format.lower():
            self.formatter = TABLEFormatter()
        elif "markdown" in format.lower():
            self.formatter = MARKDOWNFormatter()
        else:
            raise Exception("Format not supported: " + format)

    def getFormatter(self):
        return self.formatter
    


class stmpFormatter(ABC):
    @abstractmethod
    def format(self, work_hours: dict) -> str:
        pass



class JSONFormatter(stmpFormatter):
    """
    The JSONFormatter class implements the Formatter interface to provide JSON formatting.

    Methods:
        format(work_hours: dict, notes: List[dict]) -> str:
            Formats the provided work hours and notes as a JSON string.
    """

    def format(self, work_hours: dict) -> str:
        return json.dumps(work_hours, indent=4)


class MARKDOWNFormatter(stmpFormatter):
    """
    The MARKDOWNFormatter class implements the Formatter interface to provide Markdown formatting.

    Methods:
        format(work_hours: dict, notes: List[dict]) -> str:
            Formats the provided work hours and notes as a Markdown string.
    """

    def format(self, work_hours: dict) -> str:
        md: str = "## " + work_hours["date"] + "\n\n"
        for note in work_hours["notes"]:
            md += "\t- " + note["note"] + "\n"
        return md

class TABLEFormatter(stmpFormatter):
    """
    The TABLEFormatter class implements the Formatter interface to provide table formatting.

    Methods:
        format(work_hours: dict, notes: List[dict]) -> str:
            Formats the provided work hours and notes as a table.
    """

    def format(self, work_hours: dict) -> str:
        copy = work_hours.copy()
        copy.pop("notes")
        table = []
        if not work_hours["notes"]:
            copy["note_id"] = None
            copy["note"] = None
            return tabulate([copy], headers="keys", tablefmt="github")
        for note in work_hours["notes"]:
            copy["note_id"] = note["id"]
            copy["note"] = note["note"]
            table.append(copy.copy())
        return tabulate(table, headers="keys", tablefmt="github")
