.venv/.deps-installed: pyproject.toml
	.venv/bin/pip install .
	touch .venv/.deps-installed

exp: .venv/.deps-installed
	.venv/bin/python3 -m main export $(output) $(duration)
run: .venv/.deps-installed
	.venv/bin/python3 -m main
