format:
	@black .

lint:
	@flake8 .

install:
	@pip install -r requirements.txt

typecheck:
	@mypy .

test:
	@pytest tests

benchmark:
	time python -c "from tests.benchmark import fill; fill()"
	python -m timeit "from tests.benchmark import put" "put()"
	python -m timeit "from tests.benchmark import delete" "delete()"