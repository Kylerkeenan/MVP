from etl.common import fetch_player_games, now_iso, scheduled_players, upsert_rows


if __name__ == '__main__':
    players = scheduled_players()
    total = 0
    for player_id in players:
        logs = fetch_player_games(player_id, last_n=10)
        if logs.empty:
            continue
        rows = []
        for g in logs.itertuples():
            rows.append(
                {
                    'game_id': str(g.GAME_ID),
                    'player_id': int(g.PLAYER_ID),
                    'team_id': int(g.TEAM_ID),
                    'game_date': g.GAME_DATE.date().isoformat(),
                    'matchup': g.MATCHUP,
                    'minutes': g.MIN,
                    'pts': int(g.PTS),
                    'reb': int(g.REB),
                    'ast': int(g.AST),
                    'stl': int(g.STL),
                    'blk': int(g.BLK),
                    'tov': int(g.TOV),
                    'fg_pct': float(g.FG_PCT),
                    'fg3_pct': float(g.FG3_PCT),
                    'is_starter': str(g.START_POSITION).strip() != '',
                    'updated_at': now_iso(),
                }
            )
        upsert_rows('player_game_stats', rows, ['game_id', 'player_id'])
        total += len(rows)
    print(f'Upserted {total} player game rows')
