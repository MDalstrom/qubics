.venv/.deps-installed: pyproject.toml
	.venv/bin/pip install .
	touch .venv/.deps-installed

PY := .venv/bin/python3

exp: .venv/.deps-installed
	$(PY) src/main_export.py --output=output.mp4 --duration=10 --fps=60

run: .venv/.deps-installed
	$(PY) src/main_run.py --fps=120
