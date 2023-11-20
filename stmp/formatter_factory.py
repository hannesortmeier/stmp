import json
from typing import List
from tabulate import tabulate
from abc import ABC, abstractmethod


class StmpFormatter(ABC):
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

    formatter: StmpFormatter

    def __init__(self, format_string) -> None:
        if "json" in format_string.lower():
            self.formatter = JSONFormatter()
        elif "table" in format_string.lower():
            self.formatter = TABLEFormatter()
        elif "markdown" in format_string.lower():
            self.formatter = MARKDOWNFormatter()
        else:
            raise Exception("Format not supported: " + format_string)

    def get_formatter(self) -> StmpFormatter:
        return self.formatter


class JSONFormatter(StmpFormatter):
    """
    The JSONFormatter class implements the Formatter interface to provide JSON formatting.

    Methods:
        format(work_hours: List[dict]) -> str:
            Formats the provided work hours and notes as a JSON string.
    """

    def format(self, work_hours: List[dict]) -> str:
        return json.dumps(work_hours, indent=4)


class MARKDOWNFormatter(StmpFormatter):
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
            if "notes" in record.keys():
                for note in record["notes"]:
                    md += "- " + note["note"] + "\n"
                md += "\n\n"
        return md


class TABLEFormatter(StmpFormatter):
    """
    The TABLEFormatter class implements the Formatter interface to provide table formatting.

    Methods:
        format(work_hours: List[dict]) -> str:
            Formats the provided work hours and notes as a table.
    """

    def format(self, work_hours: List[dict]) -> str:
        table = []
        # Check if the entries of work_hours contain notes.
        for record in work_hours:
            copy = record.copy()
            # Include notes in the table if they exist.
            if "notes" in work_hours[0].keys():
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
            # Otherwise, just include the work hours.
            else:
                table.append(copy)
        return tabulate(table, headers="keys", tablefmt="github")
