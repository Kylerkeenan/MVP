import sqlite3

from db.sqlite_utils import upsert_sqlite_rows


def test_upsert_rows_sqlite():
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE teams (team_id INTEGER PRIMARY KEY, name TEXT, abbreviation TEXT)')

    upsert_sqlite_rows(
        conn,
        'teams',
        [
            {'team_id': 1, 'name': 'A', 'abbreviation': 'AAA'},
            {'team_id': 1, 'name': 'B', 'abbreviation': 'BBB'},
        ],
        ['team_id'],
    )

    row = conn.execute('SELECT team_id, name, abbreviation FROM teams WHERE team_id=1').fetchone()
    assert row == (1, 'B', 'BBB')
