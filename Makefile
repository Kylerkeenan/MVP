PYTHON=python
PIP=pip

setup:
	$(PIP) install -r requirements.txt
	cp -n .env.example .env || true


db:
	$(PYTHON) scripts/init_db.py

etl:
	$(PYTHON) scripts/run_etl.py

run:
	streamlit run app/app.py

test:
	pytest -q
