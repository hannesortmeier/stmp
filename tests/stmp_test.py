import argparse
import unittest
import os
from sqlite3 import Cursor
from sqlite_utils import Database
from io import StringIO
from unittest.mock import ANY, patch, mock_open

from stmp.stmp import Stmp


class TestStmp(unittest.TestCase):
    maxDiff = None

    @classmethod
    def tearDownClass(cls):
        # Specify the database file path
        db_file_paths = ["test2.db", "test3.db", "test4.db", "test5.db"]

        # Remove the database file
        for db_file_path in db_file_paths:
            if os.path.exists(db_file_path):
                os.remove(db_file_path)
            else:
                print(f"The file {db_file_path} does not exist")

    def test_add_parser(self):
        args = argparse.Namespace(
            command="add",
            date="2020-01-01",
            start_time="08:00",
            end_time="16:00",
            break_duration=30,
            note="Test note",
            overwrite=True,
        )
        stmp = Stmp(Database("test2.db"), args)

        # test update_notes
        stmp.update_notes()
        cursor: Cursor = stmp.db.execute(
            "SELECT * FROM notes WHERE date = '2020-01-01'"
        )
        id, date, note = cursor.fetchone()
        self.assertEqual(date, "2020-01-01")
        self.assertEqual(note, "Test note")

        # test insert_work_hours
        stmp.update_work_hours()
        cursor: Cursor = stmp.db.execute(
            "SELECT * FROM work_hours WHERE date = '2020-01-01'"
        )
        date, start_time, end_time, break_duration = cursor.fetchone()
        self.assertEqual(date, "2020-01-01")
        self.assertEqual(start_time, "08:00")
        self.assertEqual(end_time, "16:00")
        self.assertEqual(break_duration, 30)

        # test overwrite_upsert_work_hours
        args = argparse.Namespace(
            command="add",
            date="2020-01-01",
            start_time="07:00",
            end_time="16:00",
            break_duration=30,
            note="Test note",
            overwrite=True,
        )
        stmp.args = args
        stmp.update_work_hours()
        cursor: Cursor = stmp.db.execute(
            "SELECT start_time FROM work_hours WHERE date = '2020-01-01'"
        )
        self.assertEqual(cursor.fetchone()[0], "07:00")

        # test no_overwrite_upsert_work_hours
        args = argparse.Namespace(
            command="add",
            date="2020-01-01",
            start_time="12:00",
            end_time=None,
            break_duration=None,
            note=None,
            overwrite=False,
        )
        stmp.args = args
        stmp.update_work_hours()
        cursor: Cursor = stmp.db.execute(
            "SELECT start_time FROM work_hours WHERE date = '2020-01-01'"
        )
        self.assertEqual(cursor.fetchone()[0], "07:00")

    def test_remove_note(self):
        args = argparse.Namespace(
            command="add", date="2020-02-01", note="Test note", overwrite=True
        )
        stmp = Stmp(Database("test3.db"), args)

        # add note
        stmp.update_notes()
        cursor: Cursor = stmp.db.execute(
            "SELECT * FROM notes WHERE date = '2020-02-01'"
        )
        id, date, note = cursor.fetchone()
        self.assertEqual(date, "2020-02-01")
        self.assertEqual(note, "Test note")

        # test remove_note
        args = argparse.Namespace(command="rm", id=id)
        stmp.args = args
        stmp.remove_note()

        cursor: Cursor = stmp.db.execute(  # type: ignore
            "SELECT * FROM notes WHERE date = '2020-02-01'"
        )
        self.assertIsNone(cursor.fetchone())

    def test_remove_work_hours(self):
        args = argparse.Namespace(
            command="add",
            date="2020-02-01",
            start_time="08:00",
            end_time="16:00",
            break_duration=30,
            note="Test note",
            overwrite=True,
        )
        stmp = Stmp(Database("test3.db"), args)

        # add work hours
        stmp.update_work_hours()
        cursor: Cursor = stmp.db.execute(  # type: ignore
            "SELECT * FROM work_hours WHERE date = '2020-02-01'"
        )
        date, start_time, end_time, break_duration = cursor.fetchone()
        self.assertEqual(date, "2020-02-01")
        self.assertEqual(start_time, "08:00")
        self.assertEqual(end_time, "16:00")
        self.assertEqual(break_duration, 30)

        # test remove_work_hours
        args = argparse.Namespace(command="rm", date="2020-02-01")
        stmp.args = args
        stmp.remove_work_hours()

        cursor: Cursor = stmp.db.execute(
            "SELECT * FROM work_hours WHERE date = '2020-02-01'"
        )
        self.assertIsNone(cursor.fetchone())

    @patch("sys.stdout", new_callable=StringIO)
    def test_show_data(self, mock_stdout):
        stmp = Stmp(Database("test3.db"), None)
        self.add_record_to_database(
            stmp, "add", "2020-02-01", "08:00", "16:00", 30, "Test note", True
        )

        # show json including notes
        args = argparse.Namespace(
            command="show", date="2020-02-01", notes=True, format="json"
        )
        stmp.args = args

        stmp.show_data()
        self.assertEqual(
            mock_stdout.getvalue(),
            """[
    {
        "date": "2020-02-01",
        "start_time": "08:00",
        "end_time": "16:00",
        "break_duration": 30.0,
        "working_hours": 7.5,
        "overtime_hours": -0.3,
        "cumulative_overtime_hours": -0.3,
        "notes": [
            {
                "id": 1,
                "date": "2020-02-01",
                "note": "Test note"
            }
        ]
    }
]
""",
        )

        # show json excluding notes
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        args = argparse.Namespace(
            command="show", date="2020-02-01", notes=None, format="json"
        )
        stmp.args = args

        stmp.show_data()
        self.assertEqual(
            mock_stdout.getvalue(),
            """[
    {
        "date": "2020-02-01",
        "start_time": "08:00",
        "end_time": "16:00",
        "break_duration": 30.0,
        "working_hours": 7.5,
        "overtime_hours": -0.3,
        "cumulative_overtime_hours": -0.3
    }
]
""",
        )

        self.add_record_to_database(
            stmp, "add", "2020-02-02", "07:00", "15:00", 50, "Test note 2", True
        )
        self.add_record_to_database(
            stmp, "add", "2020-03-02", "06:00", "14:00", None, "Test note 3", True
        )

        # show table including notes
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        args = argparse.Namespace(
            command="show",
            date=None,
            month="02",
            year="2020",
            all=None,
            notes=True,
            format="table",
        )
        stmp.args = args

        stmp.show_data()
        self.assertEqual(
            mock_stdout.getvalue(),
            """| date       | start_time   | end_time   |   break_duration |   working_hours |   overtime_hours |   cumulative_overtime_hours |   note_id | note        |
|------------|--------------|------------|------------------|-----------------|------------------|-----------------------------|-----------|-------------|
| 2020-02-01 | 08:00        | 16:00      |               30 |            7.5  |            -0.3  |                       -0.3  |         1 | Test note   |
| 2020-02-02 | 07:00        | 15:00      |               50 |            7.17 |            -0.63 |                       -0.93 |         2 | Test note 2 |
""",
        )

        # show markdown
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        args = argparse.Namespace(
            command="show",
            date=None,
            month=None,
            year="2020",
            all=None,
            notes=True,
            format="markdown",
        )
        stmp.args = args

        stmp.show_data()
        self.assertEqual(
            mock_stdout.getvalue(),
            """## 2020-02-01 | 08:00 - 16:00

- Test note


## 2020-02-02 | 07:00 - 15:00

- Test note 2


## 2020-03-02 | 06:00 - 14:00

- Test note 3



""",
        )

        # show all including notes
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        args = argparse.Namespace(
            command="show",
            date=None,
            month=None,
            year=None,
            all=True,
            notes=True,
            format="table",
        )
        stmp.args = args

        stmp.show_data()
        self.assertEqual(
            mock_stdout.getvalue(),
            """| date       | start_time   | end_time   |   break_duration |   working_hours |   overtime_hours |   cumulative_overtime_hours |   note_id | note        |
|------------|--------------|------------|------------------|-----------------|------------------|-----------------------------|-----------|-------------|
| 2020-02-01 | 08:00        | 16:00      |               30 |            7.5  |            -0.3  |                       -0.3  |         1 | Test note   |
| 2020-02-02 | 07:00        | 15:00      |               50 |            7.17 |            -0.63 |                       -0.93 |         2 | Test note 2 |
| 2020-03-02 | 06:00        | 14:00      |                  |                 |                  |                       -0.93 |         3 | Test note 3 |
""",
        )

        # show all excluding notes
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        args = argparse.Namespace(
            command="show",
            date=None,
            month=None,
            year=None,
            all=True,
            notes=None,
            format="table",
        )
        stmp.args = args

        stmp.show_data()
        self.assertEqual(
            mock_stdout.getvalue(),
            """| date       | start_time   | end_time   |   break_duration |   working_hours |   overtime_hours |   cumulative_overtime_hours |
|------------|--------------|------------|------------------|-----------------|------------------|-----------------------------|
| 2020-02-01 | 08:00        | 16:00      |               30 |            7.5  |            -0.3  |                       -0.3  |
| 2020-02-02 | 07:00        | 15:00      |               50 |            7.17 |            -0.63 |                       -0.93 |
| 2020-03-02 | 06:00        | 14:00      |                  |                 |                  |                       -0.93 |
""",
        )

    def add_record_to_database(
        self,
        stmp,
        command,
        date=None,
        start_time=None,
        end_time=None,
        break_duration=None,
        note=None,
        overwrite=None,
    ):
        args = argparse.Namespace(
            command=command,
            date=date,
            start_time=start_time,
            end_time=end_time,
            break_duration=break_duration,
            note=note,
            overwrite=overwrite,
        )
        stmp.args = args

        # add work hours and notes
        stmp.update_work_hours()
        stmp.update_notes()
        work_hours_cursor: Cursor = stmp.db.execute(
            f"SELECT * FROM work_hours WHERE date = '{date}'"
        )
        date, start_time, end_time, break_duration = work_hours_cursor.fetchone()
        notes_cursor: Cursor = stmp.db.execute(
            f"SELECT * FROM notes WHERE date = '{date}'"
        )
        id, date, note = notes_cursor.fetchone()
        self.assertEqual(date, date)
        self.assertEqual(start_time, start_time)
        self.assertEqual(end_time, end_time)
        self.assertEqual(break_duration, break_duration)
        self.assertEqual(note, note)

    @patch("builtins.open", new_callable=mock_open)
    @patch.object(Stmp, "dump_to_file")
    def test_dump_data(self, mock_dump_to_file, mock_open):
        args = argparse.Namespace(
            command="add",
            date="2020-02-01",
            start_time="08:00",
            end_time="16:00",
            break_duration=30,
            note="Test note",
            overwrite=True,
        )
        stmp = Stmp(Database("test4.db"), args)

        # add work hours and notes
        stmp.update_work_hours()
        stmp.update_notes()
        work_hours_cursor: Cursor = stmp.db.execute(
            "SELECT * FROM work_hours WHERE date = '2020-02-01'"
        )
        date, start_time, end_time, break_duration = work_hours_cursor.fetchone()
        notes_cursor: Cursor = stmp.db.execute(
            "SELECT * FROM notes WHERE date = '2020-02-01'"
        )
        id, date, note = notes_cursor.fetchone()
        self.assertEqual(date, "2020-02-01")
        self.assertEqual(start_time, "08:00")
        self.assertEqual(end_time, "16:00")
        self.assertEqual(break_duration, 30)
        self.assertEqual(note, "Test note")

        # dump
        args = argparse.Namespace(command="dump", destination=".")
        stmp.args = args
        stmp.dump_data()
        mock_dump_to_file.assert_called()
        mock_dump_to_file.assert_any_call(ANY, "notes")
        mock_dump_to_file.assert_any_call(ANY, "work_hours")

    @patch("sys.stdout", new_callable=StringIO)
    def test_check_data(self, mock_stdout):
        args = argparse.Namespace(
            command="add",
            date="2020-02-01",
            start_time="08:00",
            end_time="16:00",
            break_duration=30,
            note="Test note",
            overwrite=True,
        )
        stmp = Stmp(Database("test5.db"), args)

        # add complete work hours
        stmp.update_work_hours()
        work_hours_cursor: Cursor = stmp.db.execute(
            "SELECT * FROM work_hours WHERE date = '2020-02-01'"
        )
        date, start_time, end_time, break_duration = work_hours_cursor.fetchone()
        self.assertEqual(date, "2020-02-01")
        self.assertEqual(start_time, "08:00")
        self.assertEqual(end_time, "16:00")
        self.assertEqual(break_duration, 30)

        # check
        args = argparse.Namespace(command="check")
        stmp.args = args
        stmp.check_data()
        self.assertEqual(mock_stdout.getvalue(), "")

        # check
        # Add incomplete record
        args = argparse.Namespace(
            command="add",
            date="2020-02-02",
            start_time="08:00",
            end_time=None,
            break_duration=None,
            note="Test note",
            overwrite=True,
        )
        stmp.args = args
        stmp.update_work_hours()

        args = argparse.Namespace(command="check")
        stmp.args = args
        stmp.check_data()
        self.assertEqual(
            mock_stdout.getvalue(),
            "Missing end_time for 2020-02-02\nMissing break_duration for 2020-02-02\n",
        )


if __name__ == "__main__":
    unittest.main()
