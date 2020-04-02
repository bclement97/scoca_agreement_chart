# SCOCA Agreement Chart

TODO: Description


## Dependencies

- Python 2.7
    - pip (if not using Docker)
- PHP 5.6
- SQLite3
- Docker (optional)
- Make (optional)


## Project Structure

This project comprises three main parts:

 - `cli/`: the CLI, using Python 2.7
 - `admin/`: the Admin Interface, using PHP 5.6
 - `.db`: the shared SQLite3 database file

`.db` will not exist initially and will be generated when the CLI is run for the first time.

### CLI

- `conifg/` contains configuration files
    - `courtlistener_api.token` contains the CourtListener API Authorization Token (see [Setup](#setup))
    - `justices.csv` is used to initially populate the `justices` table
- `out/` contains the generated agreement charts
- `init.sql` defines the SQLite3 database
- `__main__.py` is the CLI's entry point.

All Python files include their own documentation.

### Admin Interface

- `lib/` contains PHP files with helper functions to be included as needed
- `styles/` contains CSS stylesheets

The remaining PHP files are the frontend.


## Setup

### CourtListener API Token

1. Navigate to https://www.courtlistener.com/api/rest-info/ to view your "API Authorization Token"

2. Place the token into the file `cli/config/courtlistener_api.token`

If you have Docker installed, skip the next section.

### Install Python Requirements

In the base directory, install the required Python modules via pip:
```
pip install [--user] -r cli/requirements.txt
```


## Running

Navigate to the base directory.

If you have docker installed, run `docker-compose up --build`. Alternatively, if you have Make installed as well, simply run `make`.

Otherwise, run `python -m cli`.
