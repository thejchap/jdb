# cluster membership using the SWIM gossip protocol and CRDTs
## overview
jdb is entirely decentralized, meaning each node has its own picture of the state of the cluster and who its peers are. it is important for a node to have up-to-date knowledge of the state of its peers so it is able to route requests to the proper node.

there has been a lot of research in this area that has led to some interesting protocols, including [Chord](https://en.wikipedia.org/wiki/Chord_(peer-to-peer)) and [Kademlia](https://en.wikipedia.org/wiki/Kademlia). this past year, my friend and I implemented Chord from the paper (or two versions of the paper), so I was pretty familiar with the concepts and goals around these protocols. generally, each node only keeps track of just enough of its peers to allow for `O(log(N))` lookups. the idea behind this is to facilitate large peer-to-peer clusters with each node only having to maintain minimal routing information.

since jdb is designed to handle massive web-scale traffic with tight SLA requirements from my evening side projects, latency was a concern. because of this, i decided that each node would maintain a routing table of the whole cluster so that requests could be routed in `O(1)`. this routing table would be kept up to date by a gossip protocol based on [SWIM](http://www.cs.cornell.edu/Info/Projects/Spinglass/public_pdfs/SWIM.pdf).

## cluster state
each node maintains its knowledge of cluster state in the form of a type of [CRDT](https://hal.inria.fr/inria-00609399v1/document) (conflict-free replicated data type) called a [LWW register](https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type#LWW-Element-Set_(Last-Write-Wins-Element-Set)). using this type of data structure seemed to be a good fit for this use case because it allows nodes with divergent ideas of cluster state to merge their two states efficiently and accurately.

the LWW register maintains 2 dictionaries, an add set and a remove set. these dictionaries contain k/v pairs where the key is node id/address and the value is a [HLC](https://cse.buffalo.edu/tech-reports/2014-04.pdf) (hybrid logical clock). HLCs are a clock algorithm that facilitate maintaining a total order of events in a distributed system without a centralized clock.

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
the protocol i implemented is inspired by SWIM but is slightly simplified. the purpose of this protocol is to efficiently disseminate the above data structure throughout the cluster.
### bootstrap
when a node joins the cluster, it must know the address of at least one other node to bootstrap itself. it attempts to connect to its known peer. when it does, it syncs its peer list with that of the other node, and starts the protocol. a short grace period is allowed for each node to start up before we add it in to our list of available peers to communicate with. also, a small amount of jitter is added to timing for these cycles to even out request loads a bit.
### gossip
gossip occurs on a regular cadence (defaults to 1s), and also when a peer failure has been detected by a node and verified by k of its peers. during gossip, the node selects k peers at random and syncs its updated state with them, containing any new node removals/additions
### failure detection
every 0.5s, a random peer is chosen from our peers list and it is probed. if an ack is returned, the loop just moves on. if we can't contact the peer, we push it into a queue to be investigated. if the peer is verified as faulty, it is removed from our nodes list then a gossip cycle is initiated to disseminate the information to the rest of the cluster

![](https://github.com/thejchap/jdb/blob/master/docs/img/journal/01_membership.py/mermaid-diagram-20200607085911.png?raw=true)
### investigation
as per the SWIM protocol, when a node is detected as faulty by the probing node, it then enlists the help of k other nodes to help verify that this node is actually down and it isn't just a transient network partition. if any of those nodes are able to contact the target node, we remove it from our suspect list and move on.

![](https://github.com/thejchap/jdb/blob/master/docs/img/journal/01_membership.py/mermaid-diagram-20200607090040.png?raw=true)
### benchmarking
i wanted to get an idea of how efficient the protocol is in disseminating information throughout the cluster. to do this, i spun up a 20 node cluster, each node in its own thread. once the cluster started, i gave a grace period to allow the whole cluster to become aware of all the peers. once the cluster was "stable", i picked a node and killed it, then started a timer and measured how long it took for the dead node to be removed from every node's peer list.

the results were pretty interesting. in tweaking some of the parameters including the gossip interval, failure detection interval, and subgroup sizes, i noticed these didn't have a huge impact on performance. increasing the failure detection subgroup sizes slowed everything down pretty substantially.

with this in mind, i decided to find a happy medium for the input parameters, then decided to tweak other parts of the protocol. here is a graph of timing of node failure dissemination throughout the cluster.

![](https://github.com/thejchap/jdb/blob/master/docs/img/journal/01_membership.py/membership.png?raw=true)

1. in this initial implementation, when a node sent a ping request to k of its peers to verify that a node is down, those peers simply did as they were asked, then returned the result of the request to the requesting node. this is the closest to the SWIM protocol.
2. out of curiosity, i decided to try an implementation where, whenever a node sent a ping request, all the peers that received this request imnmediately condemned the suspect node and removed it from their own lists. this resulted in significantly faster propogation throughout the cluster, but also means a lot of false positives because it is mostly bypassing the failure detection protocol. i did not set up a way to measure false positives.
3. this implementation is slightly less trigger-happy than #2 but speeds up propogation slightly. here, when a node receives a ping request (to verify a failed node), it simply adds that node to its own suspect list to investigate, rather than ignoring it.
4. this implementation builds on the last one, and improves random peer selection by cycling through a list and choosing a random peer in the remaining list, rather than picking a random node in the whole cluster on each loop.

one interesting edge case that surfaced after node failure was other nodes starting to become aware of the failure, then encountering information that indicated the node had been added back into the cluster, then that information propogating and overruling the prior awareness of the node leaving. this can be seen in implementation #1 above, but also happened periodically in all the other implementations. in some cases, the conflicting information would take a pretty substantial amount of time to resolve (8-10s).

## closing thoughts
- verifying the protocol was time consuming. setting up tooling to be able to visualize and understand how data is flowing throughout the system was invaluable, but took just as much time (if not more) than the implementation of the protocol itself, and felt a bit hacky. i know there are [libraries](https://jepsen.io/) and systems to help with things like this, and i look forward to becoming more familiar with the ecosystem.
- the SWIM paper analyzes the efficiency of its dissemination component using epidemiology research as a foundation. this felt eerie and topical to be reading about during COVID-19.
- for the purposes of this system, just using the system clock would have been fine. but learning new things is more fun.
- LWW registers are one of the simpler types of CRDTS. implementing this was really helpful for me to conceptualize how they function a bit better, and was a great introduction to the data structures in general.
- there is definitely still a lot of room for improvement, but i am happy with where it is for now and it is time to move on to other things!