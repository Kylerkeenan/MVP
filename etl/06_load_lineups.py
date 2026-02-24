import pandas as pd
from sqlalchemy import text

from db.database import get_engine
from etl.common import now_iso, scheduled_team_ids, upsert_rows


def infer_lineup(team_id: int) -> tuple[str, list[dict]]:
    engine = get_engine()
    query = text(
        """
        SELECT pgs.game_id, pgs.player_id, pgs.minutes, pgs.is_starter,
               pgs.game_date
        FROM player_game_stats pgs
        WHERE pgs.team_id = :team_id
        ORDER BY pgs.game_date DESC
        """
    )
    with engine.begin() as conn:
        df = pd.read_sql(query, conn, params={'team_id': team_id})

    if df.empty:
        return 'missing', []

    latest_game = df['game_id'].iloc[0]
    latest = df[df['game_id'] == latest_game].copy()
    starters = latest[latest['is_starter'] == 1]
    source = 'official_starters'

    if starters.empty or len(starters) < 5:
        source = 'inferred_by_minutes'
        latest['min_num'] = pd.to_numeric(latest['minutes'], errors='coerce').fillna(0)
        starters = latest.sort_values('min_num', ascending=False).head(5)

    rows = [
        {
            'game_id': str(latest_game),
            'team_id': int(team_id),
            'player_id': int(r.player_id),
            'is_starter': True,
            'minutes': str(r.minutes),
            'lineup_source': source,
            'updated_at': now_iso(),
        }
        for r in starters.itertuples()
    ]
    return source, rows


if __name__ == '__main__':
    count = 0
    for team_id in scheduled_team_ids():
        source, rows = infer_lineup(team_id)
        if source == 'missing':
            print(f'No lineup data for team {team_id}')
            continue
        upsert_rows('lineups', rows, ['game_id', 'team_id', 'player_id'])
        count += len(rows)
    print(f'Upserted {count} lineup rows')
