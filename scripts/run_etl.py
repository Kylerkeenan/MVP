import subprocess

SCRIPTS = [
    'etl/01_load_teams.py',
    'etl/03_load_schedule.py',
    'etl/02_load_rosters.py',
    'etl/04_load_recent_games.py',
    'etl/05_load_player_gamelogs.py',
    'etl/06_load_lineups.py',
]

if __name__ == '__main__':
    for script in SCRIPTS:
        print(f'Running {script}')
        subprocess.run(['python', script], check=True)
