lint:
	isort .
	flake8 --config formatters-cfg.toml --exclude venv
	black --config formatters-cfg.toml .

check_lint:
	isort --check --diff .
	flake8 --config formatters-cfg.toml --exclude venv
	black --check --config formatters-cfg.tomll .
