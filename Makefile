SHELL=/bin/bash -e -o pipefail

format:
	@black .

lint:
	@flake8 jdb tests
	@pylint jdb tests

install:
	@export CPPFLAGS="-I$(brew --cellar snappy)/1.1.8/include -L$(brew --cellar snappy)/1.1.8/lib" && \
		pip install -r requirements.txt

typecheck:
	@mypy .

test:
	@pytest tests

cli:
	@python jdb/cli.py

server: server1

server1:
	@python jdb/server/server.py -n 1 -p 1337 -r 1338

server2:
	@python jdb/server/server.py -n 2 -p 2337 -r 2338 -j 1=127.0.0.1:1338

cluster:
	@foreman start

query:
	@python jdb/cli.py -q "${q}"

codegen:
	@python -m grpc_tools.protoc -Ijdb/pb --python_out=jdb/pb --grpc_python_out=jdb/pb peer_server.proto

bench.db:
	@python bin/bench/bench_db.py -s jdb
	@python bin/bench/bench_db.py -s redis
	@python bin/bench/bench_db.py -s lmdb

bench.membership:
	@python bin/bench/bench_membership.py

prof:
	@python bin/prof.py