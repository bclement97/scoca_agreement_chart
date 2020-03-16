# SCOCA Agreement Chart CLI

## Setup

1. Install the required modules:
    ```commandline
    pip install [--user] -r requirements.txt
    ```

2. Set the CourtListener API token as an environment variable:
    ```commandline
    export COURTLISTENER_API_TOKEN=<token>
    ```

## Running

In the project's parent directory, run:
```commandline
python -m cli
```

The SQLite3 database file will be located in the same parent directory under `.db`.

The outputted chart will be located in the `out` directory.