import argparse
import os
from typing import Generator, List, Optional
from sqlite_utils import Database
from sqlite_utils.db import NotFoundError, Table, View
from datetime import datetime

from stmp.formatting.formatter_factory import FormatterFactory

WORK_HOURS_TABLE_NAME = "work_hours"
NOTES_TABLE_NAME = "notes"


class Stmp:
    """
    The stmp class handles the creation and management of work_hours and notes tables in a SQLite database.

    Attributes:
        db (Database): The SQLite database to operate on.
        args (argparse.Namespace): The command-line arguments passed to the script.
    """

    def __init__(self, db: Database, args: argparse.Namespace):
        self.args = args

        # Initialize the database
        self.db = db

        # Create the work_hours table if it doesn"t exist
        if not self.db.table(WORK_HOURS_TABLE_NAME).exists():
            self.db.create_table(
                WORK_HOURS_TABLE_NAME,
                {
                    "date": str,
                    "start_time": int,
                    "end_time": int,
                    "break_duration": float,
                },
                pk="date",
            )

        # Create the notes table if it doesn"t exist
        if not self.db.table(NOTES_TABLE_NAME).exists():
            self.db.create_table(
                NOTES_TABLE_NAME, {"id": int, "date": str, "note": str}, pk="id"
            )

    def check_add_parser_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Checks the arguments passed to the "add" command.

        This method checks if at least one of the arguments --start_time, --end_time, --break_duration, or --note is set
        when the --date argument is set. If --date is not set, it checks if at least one of these arguments is set
        regardless of the --overwrite argument. If these conditions are not met, it raises an error.

        Args:
            parser (argparse.ArgumentParser): The argument parser object.

        Raises:
            argparse.ArgumentError: If the arguments do not meet the required conditions.
        """
        if self.args.date is not None:
            if all(
                arg is None
                for arg in [
                    self.args.start_time,
                    self.args.end_time,
                    self.args.break_duration,
                    self.args.note,
                ]
            ):
                parser.error(
                    "If --date is set, at least one argument of --start_time, --end_time, --break_duration or --note needs to be set."
                )
        elif all(
            arg is None
            for arg in [
                self.args.start_time,
                self.args.end_time,
                self.args.break_duration,
                self.args.note,
            ]
        ):
            parser.print_help()
            parser.error(
                "At least one argument other than --overwrite needs to be set."
            )

    def check_rm_parser_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Checks the arguments passed to the "rm" command.

        This method checks if at least one of the arguments --id or --date but not both are set.
        If these conditions are not met, it raises an error.

        Args:
            parser (argparse.ArgumentParser): The argument parser object.

        Raises:
            argparse.ArgumentError: If the arguments do not meet the required conditions.
        """
        if self.args.id is None and self.args.date is None:
            parser.print_help()
            parser.error("At least one argument of --id or --date needs to be set.")

        if self.args.id is not None and self.args.date is not None:
            parser.error("Arguments --id or --date cannot both be set.")

    def check_dump_parser_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Checks the arguments passed to the "dump" command.

        This method checks if the argument --destination is set.
        Raises an error, if this condition is not met.

        Args:
            parser (argparse.ArgumentParser): The argument parser object.

        Raises:
            argparse.ArgumentError: If the arguments do not meet the required conditions.
        """
        if self.args.destination is None:
            parser.print_help()
            parser.error("Argument --destination needs to be set.")

    def set_default_date(self) -> None:
        """
        Sets the default date to the current date if no date is provided.

        This method checks if the --date argument is set. If not, it sets the date to the current date.
        """
        if self.args.date is None:
            self.args.date = datetime.now().strftime("%Y-%m-%d")

    def update_work_hours(self) -> None:
        """
        Updates the work hours in the database.

        This method checks if a record for the specified date already exists in the database. If it does, it calls
        the overwrite_work_hours method to update the record. If it doesn"t, it calls the insert_work_hours method
        to insert a new record.
        """
        table: (Table | View) = self.db.table(WORK_HOURS_TABLE_NAME)
        assert isinstance(table, Table)
        row = self.getRow(table)

        if row is None:
            self.insert_work_hours(
                self.args.date,
                self.args.start_time,
                self.args.end_time,
                self.args.break_duration,
                table,
            )
        else:
            if self.args.overwrite:
                self.overwrite_upsert_work_hours(
                    self.args.date,
                    self.args.start_time,
                    self.args.end_time,
                    self.args.break_duration,
                    table,
                    row,
                )
            else:
                self.no_overwrite_upsert_work_hours(
                    self.args.date,
                    self.args.start_time,
                    self.args.end_time,
                    self.args.break_duration,
                    table,
                    row,
                )

    def getRow(self, table: Table) -> Optional[dict]:
        """
        Gets the row for the args date from the database.
        """
        try:
            row: Optional[dict] = table.get(self.args.date)
        except NotFoundError:
            row = None
        return row

    def insert_work_hours(
        self,
        date: str,
        start_time: Optional[str],
        end_time: Optional[str],
        break_duration: Optional[int],
        table: Table,
    ) -> None:
        """
        Inserts a new record of work hours into the database.

        This method inserts a new record into the work_hours table in the database with the specified date, start time,
        end time, and break duration. If no start time, end time, or break duration is specified, it uses default values.
        """
        table.insert(
            {
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "break_duration": break_duration,
            }
        )

    def overwrite_upsert_work_hours(
        self,
        date: str,
        start_time: Optional[str],
        end_time: Optional[str],
        break_duration: Optional[int],
        table: Table,
        row: dict,
    ) -> None:
        """
        Overwrites an existing record of work hours in the database.

        This method updates the record in the work_hours table in the database with the specified date. It updates the
        start time, end time, and break duration with the specified values. If no start time, end time, or break duration
        is specified, it leaves the existing values unchanged.
        """
        start_time = start_time if start_time is not None else row["start_time"]
        end_time = end_time if end_time is not None else row["end_time"]
        break_duration = (
            break_duration if break_duration is not None else row["break_duration"]
        )
        table.upsert(
            {
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "break_duration": break_duration,
            },
            pk="date",  # type: ignore
        )

    def no_overwrite_upsert_work_hours(
        self,
        date: str,
        start_time: Optional[str],
        end_time: Optional[str],
        break_duration: Optional[int],
        table: Table,
        row: dict,
    ) -> None:
        """
        Upserts work hours in the database without overwriting existing values.

        Args:
            date (str): The date for the work hours.
            start_time (str): The start time for the work hours.
            end_time (str): The end time for the work hours.
            break_duration (int): The break duration for the work hours.
            table (Table): The database table to upsert into.
            row (dict): The existing row in the database.
        """
        start_time = start_time if row["start_time"] is None else row["start_time"]
        end_time = end_time if row["end_time"] is None else row["end_time"]
        break_duration = (
            break_duration if row["break_duration"] is None else row["break_duration"]
        )
        table.upsert(
            {
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "break_duration": break_duration,
            },
            pk="date",  # type: ignore
        )

    def update_notes(self) -> None:
        """
        Inserts a note into the database.

        This method inserts a new note into the notes table in the database with the specified date and note.
        If there is no entry in the work_hours table for the specified date, it inserts a new entry with empty values.
        """
        # Insert an empty entry into the work_hours table if it doesn't exist
        work_hours_table: (Table | View) = self.db.table(WORK_HOURS_TABLE_NAME)
        assert isinstance(work_hours_table, Table)

        try:
            work_hours_table.get(self.args.date)
        except NotFoundError:
            self.insert_work_hours(
                self.args.date,
                None,
                None,
                None,
                work_hours_table,
            )

        notes_table: (Table | View) = self.db.table(NOTES_TABLE_NAME)
        assert isinstance(notes_table, Table)

        # Insert notes into the database
        notes_table.insert({"date": self.args.date, "note": self.args.note})

    def remove_note(self) -> None:
        """
        Removes a note from the database.

        This method removes the note with the specified ID from the notes table in the database.
        """
        table: (Table | View) = self.db.table(NOTES_TABLE_NAME)
        assert isinstance(table, Table)

        # Remove note from the database
        table.delete(self.args.id)

    def remove_work_hours(self) -> None:
        """
        Removes a work hours record from the database.

        This method removes the record with the specified date from the work_hours table in the database.
        """
        table: (Table | View) = self.db.table(WORK_HOURS_TABLE_NAME)
        assert isinstance(table, Table)

        # Remove note from the database
        table.delete(self.args.date)

    def show_data(self) -> None:
        """
        Retrieves and prints data from the database.

        This method retrieves data from the database and prints it to the console.
        """
        work_hours_table: (Table | View) = self.db.table(WORK_HOURS_TABLE_NAME)
        notes_table: (Table | View) = self.db.table(NOTES_TABLE_NAME)
        assert isinstance(work_hours_table, Table)
        assert isinstance(notes_table, Table)

        work_hours: dict = work_hours_table.get(self.args.date)
        notes_gen: Generator[dict, None, None] = notes_table.rows_where(
            "date = ?", [self.args.date]
        )
        notes: List[dict] = []
        for note in notes_gen:
            notes.append(note)
        work_hours["notes"] = notes
        formatter = FormatterFactory(self.args.format).getFormatter()
        print(formatter.format(work_hours))

    def dump_data(self) -> None:
        """
        Retrieves and dumps all data from the database.

        This method retrieves all data from the database and dumps it to a file per table.
        """
        work_hours_table: (Table | View) = self.db.table(WORK_HOURS_TABLE_NAME)
        notes_table: (Table | View) = self.db.table(NOTES_TABLE_NAME)
        assert isinstance(work_hours_table, Table)
        assert isinstance(notes_table, Table)

        self.dump_to_file(notes_table, NOTES_TABLE_NAME)

        self.dump_to_file(work_hours_table, WORK_HOURS_TABLE_NAME)

    def dump_to_file(self, table: Table, filename: str) -> None:
        """
        Dumps the contents of a table to a file.

        Args:
            table (Table): The table to dump.
            filename (str): The name of the file to dump the table to.
        """
        with open(os.path.join(self.args.destination, filename + ".dump"), "w") as file:
            columns = [column.name for column in table.columns]
            file.write(", ".join(columns) + "\n")
            for row in table.rows:
                values: list[str] = list(
                    map(
                        lambda x: str(x)
                        if isinstance(x, int) or isinstance(x, float) or x is None
                        else x,
                        row.values(),
                    )
                )
                file.write(", ".join(values) + "\n")

    def check_data(self) -> None:
        """
        Checks the database entries for completeness.

        This method checks if all records in the work_hours table do have all values set.
        """
        table: (Table | View) = self.db.table(WORK_HOURS_TABLE_NAME)
        assert isinstance(table, Table)
        for row in table.rows:
            if row["start_time"] is None:
                print(f"Missing start_time for {row['date']}")
            if row["end_time"] is None:
                print(f"Missing end_time for {row['date']}")
            if row["break_duration"] is None:
                print(f"Missing break_duration for {row['date']}")

    def execute(self, parser: argparse.ArgumentParser) -> None:
        """
        Executes the appropriate command based on the command-line arguments.

        Args:
            parser (argparse.ArgumentParser): The argument parser object to write check errors to.
        """
        if self.args.command is None:
            parser.print_help()
        if self.args.command == "add":
            self.check_add_parser_arguments(parser)
            self.set_default_date()
            self.update_work_hours()
            if self.args.note is not None:
                self.update_notes()
        elif self.args.command == "rm":
            self.check_rm_parser_arguments(parser)
            if self.args.id:
                self.remove_note()
            elif self.args.date:
                self.remove_work_hours()
        elif self.args.command == "show":
            self.set_default_date()
            self.show_data()
        elif self.args.command == "dump":
            self.dump_data()
        elif self.args.command == "check":
            self.check_data()

def create_dir_if_not_exists() -> str:
        """
        Creates the .stmp directory in the home directory if it doesn't exist.
        
        Returns the path to the .stmp directory.
        """
        stmp_dir = os.path.join(os.path.expanduser("~"), ".stmp")
        os.makedirs(stmp_dir, exist_ok=True)
        return stmp_dir

def main():
     # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Record working hours.",
        epilog="""
