from types import SimpleNamespace

from etl.transforms import parse_team_game_row


def test_parse_team_game_row():
    row = SimpleNamespace(
        GAME_ID='001',
        TEAM_ID=1610612747,
        GAME_DATE=__import__('datetime').datetime(2025, 1, 1),
        MATCHUP='LAL vs BOS',
        WL='W',
        PTS=110,
        REB=44,
        AST=25,
        TOV=12,
        FG_PCT=0.48,
        FG3_PCT=0.37,
        PLUS_MINUS=8,
    )
    parsed = parse_team_game_row(row)
    assert parsed['game_id'] == '001'
    assert parsed['team_id'] == 1610612747
    assert parsed['pts'] == 110
    assert parsed['fg_pct'] == 0.48
