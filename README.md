# jdb

## description
a database for fun

### design
#### api
the database has a simple API with 3 operations:
- `put`
- `get`
- `delete`

## todo
- WAL
- Rebalance index AVL tree
- Raft

## resources
### inspo
- https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf
- https://www.cs.princeton.edu/courses/archive/spring13/cos461/docs/lec16-dynamo.pdf
- https://www.cockroachlabs.com/docs/stable/architecture/distribution-layer.html
- http://www.cs.cornell.edu/Projects/ladis2009/papers/Lakshman-ladis2009.PDF
### transactions
- https://dgraph.io/blog/post/badger-txn/
- https://en.wikipedia.org/wiki/Multiversion_concurrency_control
- https://dl.acm.org/doi/pdf/10.1145/356842.356846
- https://dl.acm.org/doi/10.1145/2168836.2168853
- https://wiki.postgresql.org/wiki/SSI
## consensus
- https://raft.github.io/raft.pdf
- https://github.com/ongardie/dissertation/blob/master/stanford.pdf
### storage
- https://www.usenix.org/system/files/conference/fast16/fast16-papers-lu.pdf
- http://www.vldb.org/pvldb/vol12/p2183-zhang.pdf
- https://www.memsql.com/blog/what-is-skiplist-why-skiplist-index-for-memsql/
- https://www.cl.cam.ac.uk/teaching/2005/Algorithms/skiplists.pdf
- https://github.com/dgraph-io/badger
- https://github.com/facebook/rocksdb
- https://github.com/facebook/rocksdb/wiki/RocksDB-In-Memory-Workload-Performance-Benchmarks
### lang
- https://github.com/antirez/redis/blob/96a54866ab4694cf338af0441f28aa69e9643376/src/server.c
- https://ply.readthedocs.io/en/latest/ply.html#parsing-basics
- https://redis.io/topics/protocol
### routing
- https://people.math.gatech.edu/~yu/Papers/p2p.pdf
### data integrity
- https://en.wikipedia.org/wiki/Cyclic_redundancy_check
### time
- https://cse.buffalo.edu/tech-reports/2014-04.pdf
- https://jaredforsyth.com/posts/hybrid-logical-clocks/
- http://muratbuffalo.blogspot.com/2014/07/hybrid-logical-clocks.html
- https://medium.com/@Alibaba_Cloud/in-depth-analysis-on-hlc-based-distributed-transaction-processing-e75dad5f2af8
### other
- https://github.com/soundcloud/roshi#crdt
- http://book.mixu.net/distsys/eventual.html
- https://hal.inria.fr/file/index/docid/555588/filename/techreport.pdf