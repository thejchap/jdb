# implementing MVCC and SSI in an embedded key-value store

## intro

this is the second post documenting my adventures writing [jdb](https://github.com/thejchap/jdb). jdb is a distributed key-value store written in python. i took on this project to a) learn more about distributed databases and b) get better at writing python. the first post on cluster membership and implementing a gossip protocol can be found [](https://medium.com/@chap/peer-to-peer-cluster-membership-using-the-swim-gossip-protocol-and-crdts-13f9386fe9b4)

## overview

working on jdb has provided me with an opportunity to not only deepen my understanding of distributed programming in a multi-node environment, but also in a local, multi-threaded environment. i initially considered using an existing solution (for example [RocksDB](https://rocksdb.org/) or [LevelDB](https://en.wikipedia.org/wiki/LevelDB)) for embedded per-node storage in jdb, but decided it would be way more fun to write one myself.

embedded data stores generally have a fairly simple API (put, get, delete) and are intended to be high-performance storage engines. the storage engine on each node in jdb is where data would end up being stored and read from after getting routed around in the cluster to the correct node. i wanted to write one that supported multiple connections, [ACID transactions](https://en.wikipedia.org/wiki/ACID) (without the D for now - everything is just in memory), and [MVCC](https://en.wikipedia.org/wiki/Multiversion_concurrency_control).

## design

the data store is implemented in a `DB` class that gets opened per-process when jdb starts up. each `DB` instance gets instantiated with an `Oracle` and a `Memtable`. the `Oracle` is the point of entry for transactions, and maintains read/write timestamps for transactions and also tracks dependent keys to support [SSI](https://wiki.postgresql.org/wiki/Serializable) as the transaction isolation level. the `Memtable` maintains the actual data structures that store data that transactions write to. the index is maintained in the form of an [AVL tree](https://en.wikipedia.org/wiki/AVL_tree) where the nodes are pointers to the actual raw bytes in an `arena` which is just a byte array of encoded data entries. i chose an AVL tree for the index because it is self-balancing guarantees an upper bound of O(logN) time complexity for all its operations.

## entries

an instance of the `Entry` class is the most granular level of storage, and represents a key, its value, and metadata. when a transaction commits, the entries included in the transaction get encoded into byte arrays that get appended onto the `arena` (one long byte array that keeps growing). entries can vary in length, and the memtable's index contains pointers to offsets where each chunk of memory lives in the `arena`.

encoded entries are laid out in memory as follows:

![](https://github.com/thejchap/jdb/blob/master/docs/img/journal/02_storage/entry.png?raw=true)

## serializable snapshot isolation (SSI)

when implementing transactions, i had to choose a [transaction isolation level](<https://en.wikipedia.org/wiki/Isolation_(database_systems)>) (or levels) to provide to the database user. the isolation level determines, during the execution of a transaction, what data the operations in that transaction are allowed to see. i decided to implement [serializable snapshot isolation](https://wiki.postgresql.org/wiki/SSI) (SSI), which is the strictest isolation level, and a relatively new development in databases.

serializability in database systems is a property which ensures that the outcome of a set of transactions is equal to the outcome as if all the transactions were executed serially (one after the other). this is an extremely important property in areas such as finance, where race conditions during debit and credit operations could cause money disappearing or appearing out of thin air.

when executing transactions one after the other in a single-threaded environment, this is a very easy property to uphold. as with most concepts in programming, the second we add in any sort of concurrent processing, the problem gets a lot more interesting.

[snapshot isolation](https://en.wikipedia.org/wiki/Snapshot_isolation) (SI) is a widely used isolation level in which at the beginning of a transaction, the transaction gets assigned a start timestamp, and only sees data that is a result of transactions which have committed prior to that start timestamp. this prevents dirty reads of data that is being modified by other in-flight transactions. SSI builds on top of SI by preventing in-progress writes from modifying keys that other transactions are reading by doing some "bookkeeping" of transaction dependencies.

in jdb, the `Oracle` class does the bookkeeping, and is the only logic in the transaction commit code path that is not threadsafe. `Oracle` maintains a map of keys to their last commit timestamp and provides 2 public methods:

- `read_ts` - called by transactions when they are instantiated to obtain a start/read timestamp that determines what snapshot of the database they are getting
- `commit_request` - ensures no keys in the list of read operations in this transaction have been modified by other transactions since this transaction started

![](https://github.com/thejchap/jdb/blob/master/docs/img/journal/02_storage/mermaid-diagram-20201012084711.png?raw=true)

## multi-version concurrency control (MVCC)

[multi-version concurrency control](https://en.wikipedia.org/wiki/Multiversion_concurrency_control) (MVCC) provides a consistent point-in-time snapshot of the database to transactions who are reading data. this allows concurrent operations to happen so reads are not blocked by writes, while also ensuring that in-progress transactions don't see half committed data. this is achieved by assigning a monotonically increasing timestamp to transactions (and therefore all writes that occur within that transaction) which gets encoded as part of the `Entry`'s key when it is committed in the `Memtable`.

as stated earlier, the database index is maintained as an AVL tree in which the nodes are pointers to data in the `arena`. the keys in this table are a concatenation of key and timestamp. during a lookup, we traverse the tree and find the key matching the query key which has the latest timestamp prior to the read timestamp on the transaction.

## API

the finished product looks a little something like this in code:

```python
from jdb.db import DB

db = DB()

with db.transaction() as txn:
  txn.read(b'foo')
  txn.write(b'bar', b'baz')
```

## code

[https://github.com/thejchap/jdb](https://github.com/thejchap/jdb)
