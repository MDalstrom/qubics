.venv/.deps-installed: pyproject.toml
	.venv/bin/pip install .
	touch .venv/.deps-installed

PY := .venv/bin/python3

.PHONY: exp
.PHONY: run

exp: .venv/.deps-installed
	rm -f output.mp4;
	$(PY) src/main.py --output=output.mp4 --duration=10 --fps=60

run: .venv/.deps-installed
	$(PY) src/main.py --fps=120
