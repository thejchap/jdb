# membership
## overview
jdb is entirely decentralized, meaning each node has its own picture of the state of the cluster and who its peers are. it is important for a node to have up-to-date knowledge of the state of its peers so it is able to route requests to the proper node.

there has been a lot of research in this area that has led to some interesting protocols, including Chord<sup>[1](#footnote-chord)</sup> and Kademlia<sup>[2](#footnote-kademlia)</sup>. this past year, my friend and I implemented Chord from the paper (or two versions of the paper), so I was pretty familiar with the concepts and goals around these protocols. generally, each node only keeps track of just enough of its peers to allow for `O(log(N))` lookups. the idea behind this is to facilitate large peer-to-peer clusters with each node only having to maintain minimal routing information.

since jdb is designed to handle massive web-scale traffic with tight SLA requirements from my evening side projects, latency was a concern. because of this, i decided that each node would maintain a routing table of the whole cluster so that requests could be routed in `O(1)`. this routing table would be kept up to date by a gossip protocol based on SWIM<sup>[3](#footnote-swim)</sup>.

## cluster state
each node maintains its knowledge of cluster state in the form of a type of CRDT (conflict-free replicated data type) called a LWW (last write wins) register. using this type of data structure seemed to be a good fit for this use case because it allows nodes with divergent ideas of cluster state to merge their two states efficiently and accurately.

the LWW register maintains 2 dictionaries, an add set and a remove set. these dictionaries contain k/v pairs where the key is node id/address and the value is a HLC (hybrid logical clock). HLCs are a clock algorithm that facilitate maintaining a total order of events in a distributed system without a centralized clock.

**LWW register**
```json
{
  "add_set": {
    "node1=127.0.0.1:1338": 158973080536001,
    "node2=127.0.0.1:2338": 158973080740502
  },
  "remove_set": {
    "node1=127.0.0.1:1338": 158973080738601,
    "node2=127.0.0.1:2338": 158792457695005
  }
}
```

a node can change its view of cluster state either throughout the course of its own failure detection loop, or during gossip with another node. when a node becomes aware of a peer joining the cluster, it adds an entry to the add set. when the node becomes aware of a peer leaving the cluster, it adds the node to the remove set. cluster state is the union of the add set and the remove set, with the highest timestamp in either set winning for that particular node. this data structure can then be merged with other nodes versions versions of the same data structure, creating a merged version that has the most up-to-date info from both

**example merge**
***1. node a cluster State***
node a has awareness of nodes c and b joining the cluster at timestamps 1 and 2 respectively
```json
{
  "add_set": {
    "c": 1,
    "b": 2
  },
  "remove_set": {}
}
```
***2. node b cluster state***
node b has awareness of nodes c and a joining the cluster at timestamps 2 and 1 respectively, then subsequently detected a failure when trying to communicate with node c
```json
{
  "add_set": {
    "c": 2,
    "a": 1
  },
  "remove_set": {
    "c": 3
  }
}
```
***3. merged cluster state***
nodes a and b communicate with each other and merge their lists
```json
{
  "add_set": {
    "c": 2,
    "a": 1,
    "b": 2
  },
  "remove_set": {
    "c": 3
  }
}
```

***4. result***
nodes a and b are only in the add set. node c is in the remove set with a greater timestamp than its value in the add set. now both nodes have an up-to-date view of the cluster containing the latest information from both nodes.
```python
{"a", "b"}
```

## gossip protocol
the protocol I implemented is inspired by SWIM but is slightly simplified.
### bootstrap
when a node joins the cluster, it must know the address of at least one other node to bootstrap itself. it attempts to connect to its known peer. when it does, it syncs its peer list with that of the other node, and starts the protocol
### gossip
gossip occurs on a regular cadence (defaults to 1s), and also when a peer failure has been detected by a node and verified by k of its peers. during gossip, the node selects k peers at random and syncs its updated state with them, containing any new node removals/additions
### failure detection
every 0.5s, a random peer is chosen from our peers list and it is probed. if an ack is returned, the loop just moves on. if we can't contact the peer, we push it into a queue to be investigated. if the peer is verified as faulty, it is removed from our nodes list then a gossip cycle is initiated to disseminate the information to the rest of the cluster

![](https://mermaid.ink/img/eyJjb2RlIjoic2VxdWVuY2VEaWFncmFtXG5cdHBhcnRpY2lwYW50IG5vZGUxXG5cdHBhcnRpY2lwYW50IG5vZGUyXG5cdHBhcnRpY2lwYW50IG5vZGUzXG5cdGF1dG9udW1iZXJcblx0bm9kZTItPj5ub2RlMTogc3RhdGUgc3luY1xuXHRub2RlMS0tPj5ub2RlMjogY2x1c3RlciBzdGF0ZVxuXHRub2RlMy0-Pm5vZGUyOiBzdGF0ZSBzeW5jXG5cdG5vZGUyLS0-Pm5vZGUzOiBjbHVzdGVyIHN0YXRlXG5cdGxvb3AgZmFpbHVyZSBkZXRlY3Rpb24gbG9vcCAoMC41cylcblx0XHRub2RlMS0-Pm5vZGUyOiBwaW5nXG5cdFx0bm9kZTItLT4-bm9kZTE6IGFja1xuXHRcdG5vZGUyLT4-bm9kZTE6IHBpbmdcblx0XHRub2RlMS0tPj5ub2RlMjogYWNrXG5cdFx0bm9kZTItPj5ub2RlMzogcGluZ1xuXHRcdG5vZGUzLS0-Pm5vZGUyOiBhY2tcblx0XHRub2RlMy0-Pm5vZGUyOiBwaW5nXG5cdFx0bm9kZTItLT4-bm9kZTM6IGFja1xuXHRcdG5vZGUzLT4-bm9kZTE6IHBpbmdcblx0XHRub2RlMS0tPj5ub2RlMzogYWNrXG5cdFx0bm9kZTEtPj5ub2RlMzogcGluZ1xuXHRcdG5vZGUzLS0-Pm5vZGUxOiBhY2tcblx0ZW5kIiwibWVybWFpZCI6eyJ0aGVtZSI6ImRlZmF1bHQifSwidXBkYXRlRWRpdG9yIjpmYWxzZX0)]
### investigation
as per the SWIM protocol, when a node is detected as faulty by the probing node, it then enlists the help of k other nodes to help verify that this node is actually down and it isn't just a transient network partition. if any of those nodes are able to contact the target node, we remove it from our suspect list and move on.

![](https://mermaid.ink/img/eyJjb2RlIjoic2VxdWVuY2VEaWFncmFtXG5cdHBhcnRpY2lwYW50IG5vZGUxXG5cdHBhcnRpY2lwYW50IG5vZGUyXG5cdHBhcnRpY2lwYW50IG5vZGUzXG5cdHBhcnRpY2lwYW50IG5vZGU0XG5cdHBhcnRpY2lwYW50IG5vZGU1XG5cdGF1dG9udW1iZXJcblx0cmVjdCByZ2JhKDI1NSwwLDApXG5cdFx0bm9kZTEtPj5ub2RlMjogcGluZ1xuXHRlbmRcblx0cGFyIGludmVzdGlnYXRlIG5vZGUyXG5cdFx0bm9kZTEtPj5ub2RlMzogcGluZyByZXEgKG5vZGUyKVxuXHRcdG5vZGUxLT4-bm9kZTQ6IHBpbmcgcmVxIChub2RlMilcblx0XHRub2RlMS0-Pm5vZGU1OiBwaW5nIHJlcSAobm9kZTIpXG5cdGVuZFxuXHRwYXIgaW52ZXN0aWdhdGluZyBub2RlMlxuXHRcdHJlY3QgcmdiYSgyNTUsMCwwKVxuXHRcdFx0bm9kZTMtPj5ub2RlMjogcGluZ1xuXHRcdFx0bm9kZTQtPj5ub2RlMjogcGluZ1xuXHRcdFx0bm9kZTUtPj5ub2RlMjogcGluZ1xuXHRcdGVuZFxuXHRlbmRcblx0cGFyIG5vZGUyIGZhaWx1cmUgY29uZmlybWVkXG5cdFx0bm9kZTMtLT4-bm9kZTE6IGZhaWx1cmUgY29uZmlybWVkIChub2RlMilcblx0XHRub2RlNC0tPj5ub2RlMTogZmFpbHVyZSBjb25maXJtZWQgKG5vZGUyKVxuXHRcdG5vZGU1LS0-Pm5vZGUxOiBmYWlsdXJlIGNvbmZpcm1lZCAobm9kZTIpXG5cdGVuZFxuXHRub2RlMS0-Pm5vZGU0OiBnb3NzaXAgKHJhbmRvbSBwZWVyKSIsIm1lcm1haWQiOnsidGhlbWUiOiJkZWZhdWx0In0sInVwZGF0ZUVkaXRvciI6ZmFsc2V9)]
### benchmarking
i wanted to get an idea of how efficient the protocol is in disseminating information throughout the cluster. to do this, i spun up a 20 node cluster, each node in its own thread. once the cluster started, i gave a grace period to allow the whole cluster to become aware of all the peers. once the cluster was "stable", i picked a node and killed it, then started a timer and measured how long it took for the dead node to be removed from every node's peer list.

the results were pretty interesting. in tweaking some of the parameters including the gossip interval, failure detection interval, and subgroup sizes, i noticed these didn't have a huge impact on performance. increasing the failure detection subgroup sizes slowed everything down pretty substantially.

with this in mind, i decided to find a happy medium for the input parameters, then decided to tweak other parts of the protocol

### details
- a short grace period is allowed for each node to start up before we add it in to our list of available peers to communicate with. also, a small amount of jitter is added to timing for these cycles to even out request loads a bit.
- requests are routed among the nodes using Maglev hashing<sup>[4](#footnote-maglev)</sup>. this will be covered in another post.

## sources
- <a name="footnote-chord">1</a>: [https://en.wikipedia.org/wiki/Chord_(peer-to-peer)](https://en.wikipedia.org/wiki/Chord_(peer-to-peer))
- <a name="footnote-kademlia">2</a>: [https://en.wikipedia.org/wiki/Kademlia](https://en.wikipedia.org/wiki/Kademlia)
- <a name="footnote-swim">3</a>: [http://www.cs.cornell.edu/Info/Projects/Spinglass/public_pdfs/SWIM.pdf](http://www.cs.cornell.edu/Info/Projects/Spinglass/public_pdfs/SWIM.pdf)
- <a name="footnote-maglev">4</a>: [https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/44824.pdf](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/44824.pdf)