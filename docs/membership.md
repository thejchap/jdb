# membership
## overview
jdb is entirely decentralized, meaning each node has its own picture of the state of the cluster and who its peers are. it is important for a node to have up-to-date knowledge of the state of its peers so it is able to route requests to the proper node.

there has been a lot of research in this area that has led to some interesting protocols, including Chord, Pastry, and Kademlia. this past year, my friend and I implemented Chord from the paper (or two versions of the paper), so I was pretty familiar with the concepts and goals around these protocols. generally, each node only keeps track of just enough of its peers to allow for `O(log(N))` lookups. the idea behind this is to facilitate large clusters with each node only having to maintain minimal routing information.

since jdb is designed is to handle massive web-scale traffic with tight SLA requirements from my evening side projects, latency was a concern. because of this, i decided that each node would maintain a routing table of the whole cluster so that requests could be routed in `O(1)`. this routing table would be kept up to date by a gossip protocol based on SWIM.

## gossip protocol
### bootstrap
when a node joins the cluster, it must know the address of at least one other node to bootstrap itself. it attempts to connect to its known peer. when it does, it syncs its peer list with that of the other node, and starts the SWIM protocol failure detection component in one thread, and the dissemination component in another thread, and another thread for investigating suspect nodes (ones that it thinks might have failed but hasn't verified by indirect probing yet)

## cluster state
each node maintains its knowledge of cluster state in the form of a type of CRDT (conflict-free replicated data type) called a LWW (last write wins) register. using this type of data structure seemed to be a good fit for this use case because it allows nodes with divergent ideas of cluster state to merge their two states efficiently and accurately.

the LWW register maintains 2 dictionaries, an add set and a remove set. these dictionaries contain k/v pairs where the key is node id/address and the value is a HLC (hybrid logical clock). HLCs are a clock algorithm that facilitate maintaining a total order of events in a distributed system without a centralized clock.

**cluster state** TODO
```json
{
  "add_set": {
    "00000001=127.0.0.1:1338": 158792457695005,
    "00000002=127.0.0.1:2338": 158792457695005
  },
  "remove_set": {
    "00000001=127.0.0.1:1338": 158792457695005,
    "00000002=127.0.0.1:2338": 158792457695005
  }
}
```

a node can change its view of cluster state either throughout the course of its own failure detection loop, or during gossip with another node. when a node becomes aware of a peer joining the cluster, it adds an entry to the add set. when the node becomes aware of a peer leaving the cluster, it adds the node to the remove set. cluster state is the union of the add set and the remove set, with the highest timestamp in either set winning for that particular node. this data structure can then be merged with other nodes versions versions of the same data structure, creating a merged version that has the most up-to-date info from both

**example merge**
TODO

## protocol
the protocol I implemented is inspired by SWIM but is slightly simplified.
### gossip
gossip occurs on a regular cadence (defaults to 1s), and also when a peer failure has been detected by a node and verified by k of its peers. during gossip, the node selects k peers at random and syncs its updated state with them, containing any new node removals/additions
### failure detection
every 0.5s, a random peer is chosen from our peers list and it is probed. if an ack is returned, the loop just moves on. if we can't contact the peer, we push it into a queue to be investigated. if the peer is verified as faulty, it is removed from our nodes list then a gossip cycle is initiated to disseminate the information to the rest of the cluster
### investigation
as per the SWIM protocol, when a node is detected as faulty by the probing node, it then enlists the help of k other nodes to help verify that this node is actually down and it isn't just a transient network partition. if any of those nodes are able to contact the target node, we remove it from our suspect list and move on.
### subgroup selection
a short grace period is allowed for each node to start up before we add it in to our list of available peers to communicate with