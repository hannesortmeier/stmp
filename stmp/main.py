import os
import argparse
from sqlite_utils import Database
from datetime import datetime

from .stmp import Stmp


def _check_datetime_format(_input: str, _format: str, length: int) -> bool:
    """
    Checks whether the provided input string is in the provided format and has the provided length.

    Returns True if the format is correct, False otherwise.
    """
    try:
        datetime.strptime(_input, _format)
    except ValueError:
        return False
    return len(_input) == length


def _check_argparse_input(_input: str, _format: str, length: int) -> str:
    if _check_datetime_format(_input, _format, length):
        return _input
    else:
        raise argparse.ArgumentTypeError(
            f"Value {_input} not valid. Please use format {_format}."
        )


def create_dir_if_not_exists() -> str:
    """
    Creates the .stmp directory in the home directory if it doesn't exist.

    Returns the path to the .stmp directory.
    """
    stmp_dir = os.path.join(os.path.expanduser("~"), ".stmp")
    os.makedirs(stmp_dir, exist_ok=True)
    return stmp_dir


def main():
    now = datetime.now()
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Record working hours.",
        epilog="""
This tool allows you to record your working hours and breaks, and manage notes.

To add a record:
    stmp add -d <date> -s <start_time> -e <end_time> -b <break_duration> -n <note> -o <overwrite>
    -d, --date: Date in YYYY-MM-DD format. If not specified, the current date is used.
    -s, --start_time: Start time in HH:MM format. If option is set but no value is given, the current time is used.
    -e, --end_time: End time in HH:MM format. If option is set but no value is given, the current time is used.
    -b, --break_duration: Break duration in minutes. If not specified, the existing value is used.
    -n, --note: Add a note for the day. If not specified, no note is added.
    -o, --overwrite: Boolean to indicate whether to overwrite existing data. Default is True.

To remove a record:
    stmp rm -i <id> -d <date>
    -i, --id: ID of the note to remove.
    -d, --date: Date of the record to remove.

To show records for a date, month, year, or all records. Shows records of current month as default:
    stmp show -d <date> -m <month> -y <year> -a
    -d, --date: Date in YYYY-MM-DD format for which to show records.
    -m, --month: Month in MM format for which to show records.
    -y, --year: Year in YYYY format for which to show records.
    -a, --all: Show all records.
    -n, --notes: Show notes in the output.
    -f, --format: Format to show. Default format is table.

To dump all data:
    stmp dump -d <destination>
    -d, --destination: Destination folder for the dumped data.

To check the database entries for completeness:
    stmp check
    
To configure stmp or list configuration key value pairs:
    stmp config set -k <key> -v <value>
    stmp config list -k <key>
    stmp config rm -k <key>
    -k, --key: Key
    -v, --value: Value
""",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command")

    # add parser
    add_parser = subparsers.add_parser("add", help="Add times and notes for the day")
    add_parser.add_argument(
        "--date",
        "-d",
        type=lambda x: _check_argparse_input(x, "%Y-%m-%d", 10),
        default=now.strftime("%Y-%m-%d"),
        help="Date in YYYY-MM-DD format",
    )
    add_parser.add_argument(
        "--start_time",
        "-s",
        type=lambda x: _check_argparse_input(x, "%H:%M", 5),
        nargs="?",
        const=now.strftime("%H:%M"),
        help="Start time in HH:MM format",
    )
    add_parser.add_argument(
        "--end_time",
        "-e",
        type=lambda x: _check_argparse_input(x, "%H:%M", 5),
        nargs="?",
        const=now.strftime("%H:%M"),
        help="End time in HH:MM format",
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
    rm_either = rm_parser.add_mutually_exclusive_group()
    rm_either.add_argument("--id", "-i", type=int, help="ID of the note to remove")
    rm_either.add_argument(
        "--date", "-d", type=lambda x: _check_argparse_input(x, "%Y-%m-%d", 10), help="Date of the record to remove"
    )

    # show parser
    show_parser = subparsers.add_parser("show", help="Show hours and notes")
    show_parser.add_argument(
        "--date",
        "-d",
        type=lambda x: _check_argparse_input(x, "%Y-%m-%d", 10),
        nargs="?",
        const=now.strftime("%Y-%m-%d"),
        help="Date in YYYY-MM-DD format for which to show records",
    )
    show_parser.add_argument(
        "--month",
        "-m",
        type=lambda x: _check_argparse_input(x, "%m", 2),
        nargs="?",
        const=now.strftime("%m"),
        help="Month in MM format for which to show records",
    )
    show_parser.add_argument(
        "--year",
        "-y",
        type=lambda x: _check_argparse_input(x, "%Y", 4),
        nargs="?",
        const=now.strftime("%Y"),
        help="Year in YYYY format for which to show records",
    )
    show_parser.add_argument(
        "--all", "-a", type=bool, nargs="?", const=True, help="Show all records"
    )
    show_parser.add_argument(
        "--notes",
        "-n",
        type=bool,
        nargs="?",
        const=True,
        help="Show notes in the output",
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

    # config parser
    config_parser = subparsers.add_parser(
        "config", help="Configure stmp"
    )
    subsubparser = config_parser.add_subparsers(dest="subcommand")
    set_config_parser = subsubparser.add_parser(
        "set", help="Set a configuration key value pair"
    )
    set_config_parser.add_argument("--key", "-k", type=str, help="Key", required=True)
    set_config_parser.add_argument("--value", "-v", type=str, help="Value", required=True)
    list_config_parser = subsubparser.add_parser(
        "list", help="List configuration key value pairs"
    )
    list_config_parser.add_argument("--key", "-k", type=str, help="Key", required=False)
    rm_config_parser = subsubparser.add_parser(
        "rm", help="Remove a configuration key value pair"
    )
    rm_config_parser.add_argument("--key", "-k", type=str, help="Key", required=True)

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
