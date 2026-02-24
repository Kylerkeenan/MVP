import subprocess
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from sqlalchemy import text

from db.database import get_engine


st.set_page_config(page_title='NBA MVP Analytics', layout='wide')


def qdf(query: str, params=None) -> pd.DataFrame:
    with get_engine().begin() as conn:
        return pd.read_sql(text(query), conn, params=params or {})


def freshness(table: str) -> str:
    df = qdf(f'SELECT MAX(updated_at) AS ts FROM {table}')
    ts = df.iloc[0]['ts']
    return str(ts) if ts is not None else 'Never'


def load_schedule(selected_date: date) -> pd.DataFrame:
    return qdf(
        """
        SELECT s.game_id, s.game_date, s.status,
               ht.name AS home_name, ht.team_id AS home_team_id,
               at.name AS away_name, at.team_id AS away_team_id
        FROM schedule s
        JOIN teams ht ON ht.team_id = s.home_team_id
        JOIN teams at ON at.team_id = s.away_team_id
        WHERE s.game_date = :game_date
        ORDER BY s.game_date
        """,
        {'game_date': selected_date.isoformat()},
    )


def team_last5(team_id: int) -> pd.DataFrame:
    return qdf(
        """
        SELECT game_date, matchup, wl, pts, reb, ast, tov, fg_pct, fg3_pct
        FROM team_game_stats
        WHERE team_id = :team_id
        ORDER BY game_date DESC
        LIMIT 5
        """,
        {'team_id': team_id},
    )


def latest_lineup(team_id: int) -> pd.DataFrame:
    return qdf(
        """
        SELECT l.game_id, p.player_id, p.full_name, p.position, p.height, p.weight,
               l.minutes, l.lineup_source
        FROM lineups l
        JOIN players p ON p.player_id = l.player_id
        WHERE l.team_id = :team_id
          AND l.game_id = (
            SELECT game_id FROM lineups WHERE team_id = :team_id ORDER BY updated_at DESC LIMIT 1
          )
        ORDER BY p.position, p.full_name
        """,
        {'team_id': team_id},
    )


def player_log(player_id: int) -> pd.DataFrame:
    df = qdf(
        """
        SELECT game_date, matchup, minutes, pts, reb, ast, stl, blk, tov, fg_pct, fg3_pct
        FROM player_game_stats
        WHERE player_id = :player_id
        ORDER BY game_date DESC
        LIMIT 10
        """,
        {'player_id': player_id},
    )
    if not df.empty:
        for col in ['pts', 'reb', 'ast']:
            df[f'{col}_roll5'] = df[col][::-1].rolling(5, min_periods=1).mean()[::-1].round(2)
    return df


def probable_matchups(home_lineup: pd.DataFrame, away_lineup: pd.DataFrame) -> pd.DataFrame:
    positions = ['PG', 'SG', 'SF', 'PF', 'C']

    def prep(df: pd.DataFrame) -> pd.DataFrame:
        tmp = df.copy()
        tmp['pos_norm'] = tmp['position'].fillna('UNK').str.split('-').str[0]
        tmp['min_rank'] = pd.to_numeric(tmp['minutes'], errors='coerce').fillna(0)
        return tmp

    home = prep(home_lineup)
    away = prep(away_lineup)
    rows = []
    for pos in positions:
        h = home[home['pos_norm'] == pos].sort_values('min_rank', ascending=False).head(1)
        a = away[away['pos_norm'] == pos].sort_values('min_rank', ascending=False).head(1)
        if h.empty:
            h = home.sort_values('min_rank', ascending=False).head(1)
        if a.empty:
            a = away.sort_values('min_rank', ascending=False).head(1)
        rows.append({'Position': pos, 'Away Player': a.iloc[0]['full_name'] if not a.empty else '-', 'Home Player': h.iloc[0]['full_name'] if not h.empty else '-'})
    return pd.DataFrame(rows)


def team_tab(team_name: str, team_id: int):
    st.subheader(f'{team_name}: Last 5 Games')
    df = team_last5(team_id)
    if df.empty:
        st.warning('No recent games found yet.')
    else:
        st.dataframe(df, use_container_width=True)
        st.line_chart(df[['pts', 'reb', 'ast']].iloc[::-1], height=160)

    st.subheader('Most Recent Starting Lineup')
    lineup = latest_lineup(team_id)
    if lineup.empty:
        st.error('No lineup data available. ETL will infer starters when player logs are available.')
        return None

    st.caption(f"Lineup source: {lineup['lineup_source'].iloc[0]}")
    st.dataframe(lineup[['full_name', 'position', 'height', 'weight', 'minutes']], use_container_width=True)
    return lineup


def main() -> None:
    st.title('NBA MVP Analytics Dashboard')

    col1, col2 = st.columns(2)
    with col1:
        selected_date = st.sidebar.date_input('Select date', value=date.today(), min_value=date.today() - timedelta(days=1), max_value=date.today() + timedelta(days=7))
    with col2:
        if st.sidebar.button('Refresh data'):
            with st.spinner('Running ETL...'):
                try:
                    subprocess.run(['python', 'scripts/run_etl.py'], check=True)
                    st.sidebar.success('Data refresh complete')
                except Exception as exc:
                    st.sidebar.error(f'Refresh failed: {exc}')

    st.sidebar.markdown('### Data Freshness')
    for table in ['teams', 'players', 'schedule', 'team_game_stats', 'player_game_stats', 'lineups']:
        st.sidebar.write(f'- {table}: {freshness(table)}')

    schedule = load_schedule(selected_date)
    if schedule.empty:
        st.info('No upcoming games for selected date. Try refreshing ETL.')
        st.stop()

    schedule['label'] = schedule.apply(lambda r: f"{r.away_name} @ {r.home_name} ({r.game_date})", axis=1)
    selected = st.sidebar.selectbox('Select game', schedule['label'].tolist())
    row = schedule[schedule['label'] == selected].iloc[0]

    st.header(f"{row['away_name']} @ {row['home_name']}")
    st.caption('Matchups are heuristic only, based on position and minutes/starting status. Not an official depth chart.')

    away_tab, home_tab = st.tabs([row['away_name'], row['home_name']])
    with away_tab:
        away_lineup = team_tab(row['away_name'], int(row['away_team_id']))
    with home_tab:
        home_lineup = team_tab(row['home_name'], int(row['home_team_id']))

    if away_lineup is not None and home_lineup is not None:
        st.subheader('Probable Matchups (Heuristic)')
        st.dataframe(probable_matchups(home_lineup, away_lineup), use_container_width=True)

    all_lineup = pd.concat([df for df in [away_lineup, home_lineup] if df is not None], ignore_index=True)
    if not all_lineup.empty:
        player_name = st.selectbox('Player drilldown', all_lineup['full_name'].unique().tolist())
        pid = int(all_lineup[all_lineup['full_name'] == player_name]['player_id'].iloc[0])
        plog = player_log(pid)
        st.subheader(f'{player_name} - Last 10 Games')
        if plog.empty:
            st.warning('No player logs loaded.')
        else:
            st.dataframe(plog, use_container_width=True)


if __name__ == '__main__':
    main()