This tool allows you to record your working hours and breaks, and manage notes.

To add a record:
    stmp add -d <date> -s <start_time> -e <end_time> -b <break_duration> -n <note> -o <overwrite>
    -d, --date: Date in YYYY-MM-DD format. If not specified, the current date is used.
    -s, --start_time: Start time in HH:MM format. If not specified, the existing value is used.
    -e, --end_time: End time in HH:MM format. If not specified, the existing value is used.
    -b, --break_duration: Break duration in minutes. If not specified, the existing value is used.
    -n, --note: Add a note for the day. If not specified, no note is added.
    -o, --overwrite: Boolean to indicate whether to overwrite existing data. Default is True.

To remove a record:
    stmp rm -i <id> -d <date>
    -i, --id: ID of the note to remove.
    -d, --date: Date of the record to remove.

To show records for a date:
    stmp show -d <date> -f <format>
    -d, --date: Date for which to show records. If not specified, records for the current date are shown.
    -f, --format: Format to show records. Default is "table".
    
To dump all data:
    stmp dump -d <destination>
    -d, --destination: Destination folder for the dumped data.

To check the database entries for completeness:
    stmp check
""",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command")

    # add parser
    add_parser = subparsers.add_parser("add", help="Add times and notes for the day")
    add_parser.add_argument("--date", "-d", type=str, help="Date in YYYY-MM-DD format")
    add_parser.add_argument(
        "--start_time", "-s", type=str, help="Start time in HH:MM format"
    )
    add_parser.add_argument(
        "--end_time", "-e", type=str, help="End time in HH:MM format"
    )
    add_parser.add_argument(
        "--break_duration", "-b", type=int, help="Break duration in minutes"
    )
    add_parser.add_argument("--note", "-n", type=str, help="Add a note for the day")
    add_parser.add_argument(
        "--overwrite",
        "-o",
        type=bool,
        help="Boolean to indicate whether to overwrite existing data",
        default=True,
    )

    # rm parser
    rm_parser = subparsers.add_parser("rm", help="Remove a record")
    rm_parser.add_argument("--id", "-i", type=int, help="ID of the note to remove")
    rm_parser.add_argument(
        "--date", "-d", type=str, help="Date of the record to remove"
    )

    # show parser
    show_parser = subparsers.add_parser("show", help="Show hours and notes")
    show_parser.add_argument(
        "--date", "-d", type=str, help="Date for which to show records"
    )
    show_parser.add_argument(
        "--format", "-f", type=str, help="Format to show", default="table"
    )

    # dump parser
    dump_parser = subparsers.add_parser("dump", help="Dump the database")
    dump_parser.add_argument("--destination", "-d", type=str, help="Destination folder")

    # check parser
    check_parser = subparsers.add_parser(
        "check", help="Check the database entries for completeness"
    )

    args = parser.parse_args()
    

    # Initialize and execute stmp
    stmp_dir = create_dir_if_not_exists()
    db = Database(os.path.join(stmp_dir, "stmp.db"))
    try:
        self = Stmp(db, args)
        self.execute(parser)
    except Exception as e:
        raise e
    finally:
        db.close()

if __name__ == "__main__":  
    main()