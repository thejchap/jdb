# implementing MVCC and SSI in an embedded key-value store

## overview

working on jdb has provided me with an opportunity to not only deepen my understanding of distributed programming in a multi-node environment, but also in a local, multi-threaded environment. i initially considered using an existing solution (for example RocksDB or LevelDB) for embedded per-node storage in jdb, but then was like "why the heck would i do that? this is a learning exercise - might as well learn all i can" so i decided to write one from scratch.

embedded data stores generally have a fairly simple API (put, get, delete) and are intended to be high-performance storage engines. the storage engine on each node in jdb is where data would end up being stored and read from after getting routed around in the cluster to the correct node. i wanted to write one that supported multiple connections, ACID transactions (without the D for now), and MVCC.

## design

the data store is implemented in a `DB` class that gets opened per-process when jdb starts up. each `DB` instance gets instantiated with an `Oracle` and a `Memtable`. the oracle is the point of entry for transactions, and maintains read/write timestamps for transactions and also tracks dependent keys to support SSI as the transaction isolation level. the memtable maintains the actual data structures that store data that transactions write to. it maintains an index in the form of an AVL tree where the nodes are pointers to the actual raw bytes in an `arena` which is just a byte array of encoded data entries

## entries

an instance of the `Entry` class is the most granular level of storage, and represents a key, its value, and metadata. when a transaction commits, the entries included in the transaction get encoded into byte arrays that get appended onto the `arena` (one long byte array that keeps growing). entries can vary in length, and the memtable's index contains pointers to offsets where each chunk of memory lives in the `arena`.

entries are structured as follows:

| block size | meta | key length | value length | key | value | crc32 |

- block size
  - this is the length of the entire block of data after it has been encoded as a byte array
- meta
  - bits that can be flipped internally by the db to add metadata to the transaction
  - used during a `delete` operation to add a `tombstone` to the entry when appending to the log
- key length
- value length
- key
- value
- CRC32
  - a checksum of the header (meta, key length and value length) and key/value data
  - when decoding the byte array during a `get` operation, a checksum of the retrieved values is calculated and compared to the persisted one
  - CRC32 is a standard error-detection code

## serializable snapshot isolation (SSI)

when implementing transactions, i had to choose a transaction isolation level (or levels) to provide to the database user. the isolation level determines, during the execution of a transaction, what data the operations in that transaction are allowed to see. i decided to implement SSI, which is the strictest isolation level, and a relatively new development in databases.

serializability in database systems is a property which ensures that the outcome of a set of transactions is equal to the outcome as if all the transactions were executed serially (one after the other). this is an extremely important property in areas such as finance, where race conditions during debit and credit operations could cause money disappearing or appearing out of thin air.

when executing transactions one after the other in a single-threaded environment, this is a very easy property to uphold. as with most concepts in programming, the second we add in any sort of concurrent processing, the problem gets a lot more interesting.

snapshot isolation (SI) is a widely used isolation level in which at the beginning of a transaction, the transaction gets assigned a start timestamp, and only sees data that is a result of transactions which have committed prior to that start timestamp. this prevents dirty reads of data that is being modified by other in-flight transactions. SSI builds on top of SI by preventing in-progress writes from modifying keys that other transactions are reading by doing some "bookkeeping" of transaction dependencies.

in jdb, the `Oracle` class does the bookkeeping, and is the only logic in the transaction commit code path that is not threadsafe. `Oracle` maintains a map of keys to their last commit timestamp and provides 2 public methods:

- `read_ts` - called by transactions when they are instantiated to obtain a start/read timestamp that determines what snapshot of the database they are getting
- `commit_request` - ensures no keys in the list of read operations in this transaction have been modified by other transactions since this transaction started

## multi-version concurrency control (MVCC)
