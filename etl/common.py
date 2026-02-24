import logging
import time
from datetime import date, datetime, timedelta
from typing import Iterable

import pandas as pd
import requests_cache
from nba_api.stats.endpoints import (
    commonallplayers,
    commonteamroster,
    leaguegamefinder,
    leaguedashteamstats,
    scoreboardv2,
)
from sqlalchemy import text
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from db.database import get_engine

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
LOGGER = logging.getLogger(__name__)

SETTINGS = get_settings()
requests_cache.install_cache(cache_name=f"{SETTINGS.cache_dir}/nba_api_cache", backend='sqlite', expire_after=3600)


def throttle() -> None:
    time.sleep(SETTINGS.api_throttle_seconds)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def safe_call(func, *args, **kwargs):
    throttle()
    return func(*args, **kwargs)


def upsert_rows(table: str, rows: list[dict], conflict_cols: list[str]) -> None:
    if not rows:
        return
    engine = get_engine()
    cols = list(rows[0].keys())
    col_csv = ', '.join(cols)
    conflict_csv = ', '.join(conflict_cols)
    update_cols = [c for c in cols if c not in conflict_cols]
    set_clause = ', '.join([f"{c}=excluded.{c}" for c in update_cols])

    sql = text(
        f"INSERT INTO {table} ({col_csv}) VALUES ({', '.join([f':{c}' for c in cols])}) "
        f"ON CONFLICT ({conflict_csv}) DO UPDATE SET {set_clause}"
    )

    with engine.begin() as conn:
        conn.execute(sql, rows)


def fetch_teams() -> pd.DataFrame:
    df = pd.DataFrame(safe_call(leaguedashteamstats.LeagueDashTeamStats, season='2024-25').get_data_frames()[0])
    return df[['TEAM_ID', 'TEAM_NAME', 'TEAM_ABBREVIATION']].drop_duplicates()


def fetch_roster(team_id: int) -> pd.DataFrame:
    roster = safe_call(commonteamroster.CommonTeamRoster, team_id=team_id, season='2024-25').common_team_roster.get_data_frame()
    keep_cols = ['PLAYER_ID', 'PLAYER', 'TEAM_ID', 'POSITION', 'HEIGHT', 'WEIGHT']
    return roster[keep_cols]


def fetch_schedule_window(start: date, end: date) -> pd.DataFrame:
    game_rows = []
    current = start
    while current <= end:
        board = safe_call(scoreboardv2.ScoreboardV2, game_date=current.strftime('%m/%d/%Y'))
        games = board.game_header.get_data_frame()
        if not games.empty:
            game_rows.append(games)
        current += timedelta(days=1)
    if not game_rows:
        return pd.DataFrame()
    out = pd.concat(game_rows, ignore_index=True)
    out['GAME_DATE_EST'] = pd.to_datetime(out['GAME_DATE_EST']).dt.date
    return out[['GAME_ID', 'GAME_DATE_EST', 'HOME_TEAM_ID', 'VISITOR_TEAM_ID', 'GAME_STATUS_TEXT']]


def fetch_team_recent_games(team_id: int, last_n: int = 5) -> pd.DataFrame:
    finder = safe_call(leaguegamefinder.LeagueGameFinder, team_id_nullable=team_id, season_type_nullable='Regular Season')
    df = finder.get_data_frames()[0]
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
    return df.sort_values('GAME_DATE', ascending=False).head(last_n)


def fetch_player_games(player_id: int, last_n: int = 10) -> pd.DataFrame:
    finder = safe_call(leaguegamefinder.LeagueGameFinder, player_id_nullable=player_id, season_type_nullable='Regular Season')
    df = finder.get_data_frames()[0]
    if df.empty:
        return df
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
    return df.sort_values('GAME_DATE', ascending=False).head(last_n)


def scheduled_team_ids() -> list[int]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(text('SELECT DISTINCT home_team_id AS team_id FROM schedule UNION SELECT DISTINCT away_team_id AS team_id FROM schedule')).fetchall()
    return [int(r[0]) for r in rows]


def scheduled_players() -> list[int]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(text('SELECT DISTINCT player_id FROM players WHERE team_id IN (SELECT home_team_id FROM schedule UNION SELECT away_team_id FROM schedule)')).fetchall()
    return [int(r[0]) for r in rows]


def validate_non_empty(name: str, df: pd.DataFrame) -> None:
    if df.empty:
        LOGGER.warning('%s returned no rows', name)


def now_iso() -> str:
    return datetime.utcnow().isoformat()
