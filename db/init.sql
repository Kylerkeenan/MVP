CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    abbreviation TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    team_id INTEGER,
    position TEXT,
    height TEXT,
    weight TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS schedule (
    game_id TEXT PRIMARY KEY,
    game_date DATE NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    status TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY(away_team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS team_game_stats (
    game_id TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    game_date DATE,
    matchup TEXT,
    wl TEXT,
    pts INTEGER,
    reb INTEGER,
    ast INTEGER,
    tov INTEGER,
    fg_pct FLOAT,
    fg3_pct FLOAT,
    plus_minus FLOAT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, team_id),
    FOREIGN KEY(team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS player_game_stats (
    game_id TEXT NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER,
    game_date DATE,
    matchup TEXT,
    minutes TEXT,
    pts INTEGER,
    reb INTEGER,
    ast INTEGER,
    stl INTEGER,
    blk INTEGER,
    tov INTEGER,
    fg_pct FLOAT,
    fg3_pct FLOAT,
    is_starter BOOLEAN,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, player_id),
    FOREIGN KEY(player_id) REFERENCES players(player_id),
    FOREIGN KEY(team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS lineups (
    game_id TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    is_starter BOOLEAN DEFAULT FALSE,
    minutes TEXT,
    lineup_source TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, team_id, player_id),
    FOREIGN KEY(team_id) REFERENCES teams(team_id),
    FOREIGN KEY(player_id) REFERENCES players(player_id)
);

CREATE INDEX IF NOT EXISTS idx_schedule_game_date ON schedule(game_date);
CREATE INDEX IF NOT EXISTS idx_schedule_teams ON schedule(home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_team_stats_team_date ON team_game_stats(team_id, game_date);
CREATE INDEX IF NOT EXISTS idx_player_stats_player_game ON player_game_stats(player_id, game_id);
CREATE INDEX IF NOT EXISTS idx_lineups_team_game ON lineups(team_id, game_id);
