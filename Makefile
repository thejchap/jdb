format:
	@black .

lint:
	@flake8 .

install:
	@export CPPFLAGS="-I$(brew --cellar snappy)/1.1.8/include -L$(brew --cellar snappy)/1.1.8/lib" && \
		pip install -r requirements.txt

typecheck:
	@mypy .

test:
	@pytest tests

cli:
	@python3 jdb/cli.py

server:
	@python3 jdb/server.py

benchmark:
	time python -c "from tests.benchmark import fill; fill()"
	python -m timeit "from tests.benchmark import put" "put()"
	python -m timeit "from tests.benchmark import delete" "delete()"