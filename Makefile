.venv/.deps-installed: pyproject.toml
	.venv/bin/pip install .
	touch .venv/.deps-installed

PY := .venv/bin/python3

alt: .venv/.deps-installed
	$(PY) src/main_alt.py --fps=120

exp: .venv/.deps-installed
	$(PY) src/main.py --output=output.mp4 --duration=10 --fps=60

run: .venv/.deps-installed
	$(PY) src/main.py --fps=120
