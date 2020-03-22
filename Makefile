format:
	@black .

lint:
	@flake8 .

install:
	@pip install -r requirements.txt

typecheck:
	@mypy src

test:
	@pytest tests