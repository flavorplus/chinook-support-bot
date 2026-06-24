import pathlib
import subprocess
import sys
from chinook_bot.db import get_connection, list_tables


def test_database_contains_core_tables() -> None:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    db_path = repo_root / "data" / "Chinook.db"
    if not db_path.exists():
        subprocess.run([sys.executable, str(repo_root / "scripts" / "download_chinook.py")], check=True)
    conn = get_connection(str(db_path))
    tables = list_tables(conn)
    conn.close()
    assert "Customer" in tables
    assert "Invoice" in tables
    assert "Track" in tables
