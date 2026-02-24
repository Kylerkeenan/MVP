import logging

import pandas as pd

from etl.common import fetch_player_games, now_iso, scheduled_players, upsert_rows

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

BATCH_SIZE = 50


def parse_player_game_rows(logs: pd.DataFrame, player_id: int) -> list[dict]:
    if logs.empty:
        return []

    normalized = logs.copy()
    normalized.columns = [c.lower() for c in normalized.columns]
    rows = []
    for _, row in normalized.iterrows():
        game_date = pd.to_datetime(row.get('game_date'), errors='coerce')
        if pd.isna(game_date):
            continue

        start_position = str(row.get('start_position') or '').strip()
        rows.append(
            {
                'game_id': str(row.get('game_id', '')),
                'player_id': int(row.get('player_id') or player_id),
                'team_id': int(row.get('team_id')) if pd.notna(row.get('team_id')) else None,
                'game_date': game_date.date().isoformat(),
                'matchup': row.get('matchup'),
                'minutes': str(row.get('min', '')),
                'pts': int(pd.to_numeric(row.get('pts'), errors='coerce') or 0),
                'reb': int(pd.to_numeric(row.get('reb'), errors='coerce') or 0),
                'ast': int(pd.to_numeric(row.get('ast'), errors='coerce') or 0),
                'stl': int(pd.to_numeric(row.get('stl'), errors='coerce') or 0),
                'blk': int(pd.to_numeric(row.get('blk'), errors='coerce') or 0),
                'tov': int(pd.to_numeric(row.get('tov'), errors='coerce') or 0),
                'fg_pct': float(pd.to_numeric(row.get('fg_pct'), errors='coerce') or 0.0),
                'fg3_pct': float(pd.to_numeric(row.get('fg3_pct'), errors='coerce') or 0.0),
                'is_starter': start_position != '',
                'updated_at': now_iso(),
            }
        )

    return [r for r in rows if r['game_id']]


if __name__ == '__main__':
    players = scheduled_players()
    buffer: list[dict] = []
    total = 0

    for idx, player_id in enumerate(players, start=1):
        if idx % 10 == 0:
            LOGGER.info('Processed %s/%s players', idx, len(players))

        try:
            logs = fetch_player_games(player_id, last_n=10)
            buffer.extend(parse_player_game_rows(logs, player_id))
        except Exception as exc:
            LOGGER.warning('Skipping player %s due to API/parse failure: %s', player_id, exc)
            continue

        if len(buffer) >= BATCH_SIZE:
            upsert_rows('player_game_stats', buffer, ['game_id', 'player_id'])
            total += len(buffer)
            LOGGER.info('Upserted batch of %s rows (%s total)', len(buffer), total)
            buffer = []

    if buffer:
        upsert_rows('player_game_stats', buffer, ['game_id', 'player_id'])
        total += len(buffer)

    print(f'Upserted {total} player game rows')
