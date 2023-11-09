# stmp CLI Tool

## Introduction

stmp is a command-line interface (CLI) tool designed to help developers and other professionals track their work hours and notes. Born out of the need for a simple, flexible, and efficient time tracking tool, stmp aims to make time management as seamless as possible.

## Features

- **Work Hours Tracking**: Easily log your start and end times for each work day.
- **Break Duration**: Keep track of your break times to ensure you're taking adequate rest.
- **Notes**: Add notes to each work day for better context and recall.
- **Checks**: Check if your daily records are complete.
- **Data Dump**: Export your data to stdout or a file for further analysis or backup.

### Automatic Work Hours Tracking

Configure your machine in such a way, that start and end time are automatically tracked with your powering on and off of your machine and set your default break duration. The automatic tracking should always use the `--overwrite False` Flag.

## Installation

To install stmp, follow these steps:

1. Clone the repository: 
```bash
pip install stmp
```

## Usage

To use stmp, you can use the following commands:

- To add a working hours and notes for a day:
```bash
stmp add --date YYYY-MM-DD --start_time HH:MM --end_time HH:MM --break_duration MM --note "Your note"
```
You can omit almost all arguments:
```bash
stmp add --start_time HH:MM
```

- To view records for a day:
```bash
stmp show --date YYYY-MM-DD --format json
```
If you want to view the records for the current day, you can omit the --date argument:
```bash
stmp show
```

- Included help text:
```bash
❯ stmp -h
usage: stmp.py [-h] {add,rm,show,dump,check} ...

Record working hours.

positional arguments:
  {add,rm,show,dump,check}
    add                 Add times and notes for the day
    rm                  Remove a record
    show                Show hours and notes
    dump                Dump the database
    check               Check the database entries for completeness

options:
  -h, --help            show this help message and exit

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
```


## License

stmp is licensed under the [MIT License](LICENSE).

## Contact

If you have any questions or feedback, please feel free to contact me.