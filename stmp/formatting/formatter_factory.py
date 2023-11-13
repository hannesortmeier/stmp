import json
from typing import List
from tabulate import tabulate
from abc import ABC, abstractmethod


class stmpFormatter(ABC):
    @abstractmethod
    def format(self, work_hours: List[dict]) -> str:
        pass


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


class JSONFormatter(stmpFormatter):
    """
    The JSONFormatter class implements the Formatter interface to provide JSON formatting.

    Methods:
        format(work_hours: List[dict]) -> str:
            Formats the provided work hours and notes as a JSON string.
    """

    def format(self, work_hours: List[dict]) -> str:
        return json.dumps(work_hours, indent=4)


class MARKDOWNFormatter(stmpFormatter):
    """
    The MARKDOWNFormatter class implements the Formatter interface to provide Markdown formatting.

    Methods:
        format(work_hours: List[dict]) -> str:
            Formats the provided work hours and notes as a Markdown string.
    """

    def format(self, work_hours: List[dict]) -> str:
        md = ""
        for record in work_hours:
            md += (
                "## "
                + record["date"]
                + " | "
                + record["start_time"]
                + " - "
                + record["end_time"]
                + "\n\n"
            )
            for note in record["notes"]:
                md += "- " + note["note"] + "\n"
            md += "\n\n"
        return md


class TABLEFormatter(stmpFormatter):
    """
    The TABLEFormatter class implements the Formatter interface to provide table formatting.

    Methods:
        format(work_hours: List[dict]) -> str:
            Formats the provided work hours and notes as a table.
    """

    def format(self, work_hours: List[dict]) -> str:
        table = []
        for record in work_hours:
            copy = record.copy()
            copy.pop("notes")
            if not record["notes"]:
                copy["note_id"] = None
                copy["note"] = None
                table.append(copy)
            else:
                for note in record["notes"]:
                    copy["note_id"] = note["id"]
                    copy["note"] = note["note"]
                    table.append(copy.copy())
        return tabulate(table, headers="keys", tablefmt="github")
