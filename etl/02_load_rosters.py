from etl.common import fetch_roster, now_iso, scheduled_team_ids, upsert_rows


if __name__ == '__main__':
    team_ids = scheduled_team_ids()
    if not team_ids:
        print('No scheduled teams yet; loading all teams from teams table')
        from db.database import get_engine
        from sqlalchemy import text

        with get_engine().begin() as conn:
            team_ids = [row[0] for row in conn.execute(text('SELECT team_id FROM teams')).fetchall()]

    total = 0
    for team_id in team_ids:
        roster = fetch_roster(team_id)
        rows = [
            {
                'player_id': int(r.PLAYER_ID),
                'full_name': r.PLAYER,
                'team_id': int(r.TEAM_ID),
                'position': r.POSITION,
                'height': r.HEIGHT,
                'weight': str(r.WEIGHT),
                'updated_at': now_iso(),
            }
            for r in roster.itertuples()
        ]
        upsert_rows('players', rows, ['player_id'])
        total += len(rows)
    print(f'Upserted {total} players')
