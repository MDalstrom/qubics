.venv/.deps-installed: pyproject.toml
	.venv/bin/pip install .
	touch .venv/.deps-installed

exp: .venv/.deps-installed
	.venv/bin/python3 src/main.py export $(output) $(duration)
run: .venv/.deps-installed
	.venv/bin/python3 src/main.py --fps=120
