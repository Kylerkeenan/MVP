$ErrorActionPreference = 'Stop'

if (-not (Test-Path .\.venv\Scripts\Activate.ps1)) {
    throw 'Virtual environment not found. Run: python -m venv .venv'
}

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
. .\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."

python scripts/run_etl.py
