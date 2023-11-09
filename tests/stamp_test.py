import argparse
import unittest
import os
from sqlite3 import Cursor
from sqlite_utils import Database
from io import StringIO
from unittest.mock import ANY, patch, mock_open
from stamp.stamp import Stamp


class TestStamp(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        # Specify the database file path
        db_file_paths = ["test1.db", "test2.db", "test3.db", "test4.db", "test5.db"]

        # Remove the database file
        for db_file_path in db_file_paths:
            if os.path.exists(db_file_path):
                os.remove(db_file_path)
            else:
                print(f"The file {db_file_path} does not exist")

    def test_set_default_date(self):
        args = argparse.Namespace(
            command="add",
            date="2020-01-01",
            start_time=None,
            end_time=None,
            break_duration=None,
            note="Test note",
            overwrite=True,
        )
        stamp = Stamp(Database("test1.db"), args)

        stamp.set_default_date()
        self.assertIsNotNone(stamp.args.date)

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
        stamp = Stamp(Database("test2.db"), args)

        # test update_notes
        stamp.update_notes()
        cursor: Cursor = stamp.db.execute(
            "SELECT * FROM notes WHERE date = '2020-01-01'"
        )
        id, date, note = cursor.fetchone()
        self.assertEqual(date, "2020-01-01")
        self.assertEqual(note, "Test note")

        # test insert_work_hours
        stamp.update_work_hours()
        cursor: Cursor = stamp.db.execute(
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
        stamp.args = args
        stamp.update_work_hours()
        cursor: Cursor = stamp.db.execute(
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
        stamp.args = args
        stamp.update_work_hours()
        cursor: Cursor = stamp.db.execute(
            "SELECT start_time FROM work_hours WHERE date = '2020-01-01'"
        )
        self.assertEqual(cursor.fetchone()[0], "07:00")

    def test_remove_note(self):
        args = argparse.Namespace(
            command="add", date="2020-02-01", note="Test note", overwrite=True
        )
        stamp = Stamp(Database("test3.db"), args)

        # add note
        stamp.update_notes()
        cursor: Cursor = stamp.db.execute(
            "SELECT * FROM notes WHERE date = '2020-02-01'"
        )
        id, date, note = cursor.fetchone()
        self.assertEqual(date, "2020-02-01")
        self.assertEqual(note, "Test note")

        # test remove_note
        args = argparse.Namespace(command="rm", id=id)
        stamp.args = args
        stamp.remove_note()

        cursor: Cursor = stamp.db.execute(
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
        stamp = Stamp(Database("test3.db"), args)

        # add work hours
        stamp.update_work_hours()
        cursor: Cursor = stamp.db.execute(
            "SELECT * FROM work_hours WHERE date = '2020-02-01'"
        )
        date, start_time, end_time, break_duration = cursor.fetchone()
        self.assertEqual(date, "2020-02-01")
        self.assertEqual(start_time, "08:00")
        self.assertEqual(end_time, "16:00")
        self.assertEqual(break_duration, 30)

        # test remove_work_hours
        args = argparse.Namespace(command="rm", date="2020-02-01")
        stamp.args = args
        stamp.remove_work_hours()

        cursor: Cursor = stamp.db.execute(
            "SELECT * FROM work_hours WHERE date = '2020-02-01'"
        )
        self.assertIsNone(cursor.fetchone())

    @patch("sys.stdout", new_callable=StringIO)
    def test_show_data(self, mock_stdout):
        args = argparse.Namespace(
            command="add",
            date="2020-02-01",
            start_time="08:00",
            end_time="16:00",
            break_duration=30,
            note="Test note",
            overwrite=True,
        )
        stamp = Stamp(Database("test3.db"), args)

        # add work hours and notes
        stamp.update_work_hours()
        stamp.update_notes()
        work_hours_cursor: Cursor = stamp.db.execute(
            "SELECT * FROM work_hours WHERE date = '2020-02-01'"
        )
        date, start_time, end_time, break_duration = work_hours_cursor.fetchone()
        notes_cursor: Cursor = stamp.db.execute(
            "SELECT * FROM notes WHERE date = '2020-02-01'"
        )
        id, date, note = notes_cursor.fetchone()
        self.assertEqual(date, "2020-02-01")
        self.assertEqual(start_time, "08:00")
        self.assertEqual(end_time, "16:00")
        self.assertEqual(break_duration, 30)
        self.assertEqual(note, "Test note")

        # show json
        args = argparse.Namespace(command="show", date="2020-02-01", format="json")
        stamp.args = args

        stamp.show_data()
        self.assertEqual(
            mock_stdout.getvalue(),
            """{
    "date": "2020-02-01",
    "start_time": "08:00",
    "end_time": "16:00",
    "break_duration": 30.0,
    "notes": [
        {
            "id": 1,
            "date": "2020-02-01",
            "note": "Test note"
        }
    ]
}
""",
        )

        # show table
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        args = argparse.Namespace(command="show", date="2020-02-01", format="table")
        stamp.args = args

        stamp.show_data()
        self.assertEqual(
            mock_stdout.getvalue(),
            """| date       | start_time   | end_time   |   break_duration |   note_id | note      |
|------------|--------------|------------|------------------|-----------|-----------|
| 2020-02-01 | 08:00        | 16:00      |               30 |         1 | Test note |
""",
        )

        # show markdown
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        args = argparse.Namespace(command="show", date="2020-02-01", format="markdown")
        stamp.args = args

        stamp.show_data()
        self.assertEqual(
            mock_stdout.getvalue(),
            """## 2020-02-01

\t- Test note

""",
        )

    @patch("builtins.open", new_callable=mock_open)
    @patch.object(Stamp, "dump_to_file")
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
        stamp = Stamp(Database("test4.db"), args)

        # add work hours and notes
        stamp.update_work_hours()
        stamp.update_notes()
        work_hours_cursor: Cursor = stamp.db.execute(
            "SELECT * FROM work_hours WHERE date = '2020-02-01'"
        )
        date, start_time, end_time, break_duration = work_hours_cursor.fetchone()
        notes_cursor: Cursor = stamp.db.execute(
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
        stamp.args = args
        stamp.dump_data()
        mock_dump_to_file.assert_called()
        print(mock_dump_to_file.call_args_list)
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
        stamp = Stamp(Database("test5.db"), args)

        # add complete work hours
        stamp.update_work_hours()
        work_hours_cursor: Cursor = stamp.db.execute(
            "SELECT * FROM work_hours WHERE date = '2020-02-01'"
        )
        date, start_time, end_time, break_duration = work_hours_cursor.fetchone()
        self.assertEqual(date, "2020-02-01")
        self.assertEqual(start_time, "08:00")
        self.assertEqual(end_time, "16:00")
        self.assertEqual(break_duration, 30)

        # check
        args = argparse.Namespace(command="check")
        stamp.args = args
        stamp.check_data()
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
        stamp.args = args
        stamp.update_work_hours()

        args = argparse.Namespace(command="check")
        stamp.args = args
        stamp.check_data()
        self.assertEqual(
            mock_stdout.getvalue(),
            "Missing end_time for 2020-02-02\nMissing break_duration for 2020-02-02\n",
        )


if __name__ == "__main__":
    unittest.main()
