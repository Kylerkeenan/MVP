from datetime import date, timedelta

from etl.common import fetch_schedule_window, now_iso, upsert_rows, validate_non_empty


if __name__ == '__main__':
    start = date.today()
    end = start + timedelta(days=7)
    schedule = fetch_schedule_window(start, end)
    validate_non_empty('schedule', schedule)

    rows = [
        {
            'game_id': str(r.GAME_ID),
            'game_date': r.GAME_DATE_EST.isoformat(),
            'home_team_id': int(r.HOME_TEAM_ID),
            'away_team_id': int(r.VISITOR_TEAM_ID),
            'status': r.GAME_STATUS_TEXT,
            'updated_at': now_iso(),
        }
        for r in schedule.itertuples()
    ]
    upsert_rows('schedule', rows, ['game_id'])
    print(f'Upserted {len(rows)} schedule rows')
