"""Settings read from the environment (backend build-plan). Plain os.environ, no extra library."""

import os

# Where the SQLite file lives. Compose sets /data/txnweave.db on a named volume.
DB_PATH = os.environ.get("TXNWEAVE_DB_PATH", "./data/txnweave.db")

# The largest CSV file the import accepts (BD13). Bigger files get 413.
MAX_IMPORT_BYTES = 5_000_000
