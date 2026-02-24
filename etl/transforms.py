from typing import Any


def parse_team_game_row(row: Any) -> dict:
    return {
        'game_id': str(row.GAME_ID),
        'team_id': int(row.TEAM_ID),
        'game_date': row.GAME_DATE.date().isoformat(),
        'matchup': row.MATCHUP,
        'wl': row.WL,
        'pts': int(row.PTS),
        'reb': int(row.REB),
        'ast': int(row.AST),
        'tov': int(row.TOV),
        'fg_pct': float(row.FG_PCT),
        'fg3_pct': float(row.FG3_PCT),
        'plus_minus': float(row.PLUS_MINUS),
    }
