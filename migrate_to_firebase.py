import argparse
import os
from pathlib import Path

import db


def main():
    parser = argparse.ArgumentParser(
        description="Copy the local SQLite tracker data into Firebase Cloud Firestore."
    )
    parser.add_argument(
        "--sqlite",
        default=os.environ.get("DATABASE_PATH", "database.db"),
        help="Path to the SQLite database (default: DATABASE_PATH or database.db).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace Firestore documents with matching IDs.",
    )
    args = parser.parse_args()

    sqlite_path = Path(args.sqlite)
    if not sqlite_path.is_file():
        parser.error(f"SQLite database file not found: {sqlite_path}")
    if not db.uses_firebase():
        parser.error(
            "Set FIREBASE_SERVICE_ACCOUNT_KEY or GOOGLE_APPLICATION_CREDENTIALS first."
        )

    counts = db.import_sqlite_database(str(sqlite_path), overwrite=args.overwrite)
    print("SQLite data copied to Firestore:")
    for collection, count in counts.items():
        print(f"  {collection}: {count} document(s) imported")


if __name__ == "__main__":
    main()
