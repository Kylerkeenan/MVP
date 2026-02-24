import sqlite3
from typing import Iterable


def upsert_sqlite_rows(conn: sqlite3.Connection, table: str, rows: list[dict], conflict_cols: list[str]) -> None:
    if not rows:
        return
    cols = list(rows[0].keys())
    placeholders = ', '.join(['?' for _ in cols])
    update_cols = [c for c in cols if c not in conflict_cols]
    set_clause = ', '.join([f"{c}=excluded.{c}" for c in update_cols])
    sql = (
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT ({', '.join(conflict_cols)}) DO UPDATE SET {set_clause}"
    )
    conn.executemany(sql, [tuple(row[c] for c in cols) for row in rows])
    conn.commit()
