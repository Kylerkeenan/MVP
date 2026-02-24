# NBA MVP Analytics App (Streamlit)

MVP NBA analytics dashboard that combines upcoming schedule, recent team/player form, probable starters, and heuristic positional matchups.

## Features
- Select upcoming game from next 7 days.
- Team tabs with last 5 games (box stats + trend chart).
- Most recent starting lineup (with fallback inference by minutes).
- Player drilldown for last 10 games + rolling 5-game averages.
- Probable matchup table (heuristic by position + minutes).
- Refresh button triggers idempotent ETL pipeline.
- Data freshness timestamps shown in sidebar.
- Postgres via Docker Compose, or SQLite fallback via `.env`.

## Project Structure
```
app/        # Streamlit UI + config
etl/        # Data ingestion scripts and transforms
db/         # DB schema and connection helpers
scripts/    # Orchestration scripts + PowerShell runners
tests/      # Minimal tests
```

## Setup (macOS/Linux)
1. Install dependencies:
   ```bash
   make setup
   ```
2. Configure environment:
   ```bash
   cp .env.example .env
   ```

## Windows Setup (PowerShell)
Use these exact commands for a repeatable setup:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."
pip install -r requirements.txt
Copy-Item .env.example .env -ErrorAction SilentlyContinue
docker compose up -d
python scripts/init_db.py
python scripts/run_etl.py
python -m streamlit run app/main.py
```

Optional helper scripts:
- `powershell -ExecutionPolicy Bypass -File scripts/run_etl.ps1`
- `powershell -ExecutionPolicy Bypass -File scripts/run.ps1`

## Database
- Start Postgres:
  ```bash
  docker compose up -d
  ```
- Initialize schema:
  ```bash
  make db
  ```

## Run ETL
```bash
make etl
```

ETL scripts executed in order:
1. `etl/01_load_teams.py`
2. `etl/03_load_schedule.py`
3. `etl/02_load_rosters.py`
4. `etl/04_load_recent_games.py`
5. `etl/05_load_player_gamelogs.py`
6. `etl/06_load_lineups.py`

## Run App
```bash
python -m streamlit run app/main.py
```
Open `http://localhost:8501`.

## Testing
```bash
make test
```

## Notes / Limitations
- `nba_api` can be rate-limited by upstream; scripts use disk cache + sleep throttling + retries.
- Starting lineups are best effort from latest logs; fallback uses highest-minute players.
- Matchups are heuristic only and clearly labeled as non-official.
