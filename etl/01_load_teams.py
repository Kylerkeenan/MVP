from etl.common import fetch_teams, now_iso, upsert_rows, validate_non_empty


if __name__ == '__main__':
    teams = fetch_teams()
    validate_non_empty('teams', teams)
    rows = [
        {
            'team_id': int(r.TEAM_ID),
            'name': r.TEAM_NAME,
            'abbreviation': r.TEAM_ABBREVIATION,
            'updated_at': now_iso(),
        }
        for r in teams.itertuples()
    ]
    upsert_rows('teams', rows, ['team_id'])
    print(f'Upserted {len(rows)} teams')
