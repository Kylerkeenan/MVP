from etl.common import fetch_team_recent_games, now_iso, scheduled_team_ids, upsert_rows
from etl.transforms import parse_team_game_row


if __name__ == '__main__':
    total = 0
    for team_id in scheduled_team_ids():
        games = fetch_team_recent_games(team_id, last_n=5)
        rows = []
        for g in games.itertuples():
            parsed = parse_team_game_row(g)
            parsed['updated_at'] = now_iso()
            rows.append(parsed)
        upsert_rows('team_game_stats', rows, ['game_id', 'team_id'])
        total += len(rows)
    print(f'Upserted {total} team game rows')
